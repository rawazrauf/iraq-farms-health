"""Step 4. Rule-based reference labels from the curves (rules: README.md, "Reference labels").
Uses offset-corrected NDVI ("cor"). Blind: never reads map_key.csv.

Usage: python label_rules.py [curves file, default data/curves.json] [--out data/labels_rule_new.csv]
Accepts the archived data/curves.json or a fresh data/curves_fetched.json."""
import argparse, csv, json, os
from collections import Counter

MON = [f"2025-{m:02d}" for m in range(9, 13)] + [f"2026-{m:02d}" for m in range(1, 9)]
WIN = ["2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]
SUM = ["2026-06", "2026-07", "2026-08", "2025-09"]
EARLY = ["2025-09", "2025-10", "2025-11", "2025-12"]
LATE = ["2026-04", "2026-05", "2026-06", "2026-07"]


def label(rec):
    v = {m: rec["months"][m]["cor"] for m in MON if m in rec["months"] and "cor" in rec["months"][m]}
    if len(v) < 6:
        return "unclear", "fewer than 6 clear months"
    vals = list(v.values())
    if sum(x < 0 for x in vals) >= len(vals) / 2:
        return "water", "NDVI < 0 in half the months"
    if sum(x >= 0.35 for x in vals) >= 10 and min(vals) >= 0.25:
        return "perennial", "green all year"
    wv = {m: v[m] for m in WIN if m in v}
    W = max(wv.values()) if wv else None
    S = max([v[m] for m in SUM if m in v], default=None)
    B = min(vals)
    missing_win = sum(m not in v for m in WIN)
    if W is not None and W >= 0.40 and W - B >= 0.25:
        pk = max(wv, key=wv.get)
        early_ok = any(m in v and v[m] <= W - 0.20 and m < pk for m in EARLY)
        late_ok = any(m in v and m > pk and v[m] <= B + 0.5 * (W - B) for m in LATE)
        if early_ok and late_ok:
            return "winter_crop", f"peak {W:.2f} in {pk}, low {B:.2f}"
    if (W is None or W < 0.30) and S is not None and S >= 0.40:
        return "summer_only", f"summer peak {S:.2f}, winter max {W}"
    if max(vals) < 0.30:
        return "no_crop", f"max {max(vals):.2f}"
    if missing_win >= 2:
        return "unclear", f"{missing_win} winter months missing"
    return "unclear", f"W={W} S={S} B={B:.2f}"


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("curves", nargs="?", default=os.path.join(here, "data", "curves.json"))
    ap.add_argument("--out", default=os.path.join(here, "data", "labels_rule_new.csv"))
    a = ap.parse_args()
    C = json.load(open(a.curves))
    rows = []
    for k in sorted(C):
        rec = C[k]
        if "months" not in rec:
            rows.append((k, "unclear", "no data: " + str(rec.get("err"))[:80])); continue
        rows.append((k, *label(rec)))
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "rule_label", "rule_reason"]); w.writerows(rows)
    print(Counter(r[1] for r in rows)); print("written", a.out)
