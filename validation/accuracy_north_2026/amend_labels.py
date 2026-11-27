"""Step 7. Amended reference labels (README section 7): a winter-crop curve counts only on farmed land.

Reads data/labels_final.csv (curve labels, unchanged) and data/landuse.csv (imagery land use per point and the FTW field
test). Writes
  data/labels_amended.csv   amendment 1: imagery land use; "unsure" land -> unclear
  data/labels_amended2.csv  amendment 2: "unsure" land resolved with FTW 2025 (inside a field -> farmed)
  data/labels_amended2_ftw2024.csv  sensitivity: "unsure" land resolved with FTW 2024
A winter-crop curve on land judged not farmed becomes no_crop; unclear curves stay unclear."""
import csv, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
fin = {r["id"]: r["final_label"] for r in csv.DictReader(open(os.path.join(D, "labels_final.csv")))}
lu = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "landuse.csv")))}
RULES = {
    "labels_amended.csv": lambda r: r["landuse"],
    "labels_amended2.csv": lambda r: r["landuse_resolved"],
    "labels_amended2_ftw2024.csv": lambda r: r["landuse"] if r["landuse"] != "unsure"
        else ("farmed" if r["ftw2024_inside"] == "1" else "not_farmed"),
}
for fn, land_of in RULES.items():
    with open(os.path.join(D, fn), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "curve_label", "landuse", "amended_label"])
        for k, cl in fin.items():
            if k in lu:
                land = land_of(lu[k])
                if cl == "winter_crop":
                    am = {"farmed": "winter_crop", "not_farmed": "no_crop"}.get(land, "unclear")
                else:
                    am = "unclear"
            else:
                land, am = "", cl
            w.writerow([k, cl, land, am])
    print("written", fn)
