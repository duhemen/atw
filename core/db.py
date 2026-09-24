"""Database session manager untuk ATW & FVI."""
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.models import PublicBase, InternalBase


public_engine = create_engine(settings.PUBLIC_DB_URL, echo=False, pool_pre_ping=True)
PublicSession = sessionmaker(bind=public_engine, autoflush=False)

internal_engine = create_engine(settings.INTERNAL_DB_URL, echo=False, pool_pre_ping=True)
InternalSession = sessionmaker(bind=internal_engine, autoflush=False)


@contextmanager
def public_db():
    db = PublicSession()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def internal_db():
    db = InternalSession()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_all():
    """Buat semua tabel di kedua database."""
    with public_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    PublicBase.metadata.create_all(public_engine)

    with internal_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    InternalBase.metadata.create_all(internal_engine)

    print("✅ Database initialized.")