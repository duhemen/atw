"""Migrasi wilayah_boundaries (staging) -> regions (atw_public).

Konversi format `path` (JSON array) menjadi WKT untuk PostGIS.
"""
import sys
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from loguru import logger
from sqlalchemy import create_engine, text
from core.config import settings
from sqlalchemy.engine import URL

# ---------------------------------------------------------
# Konversi JSON array -> WKT MULTIPOLYGON
# ---------------------------------------------------------
def json_array_to_wkt(coord_array) -> str:
    """Konversi array koordinat JSON ke WKT.

    Format input:
      - Polygon:      [[[x,y],...]]         (1 ring)
      - MultiPolygon: [[[[x,y],...]], ...]  (beberapa polygon)
    Format output:
      - MULTIPOLYGON(((x y, x y, ...)), ...)
    """

    def ring_to_wkt(ring) -> str:
        return ", ".join(f"{pt[0]} {pt[1]}" for pt in ring)

    def polygon_to_wkt(poly) -> str:
        rings = [f"({ring_to_wkt(r)})" for r in poly]
        return "(" + ", ".join(rings) + ")"

    # Deteksi bentuk
    first = coord_array[0]
    # Polygon sederhana: [[[x,y],...]]
    if isinstance(first[0][0], (int, float)):
        return "MULTIPOLYGON(" + polygon_to_wkt(coord_array) + ")"
    # MultiPolygon: [[[[x,y],...]], ...]
    polygons = [polygon_to_wkt(p) for p in coord_array]
    return "MULTIPOLYGON(" + ", ".join(polygons) + ")"


def detect_level(kode: str) -> str:
    """Deteksi level wilayah dari format kode BPS."""
    dots = kode.count(".")
    return {0: "provinsi", 1: "kabupaten", 2: "kecamatan", 3: "kelurahan"}.get(dots, "unknown")


def migrate(staging_db: str = "atw_staging", level_filter: str = None):
    """Migrasi dari staging ke atw_public.regions."""

    staging_url = URL.create(
        drivername="postgresql+psycopg2",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=staging_db,
    )
    staging_engine = create_engine(staging_url, echo=False)
    target_engine = create_engine(settings.PUBLIC_DB_URL, echo=False)

    # 1. Baca dari staging
    query = "SELECT kode, nama, path FROM wilayah_boundaries ORDER BY kode"
    with staging_engine.connect() as conn:
        rows = list(conn.execute(text(query)))

    logger.info(f"📦 {len(rows)} baris ditemukan di staging")

    # 2. Migrasi
    inserted = 0
    failed = 0
    skipped = 0
    first_errors = []  # kumpulkan 20 error pertama untuk diagnosis

    with target_engine.connect() as conn:
        for kode, nama, path_json in rows:
            level = detect_level(kode)

            if level_filter and level != level_filter:
                skipped += 1
                continue

            if not path_json:
                skipped += 1
                continue

            try:
                coords = json.loads(path_json)
                wkt = json_array_to_wkt(coords)

                # SAVEPOINT per baris: kalau gagal, hanya baris ini yang rollback
                with conn.begin_nested():
                    conn.execute(
                        text("""
                            INSERT INTO regions (level, kode_bps, nama, geom)
                            VALUES (
                                :level, :kode, :nama,
                                ST_Multi(ST_GeomFromText(:wkt, 4326))
                            )
                            ON CONFLICT DO NOTHING
                        """),
                        {"level": level, "kode": kode, "nama": nama, "wkt": wkt},
                    )
                inserted += 1

                if inserted % 500 == 0:
                    logger.info(f"  ✓ {inserted} migrasi...")

            except Exception as e:
                failed += 1
                err = str(e).split("\n")[0][:200]
                if len(first_errors) < 20:
                    first_errors.append(f"{kode} ({nama}): {err}")
                # Jangan log setiap error, cuma kumpulkan

        # Commit sekali di akhir
        conn.commit()

    # Tampilkan error teratas untuk diagnosis
    if first_errors:
        logger.warning("🔍 20 error pertama (untuk diagnosis):")
        for err in first_errors:
            logger.warning(f"   {err}")

    logger.info(f"🎉 Selesai. Inserted: {inserted}, Gagal: {failed}, Skipped: {skipped}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", default="atw_staging")
    parser.add_argument("--level", default=None,
                        help="Filter level: provinsi|kabupaten|kecamatan|kelurahan")
    args = parser.parse_args()

    migrate(staging_db=args.staging, level_filter=args.level)