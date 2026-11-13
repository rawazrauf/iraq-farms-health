"""Forage test, step 2. Every clear Sentinel-2 reading at each sample point, 1 Nov 2025 - 15 Jun 2026.

Reads data/forage_sample.csv (id, lat, lon). Source: Microsoft Planetary Computer, as in fetch_curves.py.
For each point: all Sentinel-2 L2A items over it in the window with scene cloud cover under 90%; B04, B08
and SCL at the point; a reading is kept when SCL is 4 vegetation, 5 bare soil, 6 water or 7 unclassified
and both bands are above zero. NDVI is offset-corrected exactly as in fetch_curves.py (ndvi_cor). Two
readings on the same date (overlapping tiles) are averaged. Output: {id: {lat, lon, scenes, obs: [[date, ndvi], ...]}}.

The archived data/forage_series.json was produced on 13 Nov 2026 by the same steps run in the browser on
iraqfarmshealth.com (values rounded to 0.001). This script is the Python port; it writes to a different
file by default so the archive is not overwritten. Planetary Computer can reprocess scenes, so a re-fetch
may differ slightly.
Usage: python fetch_dense.py [--out data/forage_series_fetched.json] [--workers 3] [--only S010,S024]"""
import argparse, csv, json, os, threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from fetch_curves import STAC, PC, CLEAR_SCL, get, ndvi_cor

WINDOW = "2025-11-01T00:00:00Z/2026-06-15T23:59:59Z"


def dense_point(pid, lon, lat):
    feats, url = [], STAC
    params = {"collections": "sentinel-2-l2a",
              "intersects": json.dumps({"type": "Point", "coordinates": [lon, lat]}),
              "datetime": WINDOW, "limit": "250"}
    for page in range(4):
        r = get(url, params); r.raise_for_status(); j = r.json()
        feats += j.get("features", [])
        nx = next((l for l in j.get("links", []) if l.get("rel") == "next"), None)
        if not nx or nx.get("method") == "POST":
            break
        url, params = nx["href"], None
    cc = lambda f: f["properties"].get("eo:cloud_cover")
    feats = [f for f in feats if cc(f) is None or cc(f) < 90]
    by = defaultdict(list)
    for it in feats:
        try:
            r = get(f"{PC}/item/point/{lon},{lat}",
                    [("collection", "sentinel-2-l2a"), ("item", it["id"]),
                     ("assets", "B04"), ("assets", "B08"), ("assets", "SCL")])
            if r.status_code != 200:
                continue
            b4, b8, scl = r.json()["values"][:3]
        except Exception:
            continue
        if scl in CLEAR_SCL and b4 > 0 and b8 > 0:
            off = 1000 if float(it["properties"].get("s2:processing_baseline") or 0) >= 4 else 0
            by[it["properties"]["datetime"][:10]].append(ndvi_cor(b4, b8, off))
    return {"lat": lat, "lon": lon, "scenes": len(feats),
            "obs": [[d, round(sum(v) / len(v), 3)] for d, v in sorted(by.items())]}


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default=os.path.join(here, "data", "forage_sample.csv"))
    ap.add_argument("--out", default=os.path.join(here, "data", "forage_series_fetched.json"))
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only")
    a = ap.parse_args()
    pts = [(r["id"], float(r["lon"]), float(r["lat"])) for r in csv.DictReader(open(a.points))]
    if a.only:
        keep = set(a.only.split(",")); pts = [p for p in pts if p[0] in keep]
    done = json.load(open(a.out)) if os.path.exists(a.out) else {}
    todo = [p for p in pts if p[0] not in done or "err" in done[p[0]]]
    print(f"{len(pts)} points, {len(todo)} to fetch", flush=True)
    lock = threading.Lock()

    def work(p):
        try:
            rec = dense_point(*p)
        except Exception as e:
            rec = {"err": str(e)[:200]}
        with lock:
            done[p[0]] = rec
            json.dump(done, open(a.out, "w"))
            print(f"{p[0]}: {len(rec.get('obs', []))} clear dates" if "err" not in rec else f"{p[0]}: ERROR {rec['err']}", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
