from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.seed.register_crawl_sources import ensure_demo_assets
from app.services.crawling.registry import list_crawl_sources, register_seed_crawl_sources
from app.services.crawling.runner import run_crawl_job


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run configured legal crawl sources for Phase 6 corpus acquisition.",
    )
    parser.add_argument(
        "--source",
        dest="source_match",
        default="",
        help="Optional source id or partial source name. If omitted, all active sources run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_match = args.source_match.strip().casefold()

    ensure_demo_assets()
    session = SessionLocal()
    try:
        register_seed_crawl_sources(session)
        sources = [
            source
            for source in list_crawl_sources(session)
            if source.is_active
            and (
                not source_match
                or source.id.casefold() == source_match
                or source_match in source.name.casefold()
            )
        ]
        if not sources:
            print("No matching active crawl sources were found.")
            return

        for source in sources:
            job = run_crawl_job(session, source=source)
            print(
                f"{source.name}: {job.status.value} | "
                f"pages={job.pages_fetched} | discovered={job.documents_discovered} | "
                f"saved={job.documents_saved} | errors={job.errors_count}"
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()
