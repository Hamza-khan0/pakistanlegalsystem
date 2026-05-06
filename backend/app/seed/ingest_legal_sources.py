from __future__ import annotations

from app.db.session import SessionLocal
from app.services.knowledge.ingestion import ingest_seed_legal_sources


def main() -> None:
    session = SessionLocal()
    try:
        stats = ingest_seed_legal_sources(session, reset_existing=True)
        print(
            f"Ingested legal corpus successfully. Sources: {stats.sources_created}, chunks: {stats.chunks_created}."
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
