"""Load data anggaran dummy untuk pilot ATW.

Men-generate data dummy yang realistis untuk 20 kabupaten pilot:
- Pagu, realisasi Q1-Q4
- Komponen TKD (DAU, DAK, Dana Desa, DBH)
- Belanja (pegawai, barang/jasa, modal)
- Project (sekolah, jalan, jembatan)
"""
import sys
import random
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from loguru import logger
from sqlalchemy import text
from core.db import public_engine


# 20 kabupaten pilot (Kalteng + sekitarnya)
PILOT_KABUPATEN = [
    "62.01", "62.02", "62.03", "62.04", "62.05",  # Kalteng
    "62.06", "62.07", "62.08", "62.09", "62.10",
    "62.11", "62.12", "62.13", "62.71",
    "63.01", "63.02", "63.03",  # Kalsel
    "64.01", "64.02", "64.03",  # Kaltim
]

# Konfigurasi dummy per level kesulitan
LEVEL_CONFIG = {
    "baik":      {"pagu": (80_000_000_000, 150_000_000_000), "realisasi_pct": (0.85, 0.95)},
    "sedang":    {"pagu": (50_000_000_000, 100_000_000_000), "realisasi_pct": (0.65, 0.80)},
    "rendah":    {"pagu": (30_000_000_000, 80_000_000_000),  "realisasi_pct": (0.40, 0.60)},
}


def get_region_ids_by_kode(kode_list):
    """Ambil region_id dari kode_bps."""
    with public_engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, kode_bps, nama FROM regions WHERE kode_bps = ANY(:kodes) AND level = 'kabupaten'"),
            {"kodes": kode_list},
        )
        return [{"id": r[0], "kode": r[1], "nama": r[2]} for r in result]


def insert_budget(region_id, year, level_cfg):
    """Insert satu row anggaran."""
    pagu = random.randint(*level_cfg["pagu"])
    pct = random.uniform(*level_cfg["realisasi_pct"])

    # Bagi realisasi ke 4 kuartal dengan pola umum:
    # Q1 kecil, Q2 naik, Q3 naik, Q4 paling besar
    q_weights = [0.15, 0.25, 0.30, 0.30]
    total_real = pagu * pct

    q1 = total_real * q_weights[0]
    q2 = total_real * q_weights[1]
    q3 = total_real * q_weights[2]
    q4 = total_real * q_weights[3]

    with public_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO budgets
                (region_id, year, source_fund, program, activity, category,
                 pagu, realisasi_q1, realisasi_q2, realisasi_q3, realisasi_q4)
                VALUES
                (:region_id, :year, 'APBD', :program, 'Belanja Daerah', 'modal',
                 :pagu, :q1, :q2, :q3, :q4)
            """),
            {
                "region_id": region_id, "year": year,
                "program": "Program Pembangunan Daerah",
                "pagu": pagu,
                "q1": q1, "q2": q2, "q3": q3, "q4": q4,
            },
        )
    return {"pagu": pagu, "realisasi": total_real, "pct": pct}


def insert_transfers(region_id, year):
    """Insert komponen TKD dummy."""
    komponen = {
        "DAU": random.randint(200_000_000_000, 500_000_000_000),
        "DAK_FISIK": random.randint(30_000_000_000, 100_000_000_000),
        "DAK_NONFISIK": random.randint(20_000_000_000, 80_000_000_000),
        "DBH_PAJAK": random.randint(10_000_000_000, 50_000_000_000),
        "DBH_SDA": random.randint(5_000_000_000, 40_000_000_000),
        "DANA_DESA": random.randint(5_000_000_000, 20_000_000_000),
    }

    with public_engine.begin() as conn:
        for tipe, pagu in komponen.items():
            # Realisasi 70-95%
            pct = random.uniform(0.70, 0.95)
            total = pagu * pct
            # Pola pencairan TKD: Q1 rendah, Q2-Q4 merata
            q_weights = [0.15, 0.25, 0.30, 0.30]
            conn.execute(
                text("""
                    INSERT INTO transfers
                    (region_id, year, type, pagu, realisasi_q1, realisasi_q2, realisasi_q3, realisasi_q4)
                    VALUES
                    (:rid, :year, :tipe, :pagu, :q1, :q2, :q3, :q4)
                """),
                {
                    "rid": region_id, "year": year, "tipe": tipe, "pagu": pagu,
                    "q1": total * q_weights[0],
                    "q2": total * q_weights[1],
                    "q3": total * q_weights[2],
                    "q4": total * q_weights[3],
                },
            )


def main():
    year = 2024

    logger.info(f"🎯 Loading dummy fiscal data for year {year}")

    # Get region IDs
    regions = get_region_ids_by_kode(PILOT_KABUPATEN)
    logger.info(f"📍 Found {len(regions)} kabupaten pilot")

    if not regions:
        logger.error("❌ Tidak ada kabupaten pilot ditemukan. Cek kode BPS.")
        return

    # Clear existing (optional)
    with public_engine.begin() as conn:
        conn.execute(text("DELETE FROM budgets WHERE year = :year"), {"year": year})
        conn.execute(text("DELETE FROM transfers WHERE year = :year"), {"year": year})

    # Assign level kesulitan random
    for r in regions:
        level_name = random.choice(["baik", "sedang", "rendah"])
        level_cfg = LEVEL_CONFIG[level_name]

        budget = insert_budget(r["id"], year, level_cfg)
        insert_transfers(r["id"], year)

        logger.info(
            f"   ✓ {r['kode']:8s} {r['nama']:35s} "
            f"[{level_name:6s}] pagu={budget['pagu']/1e9:>6.1f}M "
            f"real={budget['pct']*100:>5.1f}%"
        )

    logger.info(f"🎉 Dummy fiscal data loaded for {len(regions)} regions")


if __name__ == "__main__":
    main()