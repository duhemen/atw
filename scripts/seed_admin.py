"""Buat user admin default."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from loguru import logger
from sqlalchemy import text
from core.db import public_engine
from core.auth import hash_password


DEFAULT_USERS = [
    ("admin", "admin@atw.local", "Administrator ATW", "admin", "admin123"),
    ("verifikator1", "verif1@atw.local", "Verifikator Satu", "verifikator", "verif123"),
    ("kontributor1", "user1@atw.local", "Kontributor Satu", "kontributor", "user123"),
]


if __name__ == "__main__":
    with public_engine.begin() as conn:
        for username, email, full_name, role, password in DEFAULT_USERS:
            existing = conn.execute(
                text("SELECT id FROM users WHERE username = :u"), {"u": username}
            ).fetchone()
            if existing:
                logger.info(f"⏭️  User '{username}' sudah ada")
                continue

            conn.execute(
                text("""
                    INSERT INTO users (username, email, full_name, password_hash, role, is_active)
                    VALUES (:u, :e, :fn, :ph, :r, true)
                """),
                {"u": username, "e": email, "fn": full_name,
                 "ph": hash_password(password), "r": role},
            )
            logger.info(f"✅ User '{username}' dibuat (role: {role}, password: {password})")

    logger.info("🎉 Seed selesai")
    logger.warning("⚠️  GANTI PASSWORD setelah login pertama!")