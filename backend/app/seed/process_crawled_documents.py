from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.services.crawled_documents import list_crawled_documents, process_crawled_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process crawled legal documents through the Phase 6 OCR and bilingual pipeline.",
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR even when direct text extraction is available.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional number of crawled documents to process. Defaults to all.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    session = SessionLocal()
    try:
        documents = list_crawled_documents(session)
        if args.limit > 0:
            documents = documents[: args.limit]
        if not documents:
            print("No crawled documents are available to process.")
            return

        for document in documents:
            processed = process_crawled_document(session, document, force_ocr=args.force_ocr)
            print(
                f"{processed.title}: {processed.processing_status.value} | "
                f"language={processed.language_detected} | ocr={processed.ocr_status}"
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()
