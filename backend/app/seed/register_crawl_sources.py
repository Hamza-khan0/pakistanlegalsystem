from __future__ import annotations

from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.crawling.registry import register_seed_crawl_sources


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def ensure_demo_assets() -> None:
    assets_dir = Path(settings.crawl_seed_dir) / "fixtures" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = assets_dir / "constitutional_remedy_note.pdf"
    if not pdf_path.exists():
        document = fitz.open()
        page = document.new_page(width=595, height=842)
        page.insert_text(
            (72, 96),
            (
                "Constitution Article 199 - Chamber PDF Excerpt\n\n"
                "A High Court may intervene where a public functionary acts without lawful authority.\n"
                "The chamber should still test alternate remedy, urgency, and the exact public-law hook."
            ),
            fontsize=12,
        )
        document.save(pdf_path)
        document.close()

    image_path = assets_dir / "horizon_customs_order.png"
    if not image_path.exists():
        image = Image.new("RGB", (1280, 900), color="white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        text = (
            "Sindh High Court - Interim Customs Order\n\n"
            "The petitioner alleges detention of textile inputs without hearing.\n"
            "The matter raises urgency, alternate remedy, and jurisdictional overreach.\n"
            "Counsel must verify the valuation note and the precise date of communication."
        )
        draw.multiline_text((40, 60), text, fill="black", font=font, spacing=8)
        image.save(image_path)


def main() -> None:
    ensure_demo_assets()
    session = SessionLocal()
    try:
        sources = register_seed_crawl_sources(session)
        print(f"Registered crawl sources successfully. Sources: {len(sources)}.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
