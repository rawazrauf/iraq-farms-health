"""Phase 2 (declared 8 Nov 2026, README section 7). Top-up of the "not cropland" stratum: 200 more points.

Same population and the same two-step draw as draw_sample.py, restricted to one stratum, with its own seed:
  1) points are shared out among the map cells by a multinomial draw weighted by the stratum's area in each cell;
  2) within a cell, they go on uniform random pixels of the stratum (inside the southern tiles and Iraq).
Pixels already sampled in phase 1 are left out. Points are shuffled and numbered T001-T200.

Writes data/topup_points.csv (id, lat, lon: nothing else, for blind labelling), data/topup_map_key.csv
(id -> stratum, code, cell) and data/topup_design.json.
Usage: python topup_draw.py [--crops crops/2026/]"""
import csv, json, numpy as np, rasterio, warnings; warnings.filterwarnings("ignore")
from rasterio.features import rasterize
from shapely.geometry import mapping, box
import pyproj
from common import args, load_index, stratum_fn, population, NAMES

SEED2 = 20261108
STRATUM = "not_cropland"
N2 = 200

a = args()
idx = load_index(a.crops); stratum = stratum_fn(idx)
k = NAMES.index(STRATUM)
rng = np.random.default_rng(SEED2)
S = json.load(open(a.out + "/strata_area.json"))
to4326 = pyproj.Transformer.from_crs(3857, 4326, always_xy=True).transform
pop, _ = population(idx, a.crops)
# phase-1 points of this stratum, as (cell, lon, lat) rounded as written, to leave those pixels out
pts1 = {r["id"]: r for r in csv.DictReader(open(a.out + "/points.csv"))}
used = {(r["cell"], pts1[r["id"]]["lon"], pts1[r["id"]]["lat"])
        for r in csv.DictReader(open(a.out + "/map_key.csv")) if r["stratum"] == STRATUM}

cells = list(S["cells"])
w = np.array([S["cells"][c][k] for c in cells]); w = w / w.sum()
want = {c: n for c, n in zip(cells, rng.multinomial(N2, w)) if n}
pts, skipped = [], 0
for c in cells:
    if c not in want: continue
    with rasterio.open(a.crops + c) as ds:
        part = pop.intersection(box(*ds.bounds))
        m = rasterize([(mapping(part), 1)], out_shape=(ds.height, ds.width), transform=ds.transform,
                      fill=0, dtype="uint8").astype(bool)
        arr = ds.read(1)
        r, col = np.nonzero(m & (stratum(arr) == k))
        got = 0
        for i in rng.choice(len(r), min(len(r), want[c] + 10), replace=False):   # spares for skipped pixels
            x, y = ds.transform * (col[i] + 0.5, r[i] + 0.5)
            lon, lat = to4326(x, y)
            if (c, f"{lon:.6f}", f"{lat:.6f}") in used:
                skipped += 1; continue
            pts.append({"lon": round(lon, 6), "lat": round(lat, 6), "stratum": STRATUM,
                        "code": int(arr[r[i], col[i]]), "cell": c})
            got += 1
            if got == want[c]: break
pts = [pts[i] for i in rng.permutation(len(pts))]
for i, p in enumerate(pts): p["id"] = f"T{i+1:03d}"
with open(a.out + "/topup_points.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["id", "lat", "lon"])
    for p in pts: wr.writerow([p["id"], f'{p["lat"]:.6f}', f'{p["lon"]:.6f}'])
with open(a.out + "/topup_map_key.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["id", "stratum", "code", "cell"])
    for p in pts: wr.writerow([p["id"], p["stratum"], p["code"], p["cell"]])
json.dump({"seed": SEED2, "stratum": STRATUM, "n": N2, "phase1_pixels_skipped": skipped,
           "cells": {c: int(n) for c, n in want.items()}}, open(a.out + "/topup_design.json", "w"), indent=1)
print(len(pts), "points;", len(want), "cells;", skipped, "phase-1 pixels skipped")
