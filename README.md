<!-- ═══════════════════════════════════════════════════════════════ -->
<!--                        ATW — README                             -->
<!-- ═══════════════════════════════════════════════════════════════ -->

<div align="center">

<img src="https://img.shields.io/badge/status-in%20development-orange?style=for-the-badge" alt="Status">
<img src="https://img.shields.io/badge/version-0.1.0-blue?style=for-the-badge" alt="Version">
<img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License">

<br><br>

# 🌾 ATW
### Anggaran Transparency Watch

**Platform transparansi anggaran publik berbasis spasial untuk Indonesia**

*Memetakan setiap rupiah anggaran hingga ke titik geografisnya.*

<br>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.6-336791?style=flat-square)](https://postgis.net)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9-199900?style=flat-square&logo=leaflet&logoColor=white)](https://leafletjs.com)
[![Jinja2](https://img.shields.io/badge/Jinja2-3.1-B41717?style=flat-square&logo=jinja&logoColor=white)](https://jinja.palletsprojects.com)

<br>

[📖 Dokumentasi](#-tentang) · [🚀 Quick Start](#-quick-start) · [🗺️ Fitur](#-fitur-utama) · [🗺️ Roadmap](#-roadmap) · [🤝 Kontribusi](#-kontribusi)

</div>

---

## 📌 Tentang

**ATW (Anggaran Transparency Watch)** adalah platform open-source untuk memantau, memvisualisasikan, dan mengaudit **aliran anggaran publik** Indonesia — dari pemerintah pusat hingga ke desa/kelurahan — dalam bentuk **peta interaktif**.

Sistem ini mengintegrasikan:

- 🗺️ **90.818 wilayah administratif** Indonesia (provinsi, kabupaten/kota, kecamatan, kelurahan)
- 💰 **Data fiskal** (pagu, realisasi, TKD: DAU/DAK/DBH/Dana Desa)
- 📸 **Dokumentasi foto** dari lapangan dengan GPS tagging
- 🔐 **Role-based access** (publik, kontributor, verifikator, admin)

> ⚠️ **Status:** Proyek ini masih dalam **pengembangan aktif (v0.1.0)**.  
> Data anggaran saat ini menggunakan **data dummy** untuk keperluan demo dan pengembangan.  
> Integrasi dengan data real (DJPK, LPSE, APBD) sedang dalam roadmap.

---

## ✨ Fitur Utama

<table>
<tr>
<td width="50%">

### 🗺️ Peta Anggaran Interaktif
- Choropleth warna berdasarkan realisasi anggaran
- 🟢 Baik (≥80%) · 🟡 Sedang (60–80%) · 🔴 Rendah (<60%)
- Multi-layer: Provinsi → Kabupaten → Kecamatan → Kelurahan
- Search box + quick zoom

</td>
<td width="50%">

### 📊 Detail Fiskal
- Pagu & realisasi per wilayah
- Grafik kuartalan (Q1–Q4)
- Breakdown TKD: DAU, DAK, DBH, Dana Desa
- Perbandingan antar wilayah

</td>
</tr>
<tr>
<td width="50%">

### 📸 Dokumentasi Warga
- Upload foto dari lapangan
- GPS tagging otomatis
- Kategori: sekolah, jalan, jembatan, kesehatan, gambut
- Marker foto di peta

</td>
<td width="50%">

### 🔐 Role-Based Access
- **Publik** — lihat peta & feedback
- **Kontributor** — upload foto (pending)
- **Verifikator** — approve/reject foto
- **Admin** — kelola semua

</td>
</tr>
<tr>
<td width="50%">

### 📬 Feedback Publik
- Form feedback terintegrasi
- Kategori: bug, data, saran, pertanyaan
- Honeypot anti-spam

</td>
<td width="50%">

### 🇮🇩 Data Wilayah Lengkap
- 38 provinsi
- 513 kabupaten/kota
- 7.284 kecamatan
- 82.983 kelurahan/desa

</td>
</tr>
</table>

---

## 🏗️ Arsitektur

```text
┌─────────────────────────────────────────────────────────────┐
│                       ATW PLATFORM                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐    ┌────────────┐   │
│  │   PUBLIC     │      │   INTERNAL   │    │   CLIENT   │   │
│  │  Dashboard   │      │    FVI       │    │   PyQt6    │   │
│  │              │      │              │    │            │   │
│  │ • Peta       │      │ • FVI Score  │    │ • Auditor  │   │
│  │ • Feedback   │      │ • Anomaly    │    │ • Analis   │   │
│  │ • Foto       │      │ • Forecast   │    │ • Override │   │
│  └──────┬───────┘      └──────┬───────┘    └─────┬──────┘   │
│         │                     │                  │          │
│         └─────────────────────┼──────────────────┘          │
│                               │                             │
│                    ┌──────────▼──────────┐                  │
│                    │   FastAPI Backend   │                  │
│                    │  (Public + Internal)│                  │
│                    └──────────┬──────────┘                  │
│                               │                             │
│                    ┌──────────▼──────────┐                  │
│                    │   CORE ENGINES      │                  │
│                    │ • spatial_engine    │                  │
│                    │ • fiscal_engine     │                  │
│                    │ • audit_engine      │                  │
│                    └──────────┬──────────┘                  │
│                               │                             │
│                    ┌──────────▼──────────┐                  │
│                    │  PostgreSQL+PostGIS │                  │
│                    │  atw_public          │                  │
│                    │  atw_internal        │                  │
│                    └─────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Struktur Proyek

```text
atw/
│
├── 📄 README.md                    # Dokumentasi ini
├── 📄 requirements.txt             # Python dependencies
├── 📄 .gitignore                   # Git ignore rules
├── 📄 .env                         # Environment variables (jangan commit!)
│
├── 📁 core/                        # Shared engine (dipakai publik & internal)
│   ├── config.py                   # Konfigurasi global
│   ├── models.py                   # SQLAlchemy models
│   ├── db.py                       # Database session
│   ├── auth.py                     # Auth helper (hash, session, role)
│   └── spatial_engine.py           # Query spasial & fiscal-aware GeoJSON
│
├── 📁 public/                      # ATW — Dashboard Publik
│   ├── api_public.py               # FastAPI app (publik)
│   ├── templates/
│   │   ├── base.html               # Layout dasar
│   │   ├── map.html                # Halaman peta
│   │   ├── feedback.html           # Form feedback
│   │   ├── login.html              # Halaman login
│   │   ├── register.html           # Halaman registrasi
│   │   └── verify.html             # Halaman verifikasi (internal)
│   └── static/
│       ├── css/style.css           # Global styles
│       └── js/
│           ├── map.js              # Logic peta, marker, modal
│           ├── auth.js             # Login/register handler
│           ├── feedback.js         # Feedback form
│           └── verify.js           # Verification UI
│
├── 📁 internal/                    # FVI — Modul Internal (decision support)
│   ├── engine/                     # FVI engine (ARIMA, LSTM, Monte Carlo)
│   ├── client/                     # PyQt6 client untuk auditor
│   └── templates/                  # Dashboard internal
│
├── 📁 data/                        # Data storage
│   ├── geo/                        # GeoJSON wilayah & proyek
│   ├── raw/                        # Data mentah (SQL dump, dll)
│   ├── processed/                  # Data olahan
│   ├── photos/                     # Upload foto user (gitignored)
│   └── atw_public.sqlite           # (opsional, untuk dev)
│
├── 📁 scripts/                     # Utility scripts
│   ├── init_db.py                  # Init tabel PostgreSQL
│   ├── migrate_boundaries.py       # Import 90k wilayah
│   ├── migrate_auth.py             # Migrasi tabel auth
│   ├── migrate_feedback.py         # Migrasi tabel feedback
│   ├── migrate_photos.py           # Migrasi tabel project_photos
│   ├── seed_admin.py               # Seed user default
│   ├── load_fiscal_dummy.py        # Load data anggaran dummy
│   └── test_spatial.py             # Test spatial engine
│
├── 📁 tests/                       # Unit tests
├── 📁 docs/                        # Dokumentasi teknis
└── 📁 environment-*.yml            # Conda environments
```

---

## 🚀 Quick Start

### Prasyarat

- **Python** 3.11+
- **PostgreSQL** 16+ dengan **PostGIS** 3.x
- **Anaconda/Miniconda** (opsional tapi direkomendasikan)
- **OS**: Windows / Linux / macOS

### 1. Clone & Setup Environment

```bash
git clone https://github.com/duhemen/atw.git
cd atw

# Buat environment core
conda env create -f environment-core.yml
conda activate atw-core
```

### 2. Setup PostgreSQL

```bash
# Buat database
psql -U postgres -c "CREATE DATABASE atw_public;"
psql -U postgres -c "CREATE DATABASE atw_internal;"
psql -U postgres -c "CREATE DATABASE atw_staging;"

# Aktifkan PostGIS
psql -U postgres -d atw_public -c "CREATE EXTENSION postgis;"
psql -U postgres -d atw_internal -c "CREATE EXTENSION postgis;"
psql -U postgres -d atw_staging -c "CREATE EXTENSION postgis;"
```

### 3. Konfigurasi `.env`

```ini
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_PUBLIC=atw_public
DB_INTERNAL=atw_internal
SECRET_KEY=generate-random-secret-key
```

### 4. Inisialisasi Database

```bash
# Buat tabel
python scripts/init_db.py
python scripts/migrate_auth.py
python scripts/migrate_feedback.py
python scripts/migrate_photos.py

# Seed user default
python scripts/seed_admin.py

# Import 90.818 wilayah Indonesia
# (butuh data dari cahyadsn/wilayah_boundaries di data/raw/)
python scripts/migrate_boundaries.py --level provinsi
python scripts/migrate_boundaries.py --level kabupaten
python scripts/migrate_boundaries.py --level kecamatan
python scripts/migrate_boundaries.py --level kelurahan

# Load data dummy untuk demo
python scripts/load_fiscal_dummy.py
```

### 5. Jalankan Server

```bash
uvicorn public.api_public:app --host 127.0.0.1 --port 8000 --reload
```

Buka browser: **http://127.0.0.1:8000** 🎉

---

## 👥 Kredensial Default

| Role | Username | Password | Akses |
|---|---|---|---|
| 🔴 **Admin** | `admin` | `admin123` | Full access |
| 🟠 **Verifikator** | `verifikator1` | `verif123` | Approve/reject foto |
| 🟢 **Kontributor** | `kontributor1` | `user123` | Upload foto |
| ⚪ **Publik** | — | — | Lihat peta |

> ⚠️ **Ganti password** setelah login pertama di production!

---

## 📖 Enduser Guide

### 🌐 Untuk Masyarakat Umum (Publik)

1. **Buka peta** → `http://127.0.0.1:8000`
2. **Klik wilayah** di peta untuk melihat detail anggaran
3. **Panel kanan** menampilkan:
   - Pagu & realisasi tahunan
   - Grafik kuartalan Q1–Q4
   - Breakdown Transfer ke Daerah (DAU, DAK, DBH, Dana Desa)
4. **Legend warna**:
   - 🟢 **Hijau** = Realisasi baik (≥80%)
   - 🟡 **Kuning** = Realisasi sedang (60–80%)
   - 🔴 **Merah** = Realisasi rendah (<60%)
   - ⚪ **Abu** = Belum ada data
5. **Lihat foto dokumentasi**: Aktifkan toggle "Tampilkan Marker Foto" di sidebar
6. **Kirim feedback**: Menu **Feedback** di header

### 📸 Untuk Kontributor

1. **Daftar akun** di `/register` atau login
2. **Klik wilayah** di peta
3. **Klik "📷 Tambah Dokumentasi"**
4. **Upload foto** + isi judul, kategori, deskripsi
5. **Klik 📍 GPS** untuk deteksi lokasi otomatis
6. **Submit** → foto masuk ke antrian **verifikasi**
7. Foto akan tampil di peta setelah di-approve verifikator

### ✅ Untuk Verifikator

1. **Login** sebagai verifikator
2. Buka menu **Verifikasi** di header
3. Lihat daftar foto **pending**
4. **Approve** (✅) atau **Reject** (❌) dengan alasan
5. Foto yang di-approve langsung tampil di peta

---

## 🗺️ Roadmap

### ✅ Fase 1 — Fondasi (Selesai)

- [x] PostgreSQL + PostGIS setup
- [x] Import 90.818 wilayah administratif Indonesia
- [x] Choropleth peta anggaran dengan Leaflet
- [x] Panel detail fiskal (pagu, realisasi, TKD, kuartalan)
- [x] Search box & quick zoom
- [x] Feedback form dengan honeypot anti-spam
- [x] Photo documentation dengan GPS tagging
- [x] Role-based access (publik, kontributor, verifikator, admin)
- [x] Verifikasi foto oleh verifikator

### 🚧 Fase 2 — Data Real (In Progress)

- [ ] Integrasi data DJPK (Transfer ke Daerah)
- [ ] Scraping APBD dari Pemda
- [ ] Integrasi LPSE/SIRUP (proyek pengadaan)
- [ ] Data Dana Desa dari Kemendesa
- [ ] Validasi & normalisasi data real

### 🔮 Fase 3 — Analitik Lanjutan

- [ ] **Fiscal Vulnerability Index (FVI)** dengan ARIMA/LSTM/GRU
- [ ] Monte Carlo simulation per klaster regional
- [ ] Panel ahli HITL (akademisi, auditor, praktisi)
- [ ] Deteksi anomali berbasis ML
- [ ] Perbandingan antar wilayah

### 🌟 Fase 4 — Ekosistem

- [ ] Vector tiles untuk kelurahan
- [ ] Mobile app (Flutter/React Native)
- [ ] Public API dengan rate limiting
- [ ] Dashboard multi-tahun
- [ ] Notifikasi perubahan anggaran
- [ ] Mekanisme pelaporan warga (crowdsourcing)

---

## 🛠️ Teknologi

<table>
<tr>
<td align="center" width="96">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="48" height="48" alt="Python"><br>
<b>Python 3.11</b>
</td>
<td align="center" width="96">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" width="48" height="48" alt="FastAPI"><br>
<b>FastAPI</b>
</td>
<td align="center" width="96">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" width="48" height="48" alt="PostgreSQL"><br>
<b>PostgreSQL</b>
</td>
<td align="center" width="96">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg" width="48" height="48" alt="JavaScript"><br>
<b>JavaScript</b>
</td>
<td align="center" width="96">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/html5/html5-original.svg" width="48" height="48" alt="HTML5"><br>
<b>HTML5</b>
</td>
<td align="center" width="96">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/css3/css3-original.svg" width="48" height="48" alt="CSS3"><br>
<b>CSS3</b>
</td>
</tr>
</table>

**Stack lengkap:**
- **Backend:** FastAPI, SQLAlchemy, Pydantic, Uvicorn
- **Database:** PostgreSQL 18 + PostGIS 3.6
- **Frontend:** Jinja2, Leaflet.js, Vanilla JS
- **Data:** GeoPandas, Shapely, PyProj, Fiona
- **Analitik (FVI):** Statsmodels, PyTorch, scikit-learn, PyMC
- **Client (internal):** PyQt6, QWebEngineView

---

## 🤝 Kontribusi

Kami menyambut kontribusi dari siapa pun! Berikut cara berkontribusi:

```bash
# 1. Fork repo ini
# 2. Buat branch fitur
git checkout -b fitur/nama-fitur

# 3. Commit perubahan
git commit -m "feat: menambahkan fitur X"

# 4. Push ke branch
git push origin fitur/nama-fitur

# 5. Buat Pull Request
```

### Konvensi Commit

- `feat:` — fitur baru
- `fix:` — bug fix
- `docs:` — dokumentasi
- `refactor:` — refactoring kode
- `test:` — testing
- `chore:` — task rutin

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **MIT License**.

```
MIT License

Copyright (c) 2024-2026 ATW Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Ucapan Terima Kasih

- **[cahyadsn/wilayah_boundaries](https://github.com/cahyadsn/wilayah_boundaries)** — Data batas wilayah administratif Indonesia
- **[Leaflet.js](https://leafletjs.com)** — Peta interaktif
- **[OpenStreetMap](https://www.openstreetmap.org)** — Base map
- **[FastAPI](https://fastapi.tiangolo.com)** — Web framework modern
- **[PostGIS](https://postgis.net)** — Ekstensi spasial PostgreSQL

---

<div align="center">

**🌾 ATW — Anggaran Transparency Watch**

*Untuk Indonesia yang lebih transparan.*

<br>

[⬆ Kembali ke Atas](#-atw)

<br>

**Made with ❤️ for Indonesia**

<br>

<img src="https://img.shields.io/badge/🇮🇩-Indonesia-red?style=for-the-badge" alt="Indonesia">

</div>

---