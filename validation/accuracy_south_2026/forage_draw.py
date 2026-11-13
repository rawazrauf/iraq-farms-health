"""Forage test, step 1. Draw the sample: 50 of the phase-1 points whose final label is "winter crop"
(simple random, seed 20261113), plus every "perennial" point as a control that should show cuts.
Writes data/forage_sample.csv (id, lat, lon, final_label, group). The map class is not used.
Usage: python forage_draw.py"""
import csv, os, random
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
L = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "labels_final.csv")))}
P = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "points.csv")))}
w = sorted(i for i in L if L[i]["final_label"] == "winter_crop")
random.Random(20261113).shuffle(w)
ids = sorted(w[:50]) + sorted(i for i in L if L[i]["final_label"] == "perennial")
with open(os.path.join(D, "forage_sample.csv"), "w", newline="") as fh:
    out = csv.writer(fh, lineterminator="\n"); out.writerow(["id", "lat", "lon", "final_label", "group"])
    for i in ids:
        lab = L[i]["final_label"]
        out.writerow([i, float(P[i]["lat"]), float(P[i]["lon"]), lab, "test" if lab == "winter_crop" else "control"])
print(f"{len(ids)} points: {sum(L[i]['final_label'] == 'winter_crop' for i in ids)} winter crop (of {len(w)}), "
      f"{sum(L[i]['final_label'] == 'perennial' for i in ids)} perennial")
