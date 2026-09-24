"""FastAPI app untuk dashboard publik ATW."""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI, Request, Response, HTTPException,
    UploadFile, File, Form,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import text

from core.spatial_engine import spatial
from core.db import public_engine
from core.auth import (
    hash_password, verify_password, create_session,
    get_current_user, delete_session, require_role,
)


# =========================================================
# DIRECTORIES
# =========================================================
BASE = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE / "templates"
STATIC_DIR = BASE / "static"
PHOTO_DIR = BASE.parent / "data" / "photos"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}


# =========================================================
# APP INIT
# =========================================================
app = FastAPI(
    title="ATW - Anggaran Transparency Watch",
    description="Platform transparansi anggaran berbasis spasial",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/photos", StaticFiles(directory=str(PHOTO_DIR)), name="photos")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =========================================================
# SCHEMAS
# =========================================================
class FeedbackIn(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=150)
    category: str = Field(..., max_length=50)
    subject: str = Field(..., max_length=200)
    message: str = Field(..., max_length=3000)
    region_id: Optional[int] = None
    page_url: Optional[str] = Field(None, max_length=500)


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=150)
    full_name: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class LoginIn(BaseModel):
    username: str
    password: str


# =========================================================
# TEMPLATE HELPER
# =========================================================
def render(request: Request, template: str, **kwargs):
    """Helper TemplateResponse — auto inject user, counts, total."""
    counts = spatial.count_by_level()
    user = get_current_user(request)
    return templates.TemplateResponse(template, {
        "request": request,
        "user": user,
        "counts": counts,
        "total": sum(counts.values()),
        **kwargs,
    })


# =========================================================
# HALAMAN PUBLIK
# =========================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render(
        request, "map.html",
        title="ATW — Peta Anggaran Indonesia",
        active_page="map",
    )


