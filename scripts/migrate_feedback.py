"""Buat tabel feedback di atw_public."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from loguru import logger
from core.db import public_engine
from core.models import PublicBase, Feedback  # noqa: F401


if __name__ == "__main__":
    logger.info("🔧 Creating feedback table...")
    PublicBase.metadata.create_all(public_engine)
    logger.info("✅ Feedback table ready")

    # Verifikasi
    from sqlalchemy import text
    with public_engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'feedback'")
        )
        exists = result.scalar()
        logger.info(f"   Table 'feedback' exists: {exists == 1}")