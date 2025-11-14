#!/usr/bin/env python3
"""Run all Agent Zero runtime services locally without Docker.

This helper script starts the Gateway plus all background workers in the
same Python virtual environment. It mirrors the Docker Compose runtime but
keeps configuration centralized through a single environment file.

Usage examples:

    # Load default .env and start all services
    python scripts/runstack.py

    # Load an explicit env file and enable uvicorn reload for Gateway
    python scripts/runstack.py --env-file config/dev.env --reload

Stop the stack with Ctrl+C. If any service exits unexpectedly, the script
will terminate the remaining processes and exit with that return code.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from dotenv import load_dotenv
from services.common import env as env_snapshot

REPO_ROOT = Path(__file__).resolve().parents[1]


ProcessSpec = Tuple[str, List[str]]


def _ensure_pythonpath(env: Dict[str, str]) -> None:
    """Guarantee that the repository root is present on PYTHONPATH."""

    current = env.get("PYTHONPATH")
    repo_path = str(REPO_ROOT)
    if not current:
        env["PYTHONPATH"] = repo_path
        return
    paths = current.split(os.pathsep)
    if repo_path not in paths:
        env["PYTHONPATH"] = os.pathsep.join([repo_path, *paths])


def _default_env() -> Dict[str, str]:
    env = os.environ.copy()
    env.setdefault("LOG_LEVEL", "INFO")
    _ensure_pythonpath(env)
    return env


def _process_specs(enable_reload: bool, host: str, port: str) -> List[ProcessSpec]:
    gateway_cmd = [
        "uvicorn",
        "services.gateway.main:app",
        "--host",
        host,
        "--port",
        port,
    ]
    if enable_reload:
        gateway_cmd.append("--reload")

    return [
        ("gateway", gateway_cmd),
        ("conversation-worker", ["python", "-m", "services.conversation_worker.main"]),
        ("tool-executor", ["python", "-m", "services.tool_executor.main"]),
        ("memory-replicator", ["python", "-m", "services.memory_replicator.main"]),
        ("memory-sync", ["python", "-m", "services.memory_sync.main"]),
        ("outbox-sync", ["python", "-m", "services.outbox_sync.main"]),
    ]


async def _launch(name: str, cmd: List[str], env: Dict[str, str]) -> asyncio.subprocess.Process:
    print(f"[runstack] starting {name}: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(*cmd, env=env)
    return process


async def _shutdown(processes: Dict[str, asyncio.subprocess.Process], reason: str) -> None:
    print(f"[runstack] stopping all services ({reason})")
    for name, proc in processes.items():
        if proc.returncode is None:
            try:
                proc.terminate()
                print(f"[runstack] sent SIGTERM to {name} (pid={proc.pid})")
            except ProcessLookupError:
                pass

    await asyncio.sleep(1)

    pending = [proc for proc in processes.values() if proc.returncode is None]
    if not pending:
        return

    try:
        await asyncio.wait_for(asyncio.gather(*(proc.wait() for proc in pending)), timeout=10)
    except asyncio.TimeoutError:
        for name, proc in processes.items():
            if proc.returncode is None:
                print(f"[runstack] forcing stop for {name} (pid={proc.pid})")
                proc.kill()
        await asyncio.gather(*(proc.wait() for proc in processes.values()), return_exceptions=True)


async def _wait_for_exit(
    processes: Dict[str, asyncio.subprocess.Process],
    stop_event: asyncio.Event,
) -> Tuple[str, int | None]:
    async def _proc_waiter(name: str, proc: asyncio.subprocess.Process):
        rc = await proc.wait()
        return name, rc

    waiters = [asyncio.create_task(_proc_waiter(name, proc)) for name, proc in processes.items()]

    async def _stop_waiter():
        await stop_event.wait()
        return ("signal", None)

    waiters.append(asyncio.create_task(_stop_waiter()))

    done, pending = await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    result = next(iter(done)).result()
    return result


def _load_env_files(paths: Iterable[Path]) -> None:
    for path in paths:
        if not path:
            continue
        resolved = path.expanduser().resolve()
        if resolved.is_file():
            load_dotenv(dotenv_path=resolved, override=True)
        else:
            raise FileNotFoundError(f"Environment file not found: {resolved}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Agent Zero runtime services locally.")
    parser.add_argument(
        "--env-file",
        action="append",
        dest="env_files",
        type=Path,
        help="Additional environment file(s) to load (default: .env).",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable uvicorn --reload for the Gateway service.",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Gateway bind host (default: env GATEWAY_HOST or 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        default=None,
        help="Gateway bind port (default: env GATEWAY_PORT or 8010)",
    )
    return parser.parse_args(argv)


async def main(argv: List[str]) -> int:
    args = parse_args(argv)

    # Load default .env followed by any explicit --env-file overrides.
    default_env_path = REPO_ROOT / ".env"
    load_dotenv(dotenv_path=default_env_path, override=True)
    if args.env_files:
        _load_env_files(args.env_files)
    env_snapshot.refresh()

    if args.host is None:
        args.host = env_snapshot.get("GATEWAY_HOST", "0.0.0.0") or "0.0.0.0"
    if args.port is None:
        args.port = env_snapshot.get("GATEWAY_PORT", "8010") or "8010"

    env = _default_env()
    specs = _process_specs(args.reload, args.host, args.port)

    processes: Dict[str, asyncio.subprocess.Process] = {}
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    signal_reason: Dict[str, str] = {}

    def _handle_signal(sig: int) -> None:
        name = signal.Signals(sig).name
        print(f"[runstack] received {name}, shutting down...", flush=True)
        signal_reason.setdefault("reason", name)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal, sig)
        except NotImplementedError:
            # add_signal_handler may not be available on some platforms (e.g., Windows)
            # Bind current value of `sig` to avoid late binding in the closure (Ruff B023)
            signal.signal(sig, lambda *_, sig=sig: _handle_signal(sig))

    try:
        for name, cmd in specs:
            processes[name] = await _launch(name, cmd, env)

        finished_name, return_code = await _wait_for_exit(processes, stop_event)

        if finished_name == "signal":
            reason = signal_reason.get("reason", "signal")
        else:
            reason = f"{finished_name} exited with code {return_code}"
        await _shutdown(processes, reason)

        if finished_name == "signal":
            return 0
        return return_code or 0
    except Exception as exc:
        # Ensure we always try to stop any started processes on error
        try:
            await _shutdown(processes, f"exception: {exc}")
        finally:
            # Re-raise so the caller sees the failure and a non-zero exit code propagates
            raise


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main(sys.argv[1:]))
    except FileNotFoundError as exc:
        print(f"[runstack] {exc}", file=sys.stderr)
        exit_code = 1
    except KeyboardInterrupt:
        exit_code = 0
    sys.exit(exit_code)
