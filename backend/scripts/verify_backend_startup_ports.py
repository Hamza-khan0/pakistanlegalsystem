from __future__ import annotations

import errno
import socket
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
HOST = "127.0.0.1"
PORTS = [8000, 8001, 8002, 8010]


def _reason(exc: OSError) -> str:
    winerror = getattr(exc, "winerror", None)
    if winerror == 10013:
        return "blocked/reserved by Windows (WinError 10013)"
    if winerror == 10048 or exc.errno == errno.EADDRINUSE:
        return "already in use"
    if exc.errno == errno.EACCES:
        return "permission denied"
    return str(exc)


def _check_port(port: int) -> tuple[bool, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, port))
        return True, "available"
    except OSError as exc:
        return False, _reason(exc)
    finally:
        sock.close()


def main() -> int:
    print("=== Backend Startup Port Verification ===")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")
    print(f"host={HOST}")

    available: list[int] = []
    for port in PORTS:
        ok, reason = _check_port(port)
        print(f"{HOST}:{port:<5} -> {'PASS' if ok else 'WARN'} - {reason}")
        if ok:
            available.append(port)

    if available:
        print(f"[PASS] usable_ports={available}")
        print(f"Recommended command: python scripts\\dev_start_backend.py --port {available[0]}")
        return 0

    print("[FAIL] No candidate backend ports are currently bindable.")
    print("Run these diagnostics in PowerShell:")
    print("  netstat -ano | findstr :8000")
    print("  netstat -ano | findstr :8001")
    print("  netsh interface ipv4 show excludedportrange protocol=tcp")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
