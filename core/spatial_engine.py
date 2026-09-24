"""Spatial engine ATW: query wilayah, spatial join, GeoJSON untuk Leaflet."""
from typing import Optional
from sqlalchemy import text
from loguru import logger

from core.db import public_engine


class SpatialEngine:
    """Engine untuk operasi spasial ATW."""

    # ---------------------------------------------------------
    # COUNT & LIST
    # ---------------------------------------------------------
    def count_regions(self, level: Optional[str] = None) -> int:
        """Hitung jumlah wilayah."""
        with public_engine.connect() as conn:
            if level:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM regions WHERE level = :level"),
                    {"level": level},
                )
            else:
                result = conn.execute(text("SELECT COUNT(*) FROM regions"))
            return result.scalar()

    def count_by_level(self) -> dict:
        """Hitung wilayah per level."""
        with public_engine.connect() as conn:
            result = conn.execute(
                text("SELECT level, COUNT(*) FROM regions GROUP BY level ORDER BY level")
            )
            return {row[0]: row[1] for row in result}

    # ---------------------------------------------------------
    # POINT-IN-REGION
    # ---------------------------------------------------------
    def point_in_region(
        self, lat: float, lon: float, level: Optional[str] = None
    ) -> list[dict]:
        """Cari wilayah yang mengandung titik koordinat.

        Args:
            lat: latitude
            lon: longitude
            level: filter level (provinsi|kabupaten|kecamatan|kelurahan)

        Returns:
            List of dict {id, level, kode_bps, nama}
        """
        sql = """
            SELECT id, level, kode_bps, nama
            FROM regions
            WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
        """
        params = {"lat": lat, "lon": lon}
        if level:
            sql += " AND level = :level"
            params["level"] = level
        sql += " ORDER BY level"

        with public_engine.connect() as conn:
            result = conn.execute(text(sql), params)
            return [
                {"id": r[0], "level": r[1], "kode_bps": r[2], "nama": r[3]}
                for r in result
            ]

    # ---------------------------------------------------------
    # GEOJSON UNTUK LEAFLET
    # ---------------------------------------------------------
    def region_geojson(self, region_id: int) -> Optional[dict]:
        """Ambil satu wilayah sebagai GeoJSON Feature."""
        with public_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, level, kode_bps, nama, ST_AsGeoJSON(geom)::json
                    FROM regions WHERE id = :id
                """),
                {"id": region_id},
            )
            row = result.fetchone()
            if not row:
                return None
            return {
                "type": "Feature",
                "properties": {
                    "id": row[0],
                    "level": row[1],
                    "kode_bps": row[2],
                    "nama": row[3],
                },
                "geometry": row[4],
            }

    def all_regions_geojson(
        self, level: str = "kabupaten", limit: Optional[int] = None
    ) -> dict:
        """Ambil semua wilayah sebagai FeatureCollection.

        Gunakan level yang lebih kecil untuk performa:
        - provinsi (~38) → cepat
        - kabupaten (~514) → cepat
        - kecamatan (~7285) → sedang
        - kelurahan (~82983) → LAMBAT, gunakan dengan hati-hati
        """
        sql = """
            SELECT id, level, kode_bps, nama, ST_AsGeoJSON(geom)::json
            FROM regions WHERE level = :level
            ORDER BY kode_bps
        """
        params = {"level": level}
        if limit:
            sql += " LIMIT :limit"
            params["limit"] = limit

        with public_engine.connect() as conn:
            result = conn.execute(text(sql), params)
            features = []
            for row in result:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "id": row[0],
                        "level": row[1],
                        "kode_bps": row[2],
                        "nama": row[3],
                    },
                    "geometry": row[4],
                })
            return {"type": "FeatureCollection", "features": features}

    # ---------------------------------------------------------
    # CHILDREN / HIERARCHY
    # ---------------------------------------------------------
    def get_children(self, parent_kode: str) -> list[dict]:
        """Ambil wilayah anak langsung dari parent_kode.

        Contoh:
            get_children('11') → semua kabupaten di Aceh
            get_children('11.01') → semua kecamatan di Kab. Aceh Selatan
        """
        # Anak langsung: kode diawali parent_kode + '.'
        with public_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, level, kode_bps, nama
                    FROM regions
                    WHERE kode_bps LIKE :pattern
                    AND kode_bps NOT LIKE :pattern_deep
                    ORDER BY kode_bps
                """),
                {
                    "pattern": f"{parent_kode}.%",
                    "pattern_deep": f"{parent_kode}.%.%",
                },
            )
            return [
                {"id": r[0], "level": r[1], "kode_bps": r[2], "nama": r[3]}
                for r in result
            ]

    # ---------------------------------------------------------
    # STATISTIK GEOMETRI
    # ---------------------------------------------------------
    def area_statistics(self, level: str = "provinsi") -> list[dict]:
        """Hitung luas wilayah (dalam km²) per level.

        Menggunakan proyeksi UTM agar luas akurat.
        """
        with public_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT kode_bps, nama,
                        ST_Area(geom::geography) / 1000000 AS area_km2
                    FROM regions
                    WHERE level = :level
                    ORDER BY area_km2 DESC
                """),
                {"level": level},
            )
            return [
                {"kode_bps": r[0], "nama": r[1], "area_km2": round(r[2], 2)}
                for r in result
            ]

        # ---------------------------------------------------------
    # FISCAL-AWARE GEOJSON
    # ---------------------------------------------------------
    def regions_geojson_with_fiscal(
        self, level: str = "kabupaten", year: int = 2024, limit: Optional[int] = None
    ) -> dict:
        """Ambil wilayah + data anggaran sebagai GeoJSON FeatureCollection.

        Setiap fitur punya properti fiscal:
        - pagu
        - realisasi (total Q1+Q2+Q3+Q4)
        - realisasi_pct
        - kategori (baik/sedang/rendah)
        """
        sql = """
            SELECT
                r.id, r.level, r.kode_bps, r.nama,
                ST_AsGeoJSON(r.geom)::json AS geom_json,
                COALESCE(SUM(b.pagu), 0) AS pagu,
                COALESCE(SUM(b.realisasi_q1 + b.realisasi_q2 + b.realisasi_q3 + b.realisasi_q4), 0) AS realisasi,
                COALESCE(SUM(b.realisasi_q1), 0) AS q1,
                COALESCE(SUM(b.realisasi_q2), 0) AS q2,
                COALESCE(SUM(b.realisasi_q3), 0) AS q3,
                COALESCE(SUM(b.realisasi_q4), 0) AS q4
            FROM regions r
            LEFT JOIN budgets b
                ON b.region_id = r.id
                AND b.year = :year
            WHERE r.level = :level
            GROUP BY r.id, r.level, r.kode_bps, r.nama, r.geom
            ORDER BY r.kode_bps
        """
        params = {"level": level, "year": year}
        if limit:
            sql += " LIMIT :limit"
            params["limit"] = limit

        with public_engine.connect() as conn:
            result = conn.execute(text(sql), params)

            features = []
            for row in result:
                pagu = float(row[5] or 0)
                realisasi = float(row[6] or 0)
                realisasi_pct = (realisasi / pagu * 100) if pagu > 0 else 0

                # Kategori
                if pagu == 0:
                    kategori = "belum_ada_data"
                elif realisasi_pct >= 80:
                    kategori = "baik"
                elif realisasi_pct >= 60:
                    kategori = "sedang"
                else:
                    kategori = "rendah"

                features.append({
                    "type": "Feature",
                    "properties": {
                        "id": row[0],
                        "level": row[1],
                        "kode_bps": row[2],
                        "nama": row[3],
                        "pagu": pagu,
                        "realisasi": realisasi,
                        "realisasi_pct": round(realisasi_pct, 2),
                        "kategori": kategori,
                        "q1": float(row[7] or 0),
                        "q2": float(row[8] or 0),
                        "q3": float(row[9] or 0),
                        "q4": float(row[10] or 0),
                    },
                    "geometry": row[4],
                })

            return {"type": "FeatureCollection", "features": features}

    def region_detail_with_fiscal(
        self, region_id: int, year: int = 2024
    ) -> Optional[dict]:
        """Detail wilayah + data fiscal lengkap + TKD."""
        with public_engine.connect() as conn:
            # Region + budget
            row = conn.execute(
                text("""
                    SELECT r.id, r.level, r.kode_bps, r.nama,
                           COALESCE(SUM(b.pagu), 0) AS pagu,
                           COALESCE(SUM(b.realisasi_q1), 0) AS q1,
                           COALESCE(SUM(b.realisasi_q2), 0) AS q2,
                           COALESCE(SUM(b.realisasi_q3), 0) AS q3,
                           COALESCE(SUM(b.realisasi_q4), 0) AS q4
                    FROM regions r
                    LEFT JOIN budgets b ON b.region_id = r.id AND b.year = :year
                    WHERE r.id = :id
                    GROUP BY r.id, r.level, r.kode_bps, r.nama
                """),
                {"id": region_id, "year": year},
            ).fetchone()

            if not row:
                return None

            pagu = float(row[4])
            q1, q2, q3, q4 = float(row[5]), float(row[6]), float(row[7]), float(row[8])
            realisasi = q1 + q2 + q3 + q4
            realisasi_pct = (realisasi / pagu * 100) if pagu > 0 else 0

            # TKD breakdown
            transfers = conn.execute(
                text("""
                    SELECT type, pagu,
                           (realisasi_q1 + realisasi_q2 + realisasi_q3 + realisasi_q4) AS realisasi
                    FROM transfers
                    WHERE region_id = :id AND year = :year
                    ORDER BY pagu DESC
                """),
                {"id": region_id, "year": year},
            ).fetchall()

            tkd = [
                {
                    "type": t[0],
                    "pagu": float(t[1]),
                    "realisasi": float(t[2]),
                    "pct": round(float(t[2]) / float(t[1]) * 100, 2) if float(t[1]) > 0 else 0,
                }
                for t in transfers
            ]

            return {
                "id": row[0],
                "level": row[1],
                "kode_bps": row[2],
                "nama": row[3],
                "year": year,
                "fiscal": {
                    "pagu": pagu,
                    "realisasi": realisasi,
                    "realisasi_pct": round(realisasi_pct, 2),
                    "q1": q1, "q2": q2, "q3": q3, "q4": q4,
                },
                "tkd": tkd,
            }


# Singleton
spatial = SpatialEngine()