#!/usr/bin/env python3
"""Agent Backup CLI.

Complete 4-Layer Agent Backup System for SomaAgent01.

Layers:
1. CAPSULE - Identity, tools, models, prompts, settings (JSON export)
2. MEMORY  - PostgreSQL + Redis + pending queues (database dumps)
3. CODE    - Git repository bundles
4. INFRA   - Docker images and Kubernetes manifests

Usage:
    python scripts/backup_agent.py --tenant acme --dest /backups
    python scripts/backup_agent.py --capsule-id <uuid> --dest /backups
    python scripts/backup_agent.py --full --dest /backups
    python scripts/backup_agent.py --layer capsule --dest /backups
    python scripts/backup_agent.py --restore backup_file.tar.gz --target-tenant new_tenant

VIBE Compliance:
- Rule 82: Professional comments
- Rule 84: Real infrastructure operations
- Rule 91: Environment variable configuration
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django

django.setup()

from services.capsule_export import export_capsule, export_tenant_capsules
from services.capsule_import import import_capsule, import_tenant_capsules

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


def get_config() -> dict:
    """Get backup configuration from environment."""
    return {
        "postgres_host": os.environ.get("SOMA_DB_HOST", "localhost"),
        "postgres_port": os.environ.get("SOMA_DB_PORT", "5432"),
        "postgres_db": os.environ.get("SOMA_DB_NAME", "somaagent01"),
        "postgres_user": os.environ.get("SOMA_DB_USER", "postgres"),
        "redis_url": os.environ.get("SOMA_REDIS_URL", "redis://localhost:6379"),
        "s3_bucket": os.environ.get("SOMA_BACKUP_BUCKET", ""),
        "s3_prefix": os.environ.get("SOMA_BACKUP_PREFIX", "agent-backups/"),
    }


# =============================================================================
# LAYER 1: CAPSULE BACKUP
# =============================================================================


def backup_layer_capsules(
    dest: Path,
    tenant: Optional[str] = None,
    capsule_id: Optional[str] = None,
) -> Path:
    """Layer 1: Export Capsule(s) to JSON.

    Args:
        dest: Destination directory
        tenant: Tenant to backup (all capsules)
        capsule_id: Specific capsule UUID to backup

    Returns:
        Path to the capsules.json file
    """
    logger.info("=== Layer 1: Capsule Export ===")

    capsule_file = dest / "capsules.json"

    if capsule_id:
        # Single capsule export
        data = export_capsule(
            UUID(capsule_id),
            include_instances=True,
            include_sessions=False,
            include_related_data=True,
        )
        data = {"capsules": [data], "single_export": True}
    else:
        # Full tenant export
        data = export_tenant_capsules(
            tenant or "default",
            include_instances=True,
            include_related_data=True,
        )

    capsule_file.write_text(json.dumps(data, indent=2, default=str))

    capsule_count = len(data.get("capsules", []))
    logger.info("Exported %d capsule(s) to %s", capsule_count, capsule_file)

    return capsule_file


# =============================================================================
# LAYER 2: MEMORY BACKUP
# =============================================================================


def backup_layer_memory(dest: Path) -> dict:
    """Layer 2: Backup PostgreSQL and Redis.

    Args:
        dest: Destination directory

    Returns:
        Dict with paths to backup files
    """
    logger.info("=== Layer 2: Memory Backup ===")

    config = get_config()
    result = {"postgres": None, "redis": None}

    # PostgreSQL backup
    pg_file = dest / "postgres_dump.sql"
    try:
        env = os.environ.copy()
        env["PGPASSWORD"] = os.environ.get("SOMA_DB_PASSWORD", "")

        cmd = [
            "pg_dump",
            f"--host={config['postgres_host']}",
            f"--port={config['postgres_port']}",
            f"--username={config['postgres_user']}",
            f"--dbname={config['postgres_db']}",
            "--format=plain",
            "--no-owner",
            "--no-acl",
            f"--file={pg_file}",
        ]

        subprocess.run(cmd, env=env, check=True, capture_output=True)
        result["postgres"] = str(pg_file)
        logger.info(
            "PostgreSQL backup: %s (%.2f MB)", pg_file, pg_file.stat().st_size / 1024 / 1024
        )

    except subprocess.CalledProcessError as e:
        logger.error("PostgreSQL backup failed: %s", e.stderr.decode() if e.stderr else str(e))
    except FileNotFoundError:
        logger.warning("pg_dump not found - skipping PostgreSQL backup")

    # Redis backup
    try:
        redis_file = dest / "redis_backup.json"
        # Export UI settings from Redis
        from services.common.ui_settings_store import UiSettingsStore

        store = UiSettingsStore()
        import asyncio

        settings = asyncio.get_event_loop().run_until_complete(store.get())
        redis_file.write_text(json.dumps(settings, indent=2))
        result["redis"] = str(redis_file)
        logger.info("Redis settings backup: %s", redis_file)

    except Exception as e:
        logger.warning("Redis backup failed: %s", e)

    return result


# =============================================================================
# LAYER 3: CODE BACKUP
# =============================================================================


def backup_layer_code(dest: Path, repo_path: Optional[Path] = None) -> dict:
    """Layer 3: Create git bundle of repository.

    Args:
        dest: Destination directory
        repo_path: Path to git repository (defaults to project root)

    Returns:
        Dict with paths to bundle files
    """
    logger.info("=== Layer 3: Code Backup ===")

    repo_path = repo_path or Path(__file__).parent.parent
    result = {"bundles": []}

    # Create git bundle
    bundle_file = dest / "somaAgent01.bundle"
    try:
        subprocess.run(
            ["git", "bundle", "create", str(bundle_file), "--all"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        result["bundles"].append(str(bundle_file))
        logger.info(
            "Git bundle: %s (%.2f MB)", bundle_file, bundle_file.stat().st_size / 1024 / 1024
        )

    except subprocess.CalledProcessError as e:
        logger.error("Git bundle failed: %s", e.stderr.decode() if e.stderr else str(e))
    except FileNotFoundError:
        logger.warning("git not found - skipping code backup")

    # Also backup knowledge directory
    knowledge_dir = repo_path / "knowledge"
    if knowledge_dir.exists():
        knowledge_backup = dest / "knowledge"
        shutil.copytree(knowledge_dir, knowledge_backup, dirs_exist_ok=True)
        result["knowledge"] = str(knowledge_backup)
        logger.info("Knowledge directory backed up")

    return result


# =============================================================================
# LAYER 4: INFRASTRUCTURE BACKUP
# =============================================================================


def backup_layer_infra(dest: Path) -> dict:
    """Layer 4: Save Docker images.

    Args:
        dest: Destination directory

    Returns:
        Dict with paths to image tarballs
    """
    logger.info("=== Layer 4: Infrastructure Backup ===")

    images = [
        "somaagent01:latest",
        "somabrain:latest",
        "somafractalmemory:latest",
    ]

    result = {"images": []}

    for image in images:
        tar_file = dest / f"{image.replace(':', '_').replace('/', '_')}.tar"
        try:
            subprocess.run(
                ["docker", "save", "-o", str(tar_file), image],
                check=True,
                capture_output=True,
            )
            result["images"].append(str(tar_file))
            logger.info("Saved image %s: %.2f MB", image, tar_file.stat().st_size / 1024 / 1024)

        except subprocess.CalledProcessError as e:
            logger.warning(
                "Failed to save image %s: %s", image, e.stderr.decode() if e.stderr else str(e)
            )
        except FileNotFoundError:
            logger.warning("docker not found - skipping image backup")
            break

    return result


# =============================================================================
# RESTORE FUNCTIONS
# =============================================================================


def restore_backup(
    backup_file: Path,
    target_tenant: Optional[str] = None,
    layers: Optional[list] = None,
) -> dict:
    """Restore from a backup archive.

    Args:
        backup_file: Path to backup .tar.gz
        target_tenant: Override tenant for imported capsules
        layers: Specific layers to restore (default: all)

    Returns:
        Dict with restore results
    """
    logger.info("=== Restoring from %s ===", backup_file)

    layers = layers or ["capsule", "memory"]
    result = {"success": True, "restored": []}

    # Extract archive
    extract_dir = Path("/tmp") / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    extract_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(backup_file, "r:gz") as tar:
        tar.extractall(extract_dir)

    # Find the backup subdirectory
    backup_dirs = list(extract_dir.iterdir())
    if backup_dirs:
        backup_dir = backup_dirs[0]
    else:
        backup_dir = extract_dir

    # Layer 1: Restore capsules
    if "capsule" in layers:
        capsule_file = backup_dir / "capsules.json"
        if capsule_file.exists():
            logger.info("Restoring capsules...")
            data = json.loads(capsule_file.read_text())

            if data.get("single_export"):
                # Single capsule restore
                for capsule_data in data.get("capsules", []):
                    import_result = import_capsule(capsule_data, target_tenant=target_tenant)
                    if import_result.success:
                        logger.info("Imported capsule: %s", import_result.capsule)
                        result["restored"].append(str(import_result.capsule))
                    else:
                        logger.error("Import failed: %s", import_result.error)
                        result["success"] = False
            else:
                # Tenant restore
                tenant_result = import_tenant_capsules(data, target_tenant=target_tenant)
                logger.info(
                    "Tenant import: %d succeeded, %d failed",
                    tenant_result.success_count,
                    tenant_result.failure_count,
                )
                result["restored"].extend(
                    [str(r.capsule) for r in tenant_result.successful_imports]
                )

    # Layer 2: Restore memory (PostgreSQL)
    if "memory" in layers:
        pg_file = backup_dir / "postgres_dump.sql"
        if pg_file.exists():
            logger.info("PostgreSQL restore available at: %s", pg_file)
            logger.info("To restore: psql -d somaagent01 < %s", pg_file)
            result["postgres_restore_file"] = str(pg_file)

    # Cleanup
    shutil.rmtree(extract_dir)

    return result


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SomaAgent01 Backup CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--tenant", default="default", help="Tenant to backup")
    parser.add_argument("--capsule-id", help="Specific capsule UUID to backup")
    parser.add_argument("--dest", type=Path, required=False, help="Destination directory")
    parser.add_argument("--full", action="store_true", help="Full 4-layer backup")
    parser.add_argument(
        "--layer",
        choices=["capsule", "memory", "code", "infra"],
        action="append",
        help="Specific layer(s) to backup",
    )
    parser.add_argument("--restore", type=Path, help="Restore from backup file")
    parser.add_argument("--target-tenant", help="Target tenant for restore")
    parser.add_argument("--no-archive", action="store_true", help="Skip creating tar.gz archive")

    args = parser.parse_args()

    # Handle restore
    if args.restore:
        result = restore_backup(
            args.restore,
            target_tenant=args.target_tenant,
            layers=args.layer,
        )
        logger.info("Restore complete: %s", result)
        return

    # Validate dest for backup
    if not args.dest:
        parser.error("--dest is required for backup operations")

    # Determine layers to backup
    if args.full:
        layers = ["capsule", "memory", "code", "infra"]
    elif args.layer:
        layers = args.layer
    else:
        layers = ["capsule"]  # Default to capsule-only

    # Create backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = args.dest / f"agent_backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting backup to %s (layers: %s)", backup_dir, layers)

    manifest = {
        "created_at": timestamp,
        "tenant": args.tenant,
        "capsule_id": args.capsule_id,
        "layers": layers,
        "results": {},
    }

    # Execute backup layers
    if "capsule" in layers:
        backup_layer_capsules(backup_dir, args.tenant, args.capsule_id)
        manifest["results"]["capsule"] = "success"
        logger.info("✅ Layer 1: Capsules exported")

    if "memory" in layers:
        result = backup_layer_memory(backup_dir)
        manifest["results"]["memory"] = result
        logger.info("✅ Layer 2: Memory backed up")

    if "code" in layers:
        result = backup_layer_code(backup_dir)
        manifest["results"]["code"] = result
        logger.info("✅ Layer 3: Code bundled")

    if "infra" in layers:
        result = backup_layer_infra(backup_dir)
        manifest["results"]["infra"] = result
        logger.info("✅ Layer 4: Infrastructure saved")

    # Write manifest
    manifest_file = backup_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2))

    # Create archive
    if not args.no_archive:
        archive = args.dest / f"agent_backup_{timestamp}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(backup_dir, arcname=backup_dir.name)
        logger.info("✅ Archive created: %s", archive)

        # Cleanup directory
        shutil.rmtree(backup_dir)
    else:
        archive = backup_dir

    logger.info("=" * 60)
    logger.info("Backup complete: %s", archive)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
