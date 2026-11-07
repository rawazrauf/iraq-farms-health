"""Step 1. Area of each map stratum in the southern tiles -> data/strata_area.json."""
import json, numpy as np, rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping, box
from common import args, load_index, stratum_fn, population, NAMES

a = args()
idx = load_index(a.crops); stratum = stratum_fn(idx)
pop, ntiles = population(idx, a.crops)
print("southern tiles:", ntiles)
area = np.zeros(5); cellarea = {}
for c in idx["cells"]:
    with rasterio.open(a.crops + c["file"]) as ds:
        part = pop.intersection(box(*ds.bounds))
        if part.is_empty: continue
        m = rasterize([(mapping(part), 1)], out_shape=(ds.height, ds.width), transform=ds.transform,
                      fill=0, dtype="uint8").astype(bool)
        if not m.any(): continue
        arr = ds.read(1); s = stratum(arr)
        # ground area of a Web Mercator pixel shrinks with cos(latitude)
        ys = ds.transform.f + (np.arange(ds.height) + 0.5) * ds.transform.e
        lat = np.degrees(np.arctan(np.sinh(ys / 6378137.0)))
        ha_row = (abs(ds.transform.a) * np.cos(np.radians(lat))) ** 2 / 1e4
        HA = np.broadcast_to(ha_row[:, None], arr.shape)
        ca = np.bincount(s[m], weights=HA[m], minlength=5)
        area += ca; cellarea[c["file"]] = ca.tolist()
json.dump({"names": NAMES, "area_ha": area.tolist(), "cells": cellarea},
          open(a.out + "/strata_area.json", "w"), indent=1)
for n, v in zip(NAMES, area): print(f"{n:<18}{v:>14,.0f} ha  {v/area.sum():6.1%}")
print("total", f"{area.sum():,.0f} ha")
