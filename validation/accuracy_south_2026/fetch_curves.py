"""Step 3. Reference curves: each sample point's own Sentinel-2 L2A history, Sep 2025 - Aug 2026.

Blind: reads only data/points.csv (id, lat, lon), never data/map_key.csv.
Source: Microsoft Planetary Computer (STAC search + titiler point reads). No account needed.

For each point and month:
  - candidate scenes = the month's Sentinel-2 L2A items over the point, clearest first (eo:cloud_cover);
  - try up to 4; read B04, B08 and SCL at the point (one 10 m pixel; SCL is 20 m);
  - accept the first whose SCL is 4 vegetation, 5 bare soil, 6 water or 7 unclassified, with B04, B08 > 0;
  - NDVI raw       = (B08 - B04) / (B08 + B04)
    NDVI corrected = (B08 - B04) / (B08 + B04 - 2*1000) on processing baseline >= 04.00, which adds
                     +1000 to every band that Planetary Computer does not remove (see validation/ndvi_offset).
The labelling rules use the corrected value.

This is a line-by-line port of the browser function that produced the published curves
(it ran in Iraq Farms Health's page on 7 Nov 2026). Planetary Computer can reprocess scenes,
so a re-fetch may differ slightly; compare_curves.py measures the difference.

Usage: python fetch_curves.py [--points data/points.csv] [--out data/curves_fetched.json] [--workers 3]
Re-running resumes: points already in the output file are skipped.
"""
import argparse, csv, json, os, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
import requests

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
PC = "https://planetarycomputer.microsoft.com/api/data/v1"
MONTHS = [f"2025-{m:02d}" for m in range(9, 13)] + [f"2026-{m:02d}" for m in range(1, 9)]
CLEAR_SCL = (4, 5, 6, 7)
S = requests.Session()
S.headers["User-Agent"] = "iraq-farms-health-validation"


def get(url, params=None, tries=4):
    wait = 0.5
    for t in range(tries):
        try:
            r = S.get(url, params=params, timeout=40)
            if r.status_code == 200:
                return r
            if r.status_code not in (429, 500, 502, 503, 504):
                return r
        except requests.RequestException:
            if t == tries - 1:
                raise
        time.sleep(wait); wait *= 2
    return r


def label_point(pid, lon, lat):
    feats = []
    params = {"collections": "sentinel-2-l2a",
              "intersects": json.dumps({"type": "Point", "coordinates": [lon, lat]}),
              "datetime": "2025-09-01T00:00:00Z/2026-08-31T23:59:59Z", "limit": "250"}
    url = STAC
    for page in range(4):
        r = get(url, params); r.raise_for_status(); j = r.json()
        feats += j.get("features", [])
        nx = next((l for l in j.get("links", []) if l.get("rel") == "next"), None)
        if not nx or nx.get("method") == "POST":
            break
        url, params = nx["href"], None
    by_month = {}
    for f in feats:
        by_month.setdefault(f["properties"]["datetime"][:7], []).append(f)
    out = {"id": pid, "lon": lon, "lat": lat, "scenes": len(feats), "months": {}}
    for m in MONTHS:
        cand = sorted(by_month.get(m, []), key=lambda f: f["properties"].get("eo:cloud_cover", 100)
                      if f["properties"].get("eo:cloud_cover") is not None else 100)[:4]
        got, tried = None, 0
        for it in cand:
            tried += 1
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
                pb = float(it["properties"].get("s2:processing_baseline") or 0)
                off = 1000 if pb >= 4 else 0
                got = {"d": it["properties"]["datetime"][:10], "scene": it["id"], "baseline": pb,
                       "raw": round((b8 - b4) / (b8 + b4), 3),
                       "cor": round((b8 - b4) / (b8 + b4 - 2 * off), 3),
                       "scl": scl, "b4": b4, "b8": b8, "cloud": it["properties"].get("eo:cloud_cover")}
                break
        out["months"][m] = got or {"none": True, "tried": tried}
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default=os.path.join(here, "data", "points.csv"))
    ap.add_argument("--out", default=os.path.join(here, "data", "curves_fetched.json"))
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", help="comma-separated ids, e.g. S001,S002 (for a quick test)")
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
            rec = label_point(*p)
        except Exception as e:
            rec = {"id": p[0], "err": str(e)[:200]}
        with lock:
            done[p[0]] = rec
            json.dump(done, open(a.out, "w"))
            n = sum(1 for m in rec.get("months", {}).values() if "cor" in m)
            print(f"{p[0]}: {n}/12 months" if "err" not in rec else f"{p[0]}: ERROR {rec['err']}", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
    json.dump(dict(sorted(done.items())), open(a.out, "w"), indent=0)
    print("written", a.out)
