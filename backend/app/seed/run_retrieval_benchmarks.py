from __future__ import annotations

from app.db.session import SessionLocal
from app.services.evaluation.retrieval_benchmark import run_retrieval_benchmark


def main() -> None:
    with SessionLocal() as db:
        benchmark = run_retrieval_benchmark(db)
        print(f"Created retrieval benchmark {benchmark['id']} with {benchmark['queryCount']} benchmark queries.")


if __name__ == "__main__":
    main()