@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request):
    with public_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, nama FROM regions WHERE level = 'kabupaten' ORDER BY nama")
        ).fetchall()
    regions = [{"id": r[0], "nama": r[1]} for r in rows]

    return render(
        request, "feedback.html",
        title="Feedback — ATW",
        active_page="feedback",
        regions=regions,
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render(
        request, "login.html",
        title="Login — ATW",
        active_page="login",
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return render(
        request, "register.html",
        title="Daftar — ATW",
        active_page="register",
    )


@app.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request):
    user = get_current_user(request)
    if not user:
        return HTMLResponse('<script>window.location.href="/login";</script>')
    if user["role"] not in ("verifikator", "admin"):
        return HTMLResponse(
            "<html><body style='font-family:sans-serif;padding:40px;text-align:center'>"
            "<h1>403 — Akses Ditolak</h1>"
            "<p>Halaman ini hanya untuk verifikator/admin.</p>"
            "<a href='/' style='color:#0f5132'>Kembali ke Peta</a>"
            "</body></html>",
            status_code=403,
        )
    return render(
        request, "verify.html",
        title="Verifikasi Foto — ATW",
        active_page="verify",
    )


# =========================================================
# API — REGIONS
# =========================================================
@app.get("/api/regions/{level}/geojson")
async def regions_geojson(level: str, limit: int | None = None):
    if level not in ("provinsi", "kabupaten", "kecamatan", "kelurahan"):
        return JSONResponse({"error": "invalid level"}, status_code=400)
    return spatial.all_regions_geojson(level=level, limit=limit)


@app.get("/api/regions/{level}/fiscal-geojson")
async def regions_fiscal_geojson(level: str, year: int = 2024, limit: int | None = None):
    if level not in ("provinsi", "kabupaten", "kecamatan"):
        return JSONResponse({"error": "invalid level"}, status_code=400)
    return spatial.regions_geojson_with_fiscal(level=level, year=year, limit=limit)


@app.get("/api/regions/{region_id}")
async def region_detail(region_id: int):
    gj = spatial.region_geojson(region_id)
    if not gj:
        return JSONResponse({"error": "not found"}, status_code=404)
    return gj


@app.get("/api/regions/{region_id}/fiscal")
async def region_fiscal(region_id: int, year: int = 2024):
    detail = spatial.region_detail_with_fiscal(region_id, year)
    if not detail:
        return JSONResponse({"error": "not found"}, status_code=404)
    return detail


@app.get("/api/regions/{region_id}/children")
async def region_children(region_id: int):
    with public_engine.connect() as conn:
        row = conn.execute(
            text("SELECT kode_bps FROM regions WHERE id = :id"), {"id": region_id}
        ).fetchone()
    if not row:
        return JSONResponse({"error": "not found"}, status_code=404)
    return spatial.get_children(row[0])


@app.get("/api/point")
async def point_in_region(lat: float, lon: float):
    return spatial.point_in_region(lat, lon)


@app.get("/api/stats")
async def stats():
    counts = spatial.count_by_level()
    return {"total": sum(counts.values()), "by_level": counts}


# =========================================================
# API — FEEDBACK
# =========================================================
@app.post("/api/feedback")
async def submit_feedback(request: Request, payload: FeedbackIn):
    VALID_CATEGORIES = {"bug_report", "data_issue", "suggestion", "question", "other"}
    if payload.category not in VALID_CATEGORIES:
        raise HTTPException(400, "Kategori tidak valid")

    if len(payload.message.strip()) < 10:
        raise HTTPException(400, "Pesan minimal 10 karakter")

    user_agent = request.headers.get("user-agent", "")[:500]

    with public_engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO feedback
                (name, email, category, subject, message, region_id, page_url, user_agent, status)
                VALUES (:name, :email, :category, :subject, :message, :region_id, :page_url, :ua, 'new')
                RETURNING id
            """),
            {
                "name": payload.name,
                "email": payload.email,
                "category": payload.category,
                "subject": payload.subject.strip(),
                "message": payload.message.strip(),
                "region_id": payload.region_id,
                "page_url": payload.page_url,
                "ua": user_agent,
            },
        )
        feedback_id = result.scalar()

    logger.info(f"📬 Feedback #{feedback_id} dari {payload.name or 'anonim'} [{payload.category}]")

    return {"success": True, "feedback_id": feedback_id, "message": "Feedback berhasil dikirim"}


# =========================================================
# API — PHOTOS
# =========================================================
@app.post("/api/photos/upload")
async def upload_photo(
    request: Request,
    region_id: int = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    latitude: float = Form(None),
    longitude: float = Form(None),
    file: UploadFile = File(...),
):
    """Upload foto dokumentasi. User harus login. Status: pending."""
    user = require_role(request, ["kontributor", "verifikator", "admin"])

    # Validasi file
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(400, f"Format tidak didukung: {file.content_type}. Gunakan JPG/PNG/WebP.")

    contents = await file.read()
    if len(contents) > MAX_PHOTO_SIZE:
        raise HTTPException(400, f"File terlalu besar (max 5 MB). Ukuran: {len(contents)/1024/1024:.2f} MB")

    # Validasi region exists
    with public_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM regions WHERE id = :id"), {"id": region_id}
        ).fetchone()
    if not exists:
        raise HTTPException(404, "Wilayah tidak ditemukan")

    # Simpan file
    region_dir = PHOTO_DIR / str(region_id)
    region_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = region_dir / filename

    with open(file_path, "wb") as f:
        f.write(contents)

    rel_path = f"/photos/{region_id}/{filename}"

    # Insert DB — status PENDING
    with public_engine.begin() as conn:
        if latitude is not None and longitude is not None:
            result = conn.execute(
                text("""
                    INSERT INTO project_photos
                    (region_id, category, title, description, file_path, file_size, mime_type,
                     latitude, longitude, geom, uploaded_by, status)
                    VALUES
                    (:rid, :cat, :title, :desc, :path, :size, :mime,
                     :lat, :lng, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                     :uploader, 'pending')
                    RETURNING id
                """),
                {
                    "rid": region_id, "cat": category, "title": title, "desc": description,
                    "path": rel_path, "size": len(contents), "mime": file.content_type,
                    "lat": latitude, "lng": longitude, "uploader": user["username"],
                },
            )
        else:
            result = conn.execute(
                text("""
                    INSERT INTO project_photos
                    (region_id, category, title, description, file_path, file_size, mime_type,
                     uploaded_by, status)
                    VALUES
                    (:rid, :cat, :title, :desc, :path, :size, :mime, :uploader, 'pending')
                    RETURNING id
                """),
                {
                    "rid": region_id, "cat": category, "title": title, "desc": description,
                    "path": rel_path, "size": len(contents), "mime": file.content_type,
                    "uploader": user["username"],
                },
            )

        photo_id = result.scalar()

    logger.info(f"📷 Photo #{photo_id} uploaded by {user['username']}: {title} (pending)")

    return {
        "success": True,
        "photo_id": photo_id,
        "file_path": rel_path,
        "status": "pending",
        "message": "Foto berhasil diupload. Menunggu verifikasi.",
    }


@app.get("/api/photos")
async def list_photos(region_id: int = None, limit: int = 100):
    sql = """
        SELECT p.id, p.region_id, p.category, p.title, p.description,
               p.file_path, p.latitude, p.longitude, p.uploaded_by, p.created_at,
               r.nama AS region_nama
        FROM project_photos p
        JOIN regions r ON r.id = p.region_id
        WHERE p.status = 'approved'
    """
    params = {"limit": limit}
    if region_id:
        sql += " AND p.region_id = :rid"
        params["rid"] = region_id
    sql += " ORDER BY p.created_at DESC LIMIT :limit"

    with public_engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    return [
        {
            "id": r[0], "region_id": r[1], "category": r[2], "title": r[3],
            "description": r[4], "file_path": r[5],
            "latitude": r[6], "longitude": r[7],
            "uploaded_by": r[8],
            "created_at": r[9].isoformat() if r[9] else None,
            "region_nama": r[10],
        }
        for r in rows
    ]


@app.get("/api/photos/geojson")
async def photos_geojson():
    with public_engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT p.id, p.region_id, p.category, p.title, p.description,
                       p.file_path, p.uploaded_by, p.created_at,
                       ST_X(p.geom) AS lng, ST_Y(p.geom) AS lat,
                       r.nama AS region_nama
                FROM project_photos p
                JOIN regions r ON r.id = p.region_id
                WHERE p.status = 'approved'
                  AND p.geom IS NOT NULL
                ORDER BY p.created_at DESC
            """)
        ).fetchall()

    features = []
    for r in rows:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r[8], r[9]]},
            "properties": {
                "id": r[0], "region_id": r[1], "category": r[2],
                "title": r[3], "description": r[4], "file_path": r[5],
                "uploaded_by": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
                "region_nama": r[10],
            },
        })

    return {"type": "FeatureCollection", "features": features}


