"""Compare a fresh fetch (fetch_curves.py) with the archived curves, and the rule labels from both.
Usage: python compare_curves.py data/curves_fetched.json [data/curves.json]"""
import json, sys
import numpy as np
from label_rules import label

new = json.load(open(sys.argv[1]))
old = json.load(open(sys.argv[2] if len(sys.argv) > 2 else __file__.replace("compare_curves.py", "data/curves.json")))
d, miss, same, diff = [], 0, 0, []
for pid, rec in new.items():
    if pid not in old or "months" not in rec: continue
    for m, v in rec["months"].items():
        o = old[pid]["months"].get(m, {})
        if "cor" in v and "cor" in o: d.append(v["cor"] - o["cor"])
        elif ("cor" in v) != ("cor" in o): miss += 1
    a, b = label(rec)[0], label(old[pid])[0] if "months" in old[pid] else "unclear"
    if a == b: same += 1
    else: diff.append((pid, b, a))
d = np.abs(np.array(d))
print(f"months compared {len(d)}: identical {np.mean(d < 0.0005):.1%}, within 0.02 {np.mean(d <= 0.02):.1%}, "
      f"max difference {d.max():.3f}; months present in only one {miss}")
print(f"rule labels: {same} same, {len(diff)} different", diff[:20])
