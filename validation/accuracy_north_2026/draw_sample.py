"""Step 2. Stratified random sample (seed 20261127), the same two-step draw as the southern assessment.
Writes points.csv (id, lat, lon: no map class, for blind labelling) and map_key.csv (id -> stratum),
design.json (sample sizes, stratum areas, map identity) and spotcheck_ids.csv (the second labeller's subset)."""
import csv, json, warnings, numpy as np, rasterio
from collections import Counter
from rasterio.features import rasterize
from shapely.geometry import mapping, box
import pyproj
from common import args, load_index, stratum_fn, population, NAMES, N, SEED, ID_PREFIX
warnings.filterwarnings("ignore", category=DeprecationWarning)

SPOT_SEED, SPOT_N = 20261128, 57      # random 10% of the points for an independent second labeller

a = args()
idx = load_index(a); stratum = stratum_fn(idx)
rng = np.random.default_rng(SEED)
S = json.load(open(a.out + "/strata_area.json"))
to4326 = pyproj.Transformer.from_crs(3857, 4326, always_xy=True).transform
pop, _, _ = population(idx, a.crops)
cells = list(S["cells"])
# 1) how many points each map cell gets, per stratum: multinomial on the stratum's area in the cell
want = {}
for k in range(5):
    w = np.array([S["cells"][c][k] for c in cells]); w = w / w.sum()
    for c, n in zip(cells, rng.multinomial(N[k], w)):
        if n: want[(c, k)] = n
# 2) uniform pixels of that stratum within the cell
pts = []
for c in cells:
    ks = [k for k in range(5) if (c, k) in want]
    if not ks: continue
    with rasterio.open(a.crops + c) as ds:
        part = pop.intersection(box(*ds.bounds))
        m = rasterize([(mapping(part), 1)], out_shape=(ds.height, ds.width), transform=ds.transform,
                      fill=0, dtype="uint8").astype(bool)
        arr = ds.read(1); s = stratum(arr)
        for k in ks:
            r, col = np.nonzero(m & (s == k))
            for i in rng.choice(len(r), want[(c, k)], replace=False):
                x, y = ds.transform * (col[i] + 0.5, r[i] + 0.5)
                lon, lat = to4326(x, y)
                pts.append({"lon": round(lon, 6), "lat": round(lat, 6), "stratum": NAMES[k],
                            "code": int(arr[r[i], col[i]]), "cell": c})
# 3) shuffle, so the point order says nothing about the class
pts = [pts[i] for i in rng.permutation(len(pts))]
for i, p in enumerate(pts): p["id"] = f"{ID_PREFIX}{i+1:03d}"
with open(a.out + "/points.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "lat", "lon"])
    for p in pts: w.writerow([p["id"], f'{p["lat"]:.6f}', f'{p["lon"]:.6f}'])
with open(a.out + "/map_key.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "stratum", "code", "cell"])
    for p in pts: w.writerow([p["id"], p["stratum"], p["code"], p["cell"]])
spot = sorted(np.random.default_rng(SPOT_SEED).choice([p["id"] for p in pts], SPOT_N, replace=False).tolist())
with open(a.out + "/spotcheck_ids.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id"]); w.writerows([[i] for i in spot])
json.dump({"seed": SEED, "n": dict(zip(NAMES, N)), "area_ha": dict(zip(NAMES, S["area_ha"])),
           "tiles": S["tiles"], "tiles_by_run": S["tiles_by_run"],
           "map": {"generated_utc": idx["generated_utc"], "tiles": len(idx["processed"]), "cells": len(idx["cells"])},
           "spotcheck": {"seed": SPOT_SEED, "n": SPOT_N}},
          open(a.out + "/design.json", "w"), indent=1)
print(len(pts), Counter(p["stratum"] for p in pts))