@app.get("/api/photos/pending")
async def list_pending_photos(request: Request):
    require_role(request, ["verifikator", "admin"])

    with public_engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT p.id, p.region_id, p.category, p.title, p.description,
                       p.file_path, p.latitude, p.longitude, p.uploaded_by, p.created_at,
                       r.nama AS region_nama
                FROM project_photos p
                JOIN regions r ON r.id = p.region_id
                WHERE p.status = 'pending'
                ORDER BY p.created_at DESC
            """)
        ).fetchall()

    return [
        {
            "id": r[0], "region_id": r[1], "category": r[2], "title": r[3],
            "description": r[4], "file_path": r[5],
            "latitude": r[6], "longitude": r[7],
            "uploaded_by": r[8],
            "created_at": r[9].isoformat() if r[9] else None,
            "region_nama": r[10],
        }
        for r in rows
    ]


@app.post("/api/photos/{photo_id}/approve")
async def approve_photo(photo_id: int, request: Request):
    user = require_role(request, ["verifikator", "admin"])

    with public_engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE project_photos
                SET status = 'approved', verified_by = :uid, verified_at = :now
                WHERE id = :id
            """),
            {"uid": user["id"], "now": datetime.utcnow(), "id": photo_id},
        )
    return {"success": True}


@app.post("/api/photos/{photo_id}/reject")
async def reject_photo(photo_id: int, request: Request, reason: str = Form("")):
    user = require_role(request, ["verifikator", "admin"])

    with public_engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE project_photos
                SET status = 'rejected', verified_by = :uid, verified_at = :now,
                    rejection_reason = :reason
                WHERE id = :id
            """),
            {"uid": user["id"], "now": datetime.utcnow(), "id": photo_id, "reason": reason},
        )
    return {"success": True}


@app.delete("/api/photos/{photo_id}")
async def delete_photo(photo_id: int, request: Request):
    require_role(request, ["verifikator", "admin"])

    with public_engine.begin() as conn:
        row = conn.execute(
            text("SELECT file_path FROM project_photos WHERE id = :id"),
            {"id": photo_id},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Foto tidak ditemukan")

        file_path = BASE.parent / "data" / row[0].lstrip("/")
        if file_path.exists():
            file_path.unlink()

        conn.execute(text("DELETE FROM project_photos WHERE id = :id"), {"id": photo_id})

    return {"success": True, "message": "Foto dihapus"}


# =========================================================
# API — AUTH
# =========================================================
@app.post("/api/auth/register")
async def register(request: Request, payload: RegisterIn, response: Response):
    with public_engine.begin() as conn:
        dup = conn.execute(
            text("SELECT id FROM users WHERE username = :u OR email = :e"),
            {"u": payload.username, "e": payload.email},
        ).fetchone()
        if dup:
            raise HTTPException(400, "Username atau email sudah terdaftar")

        result = conn.execute(
            text("""
                INSERT INTO users (username, email, full_name, password_hash, role)
                VALUES (:u, :e, :fn, :ph, 'kontributor')
                RETURNING id
            """),
            {"u": payload.username, "e": payload.email, "fn": payload.full_name,
             "ph": hash_password(payload.password)},
        )
        user_id = result.scalar()

    token = create_session(user_id, request.headers.get("user-agent", ""), request.client.host)
    response.set_cookie("atw_session", token, max_age=7*24*3600, httponly=True, samesite="lax")
    return {"success": True, "user_id": user_id, "message": "Registrasi berhasil"}


@app.post("/api/auth/login")
async def login(request: Request, payload: LoginIn, response: Response):
    with public_engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, password_hash, is_active FROM users WHERE username = :u"),
            {"u": payload.username},
        ).fetchone()

    if not row or not verify_password(payload.password, row[1]):
        raise HTTPException(401, "Username atau password salah")
    if not row[2]:
        raise HTTPException(403, "Akun tidak aktif")

    token = create_session(row[0], request.headers.get("user-agent", ""), request.client.host)
    response.set_cookie("atw_session", token, max_age=7*24*3600, httponly=True, samesite="lax")
    return {"success": True, "user_id": row[0], "message": "Login berhasil"}


@app.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("atw_session")
    if token:
        delete_session(token)
    response.delete_cookie("atw_session")
    return {"success": True}


@app.get("/api/auth/me")
async def me(request: Request):
    user = get_current_user(request)
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}


# =========================================================
# STARTUP
# =========================================================
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 ATW Public API started")
    counts = spatial.count_by_level()
    logger.info(f"📊 Regions loaded: {sum(counts.values()):,}")