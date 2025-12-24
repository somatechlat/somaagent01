"""Manifest ingestion pipeline for capsule YAML files.

Parses manifest.yaml files and normalizes them to CapsuleDefinition records.
Validates policy, risk, and HITL fields. Rejects incompatible capsules
based on environment mode (DEV, STAGING, PROD).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

import os
from services.common.capsule_store import CapsuleRecord, CapsuleStatus, CapsuleStore


__all__ = ["ManifestParser", "ManifestValidationError", "parse_manifest"]


class ManifestValidationError(Exception):
    """Raised when manifest validation fails."""
    def __init__(self, message: str, field: str | None = None, errors: List[str] | None = None):
        self.message = message
        self.field = field
        self.errors = errors or []
        super().__init__(message)


@dataclass
class ManifestValidationResult:
    """Result of manifest validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]


class ManifestParser:
    """Parser and validator for capsule manifest.yaml files."""
    
    # Required fields in manifest
    REQUIRED_FIELDS = {"id", "name", "version"}
    
    # Fields that require specific validation
    POLICY_FIELDS = {
        "allowed_tools", "prohibited_tools", "allowed_mcp_servers",
        "allowed_domains", "blocked_domains", "egress_mode",
        "opa_policy_packages", "guardrail_profiles"
    }
    
    RISK_FIELDS = {
        "tool_risk_profile", "risk_thresholds", "data_classification"
    }
    
    HITL_FIELDS = {
        "default_hitl_mode", "max_pending_hitl"
    }
    
    # Valid enum values
    VALID_EGRESS_MODES = {"none", "restricted", "open"}
    VALID_HITL_MODES = {"none", "optional", "required"}
    VALID_RISK_PROFILES = {"low", "standard", "high", "critical"}
    VALID_DATA_CLASSIFICATIONS = {"public", "internal", "confidential", "restricted"}
    VALID_STATUSES = {"draft", "published", "deprecated"}
    
    # Environment mode restrictions
    PROD_RESTRICTIONS = {
        "egress_mode": {"open"},  # Not allowed in prod
        "default_hitl_mode": set(),  # All allowed
    }
    
    def __init__(self, environment: str | None = None):
        self.environment = environment or os.environ.service.environment
    
    def parse_file(self, path: Path) -> Dict[str, Any]:
        """Parse a manifest YAML file."""
        if not path.exists():
            raise ManifestValidationError(f"Manifest file not found: {path}")
        
        with path.open("r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ManifestValidationError(f"Invalid YAML: {e}")
        
        if not isinstance(data, dict):
            raise ManifestValidationError("Manifest must be a YAML dictionary")
        
        return data
    
    def parse_string(self, content: str) -> Dict[str, Any]:
        """Parse a manifest from YAML string."""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ManifestValidationError(f"Invalid YAML: {e}")
        
        if not isinstance(data, dict):
            raise ManifestValidationError("Manifest must be a YAML dictionary")
        
        return data
    
    def validate(self, manifest: Dict[str, Any]) -> ManifestValidationResult:
        """Validate manifest data against schema and environment rules."""
        errors: List[str] = []
        warnings: List[str] = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in manifest or not manifest[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate enum fields
        if "egress_mode" in manifest:
            if manifest["egress_mode"] not in self.VALID_EGRESS_MODES:
                errors.append(f"Invalid egress_mode: {manifest['egress_mode']}. "
                             f"Must be one of: {self.VALID_EGRESS_MODES}")
        
        if "default_hitl_mode" in manifest:
            if manifest["default_hitl_mode"] not in self.VALID_HITL_MODES:
                errors.append(f"Invalid default_hitl_mode: {manifest['default_hitl_mode']}. "
                             f"Must be one of: {self.VALID_HITL_MODES}")
        
        if "tool_risk_profile" in manifest:
            if manifest["tool_risk_profile"] not in self.VALID_RISK_PROFILES:
                errors.append(f"Invalid tool_risk_profile: {manifest['tool_risk_profile']}. "
                             f"Must be one of: {self.VALID_RISK_PROFILES}")
        
        if "data_classification" in manifest:
            if manifest["data_classification"] not in self.VALID_DATA_CLASSIFICATIONS:
                errors.append(f"Invalid data_classification: {manifest['data_classification']}. "
                             f"Must be one of: {self.VALID_DATA_CLASSIFICATIONS}")
        
        # Validate list fields
        for field in ["allowed_tools", "prohibited_tools", "allowed_mcp_servers",
                      "allowed_domains", "blocked_domains", "allowed_runtimes",
                      "opa_policy_packages", "guardrail_profiles", "rl_excluded_fields"]:
            if field in manifest and not isinstance(manifest[field], list):
                errors.append(f"Field '{field}' must be a list")
        
        # Validate dict fields
        for field in ["role_overrides", "risk_thresholds", "metadata"]:
            if field in manifest and not isinstance(manifest[field], dict):
                errors.append(f"Field '{field}' must be a dictionary")
        
        # Validate integer fields
        for field in ["max_wall_clock_seconds", "max_concurrent_nodes", 
                      "max_pending_hitl", "retention_policy_days"]:
            if field in manifest:
                if not isinstance(manifest[field], int) or manifest[field] < 0:
                    errors.append(f"Field '{field}' must be a non-negative integer")
        
        # Environment-specific restrictions
        if self.environment == "PROD":
            errors.extend(self._validate_prod_restrictions(manifest))
        
        # Check conflicting policies
        if manifest.get("egress_mode") == "none" and manifest.get("allowed_domains"):
            warnings.append("allowed_domains ignored when egress_mode is 'none'")
        
        # HITL warning for high-risk without HITL
        if (manifest.get("tool_risk_profile") in {"high", "critical"} 
            and manifest.get("default_hitl_mode") == "none"):
            warnings.append("High-risk capsule with no HITL - consider requiring human approval")
        
        return ManifestValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_prod_restrictions(self, manifest: Dict[str, Any]) -> List[str]:
        """Check production environment restrictions."""
        errors = []
        
        # No open egress in prod
        if manifest.get("egress_mode") == "open":
            errors.append("egress_mode='open' is not allowed in PROD environment")
        
        # Must have at least one guardrail in prod
        if not manifest.get("opa_policy_packages") and not manifest.get("guardrail_profiles"):
            errors.append("Capsules in PROD must have at least one policy package or guardrail profile")
        
        # High/critical risk capsules require HITL in prod
        if manifest.get("tool_risk_profile") in {"high", "critical"}:
            if manifest.get("default_hitl_mode") == "none":
                errors.append("High/critical risk capsules require HITL in PROD (default_hitl_mode != 'none')")
        
        return errors
    
    def to_capsule_record(
        self, 
        manifest: Dict[str, Any], 
        tenant_id: str,
        generate_id: bool = True
    ) -> CapsuleRecord:
        """Convert validated manifest to CapsuleRecord."""
        # Validate first
        result = self.validate(manifest)
        if not result.valid:
            raise ManifestValidationError(
                f"Manifest validation failed: {result.errors}",
                errors=result.errors
            )
        
        capsule_id = manifest.get("id") or (str(uuid.uuid4()) if generate_id else None)
        if not capsule_id:
            raise ManifestValidationError("Capsule ID is required")
        
        return CapsuleRecord(
            capsule_id=capsule_id,
            tenant_id=tenant_id,
            name=manifest["name"],
            version=manifest.get("version", "1.0.0"),
            status=CapsuleStatus(manifest.get("status", "draft")),
            description=manifest.get("description", ""),
            default_persona_ref_id=manifest.get("default_persona_ref_id"),
            role_overrides=manifest.get("role_overrides", {}),
            allowed_tools=manifest.get("allowed_tools", []),
            prohibited_tools=manifest.get("prohibited_tools", []),
            allowed_mcp_servers=manifest.get("allowed_mcp_servers", []),
            tool_risk_profile=manifest.get("tool_risk_profile", "standard"),
            max_wall_clock_seconds=manifest.get("max_wall_clock_seconds", 3600),
            max_concurrent_nodes=manifest.get("max_concurrent_nodes", 5),
            allowed_runtimes=manifest.get("allowed_runtimes", ["python", "node"]),
            resource_profile=manifest.get("resource_profile", "default"),
            allowed_domains=manifest.get("allowed_domains", []),
            blocked_domains=manifest.get("blocked_domains", []),
            egress_mode=manifest.get("egress_mode", "restricted"),
            opa_policy_packages=manifest.get("opa_policy_packages", []),
            guardrail_profiles=manifest.get("guardrail_profiles", []),
            default_hitl_mode=manifest.get("default_hitl_mode", "optional"),
            risk_thresholds=manifest.get("risk_thresholds", {}),
            max_pending_hitl=manifest.get("max_pending_hitl", 10),
            rl_export_allowed=manifest.get("rl_export_allowed", False),
            rl_export_scope=manifest.get("rl_export_scope", "tenant"),
            rl_excluded_fields=manifest.get("rl_excluded_fields", []),
            example_store_policy=manifest.get("example_store_policy", "retain"),
            data_classification=manifest.get("data_classification", "internal"),
            retention_policy_days=manifest.get("retention_policy_days", 365),
            installed=False,
            metadata=manifest.get("metadata", {}),
        )


async def parse_manifest(
    content: str | Path,
    tenant_id: str,
    environment: str | None = None,
    persist: bool = False,
) -> CapsuleRecord:
    """Parse and optionally persist a capsule manifest.
    
    Args:
        content: YAML string or Path to manifest file
        tenant_id: Tenant ID for the capsule
        environment: Override environment for validation
        persist: If True, save to database
    
    Returns:
        CapsuleRecord parsed from manifest
    
    Raises:
        ManifestValidationError: If validation fails
    """
    parser = ManifestParser(environment=environment)
    
    if isinstance(content, Path):
        data = parser.parse_file(content)
    else:
        data = parser.parse_string(content)
    
    record = parser.to_capsule_record(data, tenant_id)
    
    if persist:
        store = CapsuleStore()
        await store.ensure_schema()
        await store.create(record)
    
    return record
