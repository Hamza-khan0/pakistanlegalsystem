from __future__ import annotations

import argparse
import errno
import os
import socket
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_HOST = "127.0.0.1"
FALLBACK_PORTS = [8000, 8001, 8002, 8010]


def _candidate_ports(preferred_port: int) -> list[int]:
    return list(dict.fromkeys([preferred_port, *FALLBACK_PORTS]))


def _diagnose_bind_error(exc: OSError) -> str:
    winerror = getattr(exc, "winerror", None)
    if winerror == 10013:
        return "Windows denied binding this port, often because it is reserved/excluded or blocked by security policy."
    if winerror == 10048 or exc.errno == errno.EADDRINUSE:
        return "The port is already in use by another process."
    if exc.errno == errno.EACCES:
        return "Permission denied while binding the port."
    return str(exc)


def _can_bind(host: str, port: int) -> tuple[bool, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        return True, "available"
    except OSError as exc:
        return False, _diagnose_bind_error(exc)
    finally:
        sock.close()


def _print_diagnostics() -> None:
    print("\nAll candidate ports failed. Useful Windows diagnostics:")
    print("  netstat -ano | findstr :8000")
    print("  netstat -ano | findstr :8001")
    print("  netsh interface ipv4 show excludedportrange protocol=tcp")
    print("\nIf port 8000 is excluded, start on 8001 and set:")
    print("  $env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8001'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Start AI Legal Chambers FastAPI on a safe local port.")
    parser.add_argument("--host", default=os.getenv("BACKEND_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("BACKEND_PORT", "8000")))
    parser.add_argument("--no-reload", action="store_true", help="Disable uvicorn reload mode.")
    args = parser.parse_args()

    print("=== AI Legal Chambers Backend Dev Start ===")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")
    print(f"host={args.host}")

    selected_port: int | None = None
    for port in _candidate_ports(args.port):
        ok, reason = _can_bind(args.host, port)
        print(f"checking {args.host}:{port} -> {reason}")
        if ok:
            selected_port = port
            break

    if selected_port is None:
        _print_diagnostics()
        return 1

    os.environ["BACKEND_HOST"] = args.host
    os.environ["BACKEND_PORT"] = str(selected_port)
    os.chdir(BACKEND_DIR)
    sys.path.insert(0, str(BACKEND_DIR))

    print(f"\nStarting FastAPI on http://{args.host}:{selected_port}")
    print("Health check will be:")
    print(f"  http://{args.host}:{selected_port}/health")
    if selected_port != args.port:
        print("\nFrontend note:")
        print(f"  Set NEXT_PUBLIC_API_BASE_URL=http://{args.host}:{selected_port}")
        print("  Then restart the Next.js dev server.")

    try:
        import uvicorn
    except ImportError as exc:
        print("uvicorn is not installed in this Python environment.")
        return 1

    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=selected_port,
            reload=not args.no_reload,
            app_dir=str(BACKEND_DIR),
        )
    except OSError as exc:
        print(f"Backend failed after selecting port {selected_port}: {_diagnose_bind_error(exc)}")
        _print_diagnostics()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
