"""Buat tabel users, sessions, update project_photos."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from loguru import logger
from sqlalchemy import text
from core.db import public_engine
from core.models import PublicBase, User, UserSession  # noqa


if __name__ == "__main__":
    logger.info("🔧 Creating users & sessions tables...")
    PublicBase.metadata.create_all(public_engine)

    # ALTER project_photos — tambah kolom baru
    with public_engine.begin() as conn:
        for col, sql in [
            ("verified_by", "ALTER TABLE project_photos ADD COLUMN IF NOT EXISTS verified_by INTEGER REFERENCES users(id)"),
            ("verified_at", "ALTER TABLE project_photos ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP"),
            ("rejection_reason", "ALTER TABLE project_photos ADD COLUMN IF NOT EXISTS rejection_reason TEXT"),
        ]:
            try:
                conn.execute(text(sql))
                logger.info(f"   ✓ column {col} OK")
            except Exception as e:
                logger.warning(f"   ⚠️ {col}: {e}")

    logger.info("✅ Tables ready")