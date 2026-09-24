"""Auth helpers — password hash, session token, role check."""
import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import text
from core.db import public_engine


SESSION_DAYS = 7


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 hash."""
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100_000)
    return f"pbkdf2:sha256:100000${salt}${h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verifikasi password terhadap hash."""
    try:
        _, salt, hash_hex = stored.split("$")
        _, _, iterations = _.split(":")
        iterations = int(iterations)
        h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
        return secrets.compare_digest(h.hex(), hash_hex)
    except Exception:
        return False


def generate_token() -> str:
    """Generate session token."""
    return secrets.token_urlsafe(48)


def create_session(user_id: int, user_agent: str = "", ip: str = "") -> str:
    """Buat session baru, return token."""
    token = generate_token()
    expires = datetime.utcnow() + timedelta(days=SESSION_DAYS)

    with public_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO user_sessions (token, user_id, expires_at, user_agent, ip_address)
                VALUES (:token, :uid, :exp, :ua, :ip)
            """),
            {"token": token, "uid": user_id, "exp": expires, "ua": user_agent[:500], "ip": ip[:50]},
        )
        conn.execute(
            text("UPDATE users SET last_login = :now WHERE id = :id"),
            {"now": datetime.utcnow(), "id": user_id},
        )
    return token


def get_current_user(request) -> dict | None:
    """Ambil user dari cookie session."""
    token = request.cookies.get("atw_session")
    if not token:
        return None

    with public_engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT u.id, u.username, u.email, u.full_name, u.role, u.is_active,
                       s.expires_at
                FROM user_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = :token
            """),
            {"token": token},
        ).fetchone()

    if not row:
        return None
    if row[6] < datetime.utcnow():
        return None
    if not row[5]:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "full_name": row[3],
        "role": row[4],
    }


def require_role(request, roles: list[str]) -> dict:
    """Raises HTTPException jika role tidak sesuai."""
    from fastapi import HTTPException
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Login diperlukan")
    if user["role"] not in roles:
        raise HTTPException(403, f"Akses ditolak. Role minimal: {roles}")
    return user


def delete_session(token: str):
    with public_engine.begin() as conn:
        conn.execute(text("DELETE FROM user_sessions WHERE token = :t"), {"t": token})