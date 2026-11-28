"""Step 8. Second labeller (README section 8): compare data/spotcheck_second_labeller.csv with Claude's labels on the
57 spot-check points, and write data/labels_amended2_second_labeller.csv, which is labels_amended2.csv with the second
labeller's answers in place of Claude's on those 57 points (same rule as amendment 2: a winter-crop curve counts only on
farmed land; "unsure" land is resolved with FTW 2025 where Claude's land-use look recorded it, otherwise not farmed).

Usage: python spotcheck_compare.py   then   python estimate.py data/labels_amended2_second_labeller.csv --column amended_label"""
import csv, os
from collections import Counter

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
rd = lambda f: list(csv.DictReader(open(os.path.join(D, f))))
ids = [r["id"] for r in rd("spotcheck_ids.csv")]
sl = {r["id"]: r for r in rd("spotcheck_second_labeller.csv")}
fin = {r["id"]: r["final_label"] for r in rd("labels_final.csv")}
lu = {r["id"]: r for r in rd("landuse.csv")}
am2 = {r["id"]: r for r in rd("labels_amended2.csv")}
assert set(sl) == set(ids) and all(sl[k]["curve_label"] and sl[k]["landuse"] for k in ids), "answers incomplete"


def sl_amended(k):
    c, land = sl[k]["curve_label"], sl[k]["landuse"]
    if c != "winter_crop":
        return c
    if land == "unsure":
        land = "farmed" if lu.get(k, {}).get("ftw2025_inside") == "1" else "not_farmed"
    return "winter_crop" if land == "farmed" else "no_crop"


n = len(ids)
cur = Counter((fin[k], sl[k]["curve_label"]) for k in ids)
print(f"Curve label, exact: {sum(v for (a, b), v in cur.items() if a == b)} of {n}")
print(f"Curve, winter crop or not: {sum(v for (a, b), v in cur.items() if (a == 'winter_crop') == (b == 'winter_crop'))} of {n}")
for (a, b), v in sorted(cur.items()):
    if a != b:
        print(f"   Claude {a:<12} second labeller {b:<12} {v}")
both = [k for k in ids if k in lu]
dec = [k for k in both if lu[k]["landuse"] != "unsure" and sl[k]["landuse"] != "unsure"]
print(f"Land use, points both looked at: {len(both)}; agree where both decided: "
      f"{sum(lu[k]['landuse'] == sl[k]['landuse'] for k in dec)} of {len(dec)}")
pos_c = {k for k in ids if am2[k]["amended_label"] == "winter_crop"}
pos_s = {k for k in ids if sl_amended(k) == "winter_crop"}
print(f"Winter crop on farmland: agree on {n - len(pos_c ^ pos_s)} of {n}; Claude {len(pos_c)} points, second labeller "
      f"{len(pos_s)}; both {len(pos_c & pos_s)}; Claude only {sorted(pos_c - pos_s)}; second labeller only {sorted(pos_s - pos_c)}")
with open(os.path.join(D, "labels_amended2_second_labeller.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "amended_label"])
    for k, r in am2.items():
        w.writerow([k, sl_amended(k) if k in sl else r["amended_label"]])
print("written data/labels_amended2_second_labeller.csv")
