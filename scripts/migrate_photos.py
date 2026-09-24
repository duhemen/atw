"""Buat tabel project_photos."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from loguru import logger
from core.db import public_engine
from core.models import PublicBase, ProjectPhoto  # noqa


if __name__ == "__main__":
    logger.info("🔧 Creating project_photos table...")
    PublicBase.metadata.create_all(public_engine)
    logger.info("✅ Table ready")

    # Buat folder uploads
    photo_dir = BASE / "data" / "photos"
    photo_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Photo storage: {photo_dir}")