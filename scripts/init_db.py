"""Inisialisasi database ATW."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.config import DATA_DIR
from core.db import init_all


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "geo" / "boundaries").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "geo" / "projects").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    init_all()
    print(f"📁 Data dir: {DATA_DIR}")