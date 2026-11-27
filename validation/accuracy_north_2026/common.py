"""Shared settings for the northern accuracy assessment.

Every script takes the frozen crop layer folder with --crops. The map that is assessed is the publish of
27 Nov 2026 (index.json generated_utc "2026-11-27 07:17", 213 tiles); it is NOT the crops/2026 folder in
this repository at the time of writing. A fixed copy (crops_2026_20261127_0717.zip, SHA-256 in README.md
section 1 and every file's SHA-256 in data/assessed_map_sha256.txt) is to be attached to a GitHub release.
Unzip it and pass its 2026 folder: --crops crops_2026_20261127_0717/2026
The scripts refuse any other map unless --any-map is given.
"""
import argparse, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

SEED = 20261127
NORTH_MIN_LAT = 34.8            # tile centre (middle of its bounding box) at or north of this
NAMES = ["confident_cereal", "doubtful_cereal", "other_crop", "no_crop", "not_cropland"]
N = [100, 100, 60, 60, 250]     # sample size per stratum (570)
ID_PREFIX = "N"
FROZEN = {"generated_utc": "2026-11-27 07:17", "tiles": 213, "cells": 112}


def args(extra=None):
    p = argparse.ArgumentParser()
    p.add_argument("--crops", required=True, help="frozen crop layer folder (holds index.json)")
    p.add_argument("--out", default=DATA, help="folder for outputs")
    p.add_argument("--any-map", action="store_true", help="allow a map other than the frozen 27 Nov publish")
    if extra:
        extra(p)
    a = p.parse_args()
    a.crops = a.crops.rstrip("/") + "/"
    os.makedirs(a.out, exist_ok=True)
    return a


def load_index(a):
    idx = json.load(open(a.crops + "index.json"))
    got = {"generated_utc": idx.get("generated_utc"), "tiles": len(idx["processed"]), "cells": len(idx["cells"])}
    if got != FROZEN and not a.any_map:
        raise SystemExit(f"This is not the assessed map: {got}, expected {FROZEN}. Pass --any-map to use it anyway.")
    return idx


def stratum_fn(idx):
    """Pixel code -> stratum number (0..4, see NAMES). Same as the southern assessment.
    Codes: 0 = not cropland; 1 + class index = confident; +100 = less sure; +200 = doubtful cereal."""
    cl = idx["codes"]["classes"]
    CER = {cl.index(c) + 1 for c in ("wheat", "barley", "rye", "oats")}
    NOCROP = cl.index("no_crop") + 1

    def stratum(a):
        base = np.where(a == 0, 0, ((a.astype(np.int16) - 1) % 100) + 1)
        s = np.full(a.shape, 4, np.uint8)                                    # not cropland (code 0)
        s[(base > 0) & ~np.isin(base, list(CER)) & (base != NOCROP)] = 2     # other crop
        s[base == NOCROP] = 3                                                # no crop
        s[np.isin(base, list(CER)) & (a < 200)] = 0                          # confident cereal
        s[np.isin(base, list(CER)) & (a > 200)] = 1                          # doubtful cereal
        return s
    return stratum


def population(idx, crops):
    """Northern tiles (any run: in this publish they come from the north run and the season pilot)
    inside Iraq's boundary, in EPSG:3857. Returns (shape, number of tiles, tiles by run)."""
    import pyproj
    from collections import Counter
    from shapely.geometry import shape, Polygon
    from shapely.ops import unary_union, transform
    to3857 = pyproj.Transformer.from_crs(4326, 3857, always_xy=True).transform
    north, runs = [], Counter()
    for p in idx["processed"]:
        ys = [y for x, y in p["ring"]]
        if (min(ys) + max(ys)) / 2 >= NORTH_MIN_LAT:
            north.append(transform(to3857, Polygon(p["ring"]))); runs[p["run"]] += 1
    iraq = transform(to3857, unary_union([shape(f["geometry"]) for f in
                     json.load(open(crops + "boundaries.geojson"))["features"]]).buffer(0))
    return unary_union(north).intersection(iraq), len(north), dict(runs)
