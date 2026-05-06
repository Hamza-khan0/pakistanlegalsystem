from __future__ import annotations

from app.db.session import SessionLocal
from app.services.corpus import export_corpus_datasets


def main() -> None:
    session = SessionLocal()
    try:
        stats = export_corpus_datasets(session)
        print(
            "Exported corpus successfully. "
            f"Output: {stats.output_dir}, "
            f"Retrieval: {stats.retrieval_records}, "
            f"Classification: {stats.classification_records}, "
            f"Bilingual: {stats.bilingual_records}."
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
