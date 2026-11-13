"""Land-use check against very-high-resolution imagery (README section 11).

76 points: the 72 hand-reviewed points and the 5 points where the map says "not cropland" and the
reference says winter crop (one point is in both groups). Each was looked at in Esri World Imagery
(0.3-0.5 m; the app's basemap) in a 250 m window, and given one land class by eye:
  F field parcels   T trees or orchard   E field edge or canal bank
  U farmstead or built   B bare or natural land with no parcels   W marsh or water
data/vhr_landuse.csv holds the class and the image date of each point. The image dates run from 2018
to April 2025: none is in the 2025-26 season, so this shows what kind of land a point is, not what
grew there in 2025-26. The reading was not blind to the reference labels.

This script joins that file with the reference labels and prints the tables.
  python vhr_check.py            tables from the archived file
  python vhr_check.py --dates    also re-read each image date from Esri's service and report changes
                                 (the basemap is updated over time; not run when this was archived)"""
import argparse, csv, os
from collections import Counter

here = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(here, "data")
ap = argparse.ArgumentParser(); ap.add_argument("--dates", action="store_true"); a = ap.parse_args()
rd = lambda f: {r["id"]: r for r in csv.DictReader(open(os.path.join(D, f)))}
lab = {**rd("labels_final.csv"), **rd("topup_labels_final.csv")}
key = {**rd("map_key.csv"), **rd("topup_map_key.csv")}
V = rd("vhr_landuse.csv")
CL = "FTEUBW"

yrs = Counter(v["image_date"][:4] for v in V.values())
print(f"{len(V)} points; image years: " + ", ".join(f"{y} x{n}" for y, n in sorted(yrs.items())))
print(f"latest image {max(v['image_date'] for v in V.values())}; in the 2025-26 season (Sep-Aug): "
      f"{sum('2025-09-01' <= v['image_date'] <= '2026-08-31' for v in V.values())}; "
      f"taken in December-April of any year: {sum(v['image_date'][5:7] in ('12', '01', '02', '03', '04') for v in V.values())}")
t = Counter((lab[i]["final_label"], V[i]["land"]) for i in V)
print("\nreference label " + "".join(f"{c:>4}" for c in CL) + "    n")
for l in ("winter_crop", "summer_only", "perennial", "no_crop", "unclear"):
    print(f"{l:<16}" + "".join(f"{t[(l, c)]:>4}" for c in CL) + f"{sum(t[(l, c)] for c in CL):>5}")
crop = [i for i in V if lab[i]["final_label"] in ("winter_crop", "summer_only", "perennial")]
farm = [i for i in crop if V[i]["land"] in "FTE"]
print(f"\ncrop labels (winter, summer, perennial) on fields, orchards or their edges: {len(farm)} of {len(crop)}")
print("crop labels on other land:")
for i in sorted(crop):
    if i not in farm:
        print(f"  {i} {lab[i]['final_label']:<12} land {V[i]['land']}  map {key[i]['stratum']:<16} image {V[i]['image_date']}")
om = sorted(i for i in V if key[i]["stratum"] == "not_cropland" and lab[i]["final_label"] == "winter_crop")
print('map "not cropland", reference winter crop:')
for i in om:
    print(f"  {i} land {V[i]['land']}  image {V[i]['image_date']}")

if a.dates:
    import requests
    U = "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/identify"
    changed = 0
    for i, v in sorted(V.items()):
        lon, lat = float(v["lon"]), float(v["lat"])
        j = requests.get(U, params={"f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
                                    "sr": "4326", "layers": "all:2", "tolerance": "1", "returnGeometry": "false",
                                    "mapExtent": f"{lon - .001},{lat - .001},{lon + .001},{lat + .001}",
                                    "imageDisplay": "256,256,96"}, timeout=40).json()
        d = (j.get("results") or [{}])[0].get("attributes", {}).get("DATE (YYYYMMDD)", "")
        d = f"{d[:4]}-{d[4:6]}-{d[6:]}" if len(d) == 8 else "none"
        if d != v["image_date"]:
            changed += 1; print(f"  {i}: archived {v['image_date']}, now {d}")
    print(f"image date changed at {changed} of {len(V)} points")
