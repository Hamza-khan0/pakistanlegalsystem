from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"


def _run(label: str, command: list[str], *, cwd: Path) -> None:
    print(f"\n=== {label} ===", flush=True)
    print(f"cwd={cwd}", flush=True)
    print(" ".join(command), flush=True)
    completed = subprocess.run(command, cwd=cwd, env=os.environ.copy())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    python = sys.executable
    _run("Backend compile", [python, "-m", "compileall", "backend"], cwd=PROJECT_ROOT)
    _run("Alembic migrations", ["alembic", "upgrade", "head"], cwd=BACKEND_DIR)
    _run("Seed demo data", [python, "-m", "app.seed.seed_data"], cwd=BACKEND_DIR)
    _run("Runtime certification", [python, "-m", "app.seed.verify_runtime"], cwd=BACKEND_DIR)
    print("\nCertification complete. Reports are in verification_reports/.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
