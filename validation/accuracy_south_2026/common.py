"""Shared settings for the southern accuracy assessment.

Every script takes the crop layer folder with --crops (default: crops/2026 in this repo).
To reproduce the published figures exactly, use the map that was assessed (commit 969b4aa,
7 Nov 2026), attached to the release crops-2026-assessed:
    https://github.com/rawazrauf/iraq-farms-health/releases/download/crops-2026-assessed/crops-2026-assessed.zip
Unzip it and pass the folder: --crops crops-2026-assessed
"""
import argparse, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DEFAULT_CROPS = os.path.normpath(os.path.join(HERE, "..", "..", "crops", "2026"))

SEED = 20261107
MAIN_RUN = "iraq_winter2026"
SOUTH_MAX_LAT = 34.8            # tile centre (middle of its bounding box) south of this
NAMES = ["confident_cereal", "doubtful_cereal", "other_crop", "no_crop", "not_cropland"]
N = [100, 75, 50, 50, 100]      # sample size per stratum


def args(extra=None):
    p = argparse.ArgumentParser()
    p.add_argument("--crops", default=DEFAULT_CROPS, help="crop layer folder (holds index.json)")
    p.add_argument("--out", default=DATA, help="folder for outputs")
    if extra:
        extra(p)
    a = p.parse_args()
    a.crops = a.crops.rstrip("/") + "/"
    os.makedirs(a.out, exist_ok=True)
    return a


def load_index(crops):
    return json.load(open(crops + "index.json"))


def stratum_fn(idx):
    """Pixel code -> stratum number (0..4, see NAMES).
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
    """Southern main-run tiles inside Iraq's boundary, in EPSG:3857."""
    import pyproj
    from shapely.geometry import shape, Polygon
    from shapely.ops import unary_union, transform
    to3857 = pyproj.Transformer.from_crs(4326, 3857, always_xy=True).transform
    south = []
    for p in idx["processed"]:
        ys = [y for x, y in p["ring"]]
        if p["run"] == MAIN_RUN and (min(ys) + max(ys)) / 2 < SOUTH_MAX_LAT:
            south.append(transform(to3857, Polygon(p["ring"])))
    iraq = transform(to3857, unary_union([shape(f["geometry"]) for f in
                     json.load(open(crops + "boundaries.geojson"))["features"]]).buffer(0))
    return unary_union(south).intersection(iraq), len(south)
