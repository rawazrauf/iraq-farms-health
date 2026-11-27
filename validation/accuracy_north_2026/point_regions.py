"""Step 5a. Governorate and region of each sample point -> data/point_regions.csv (for the sub-area estimates).
Reads data/points.csv and the frozen map's boundaries.geojson; never the map key."""
import csv, json
from shapely.geometry import shape, Point
from common import args, load_index

a = args()
load_index(a)
govs = [(f["properties"]["name"], shape(f["geometry"]).buffer(0)) for f in json.load(open(a.crops + "boundaries.geojson"))["features"]]
KRI = {"Erbil", "Duhok", "Sulaymaniyah", "Halabja"}
with open(a.out + "/point_regions.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "governorate", "region"])
    for p in csv.DictReader(open(a.out + "/points.csv")):
        pt = Point(float(p["lon"]), float(p["lat"]))
        g = next((n for n, s in govs if s.contains(pt)), None)
        if g is None:                                   # on a simplified border: nearest governorate
            g = min(govs, key=lambda t: t[1].distance(pt))[0]
        w.writerow([p["id"], g, "Kurdistan Region" if g in KRI else "federal north"])
print("written", a.out + "/point_regions.csv")
