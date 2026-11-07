"""Compare NDVI from Planetary Computer (with and without the +1000 offset removed) against a
Copernicus Browser "Statistical Info" CSV export for the same field.

  python compare_copernicus.py --summary comparison_field_PP1CC5.csv      # offline: summarise a saved table
  python compare_copernicus.py --outline field_PP1CC5_outline.geojson \\
         --copernicus copernicus_export_field_PP1CC5.csv --out my_comparison.csv   # re-fetch (internet)

Planetary Computer values are field medians from its titiler /item/statistics endpoint over the
outline, one Sentinel-2 L2A scene per date (tile 38SMA where a date has two).
Copernicus rows with cloudCoveragePercent > 0 are skipped."""
import argparse, csv, json, statistics as st, sys

RAW = "(B08-B04)/(B08+B04)"
COR = "(B08-B04)/(B08+B04-2000)"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
PC = "https://planetarycomputer.microsoft.com/api/data/v1"


def summarise(rows):
    cb = [float(r["copernicus_median"]) for r in rows]
    for col, name in (("pc_uncorrected_median", "uncorrected"), ("pc_corrected_median", "offset removed")):
        d = [abs(float(r[col]) - c) for r, c in zip(rows, cb)]
        g = [abs(float(r[col]) - c) for r, c in zip(rows, cb) if c >= 0.5]
        print(f"{name:<15} median gap {st.median(d):.3f}  max {max(d):.3f}  |  green dates (n={len(g)}) median gap {st.median(g):.3f}")
    closer = sum(abs(float(r["pc_corrected_median"]) - c) < abs(float(r["pc_uncorrected_median"]) - c) for r, c in zip(rows, cb))
    print(f"offset-removed formula is closer to Copernicus on {closer} of {len(rows)} dates")


def fetch(outline, cop, out):
    import requests
    geom = json.load(open(outline))
    geom = geom.get("geometry", geom)
    cb = {r["C0/date"][:10]: float(r["C0/median"]) for r in csv.DictReader(open(cop))
          if float(r["C0/cloudCoveragePercent"]) == 0 and float(r["C0/mean"]) != 0}
    lo, hi = min(cb), max(cb)
    lon = sum(x for x, y in geom["coordinates"][0][0]) / len(geom["coordinates"][0][0])
    lat = sum(y for x, y in geom["coordinates"][0][0]) / len(geom["coordinates"][0][0])
    feats, params, url = [], {"collections": "sentinel-2-l2a", "limit": "250",
                              "intersects": json.dumps({"type": "Point", "coordinates": [lon, lat]}),
                              "datetime": f"{lo}T00:00:00Z/{hi}T23:59:59Z"}, STAC
    while url:
        j = requests.get(url, params=params, timeout=60).json(); feats += j["features"]
        nx = next((l for l in j.get("links", []) if l.get("rel") == "next" and l.get("method", "GET") == "GET"), None)
        url, params = (nx["href"], None) if nx else (None, None)
    by = {}
    for f in feats:
        d = f["properties"]["datetime"][:10]
        if d not in by or "T38SMA" in f["id"]: by[d] = f
    rows = []
    for d in sorted(cb, reverse=True):
        if d not in by: continue
        it = by[d]; v = {}
        for k, e in (("pc_uncorrected_median", RAW), ("pc_corrected_median", COR)):
            r = requests.post(f"{PC}/item/statistics", params={"collection": "sentinel-2-l2a", "item": it["id"],
                              "expression": e, "asset_as_band": "true"},
                              json={"type": "Feature", "properties": {}, "geometry": geom}, timeout=60).json()
            stats = r.get("properties", r.get("features", [{}])[0].get("properties", {}))["statistics"]
            v[k] = round(list(stats.values())[0]["median"], 3)
        rows.append({"date": d, "satellite": it["id"][:3], "copernicus_median": round(cb[d], 3), **v})
        print(d, rows[-1], flush=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary"); ap.add_argument("--outline"); ap.add_argument("--copernicus")
    ap.add_argument("--out", default="my_comparison.csv")
    a = ap.parse_args()
    if a.summary:
        summarise(list(csv.DictReader(open(a.summary))))
    elif a.outline and a.copernicus:
        summarise([{k: str(v) for k, v in r.items()} for r in fetch(a.outline, a.copernicus, a.out)])
    else:
        ap.print_help(); sys.exit(1)
