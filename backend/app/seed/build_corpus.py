from __future__ import annotations

from app.db.session import SessionLocal
from app.services.corpus import build_corpus_entries


def main() -> None:
    session = SessionLocal()
    try:
        stats = build_corpus_entries(session)
        print(
            "Built corpus successfully. "
            f"Legal sources upserted: {stats.legal_sources_upserted}, "
            f"Corpus entries upserted: {stats.corpus_entries_upserted}, "
            f"Crawled documents promoted: {stats.crawled_documents_promoted}."
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
