"""Test spatial engine."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.spatial_engine import spatial


def main():
    print("\n📊 1. Jumlah wilayah per level:")
    counts = spatial.count_by_level()
    for level, count in counts.items():
        print(f"   {level:12s}: {count:>7,}")
    print(f"   {'TOTAL':12s}: {sum(counts.values()):>7,}")

    print("\n🔍 2. Test point-in-region:")
    tests = [
        ("Palangka Raya", -2.2, 113.9),
        ("Jakarta Pusat", -6.2, 106.85),
        ("Surabaya", -7.25, 112.75),
        ("Jayapura", -2.5, 140.7),
    ]
    for label, lat, lon in tests:
        print(f"\n   📍 {label} ({lat}, {lon}):")
        results = spatial.point_in_region(lat, lon)
        for r in results:
            print(f"      [{r['level']:10s}] {r['nama']}")

    print("\n🌳 3. Test hierarchy (Aceh):")
    kabupaten = spatial.get_children("11")
    print(f"   Kabupaten di Aceh: {len(kabupaten)}")
    for kab in kabupaten[:5]:
        print(f"      {kab['kode_bps']}: {kab['nama']}")

    print("\n📐 4. Test GeoJSON (single region):")
    results = spatial.point_in_region(-2.2, 113.9, level="provinsi")
    if results:
        gj = spatial.region_geojson(results[0]["id"])
        print(f"   {gj['properties']['nama']}: {gj['geometry']['type']}")

    print("\n🗺️ 5. Test FeatureCollection (provinsi):")
    fc = spatial.all_regions_geojson("provinsi")
    print(f"   {len(fc['features'])} fitur provinsi")

    print("\n📏 6. Test area statistics (5 provinsi terluas):")
    stats = spatial.area_statistics("provinsi")
    for s in stats[:5]:
        print(f"   {s['nama']:25s}: {s['area_km2']:>10,.2f} km²")


if __name__ == "__main__":
    main()