from __future__ import annotations

from app.db.session import SessionLocal
from app.services.evaluation.report_generator import build_evaluation_report


def main() -> None:
    with SessionLocal() as db:
        report = build_evaluation_report(db)
        print(f"Created evaluation report {report['id']} at {report['markdownPath']}.")


if __name__ == "__main__":
    main()
