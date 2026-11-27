"""Step 4. Rule-based reference labels from the curves (rules: README.md section 3). Northern windows.
Uses offset-corrected NDVI ("cor"). Blind: never reads map_key.csv.

The southern rules (validation/accuracy_south_2026/label_rules.py) look for the winter peak in Dec-Apr.
The north run's season ends on 30 June and late rain-fed fields peak in May, so a point is a winter crop if
EITHER the southern winter test passes unchanged, OR the late test passes:
  peak W2 = highest of Dec-May >= 0.40; W2 - B >= 0.25; a Sep-Dec month before the peak at least 0.20 below it
  (green-up inside the season); a month from May-Jul after the peak at most B + 0.5 (W2 - B) (dry-down by July: the
  north season ends on 30 June);
  and the first clear month after the peak is lower than the peak (so a spring-sown summer crop that is still
  rising in May does not pass).
"Summer crop only" is unchanged (Dec-Apr below 0.30, Jun-Sep peak >= 0.40) but is only reached when both winter
tests fail; the missing-month check counts Dec-May. Everything else is as in the south.
Tested on the 575 southern curves before any northern curve existed: 570 labels identical, 5 "unclear" become
"winter crop" (S023, S079, S096, S184, S298: peak in May, dry by June; judged summer only by hand in the south).
Anything the southern rules call a winter crop stays a winter crop here.

Usage: python label_rules.py data/curves.json [--out data/labels_rule.csv]"""
import argparse, csv, json, os
from collections import Counter

MON = [f"2025-{m:02d}" for m in range(9, 13)] + [f"2026-{m:02d}" for m in range(1, 9)]
WIN_S = ["2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]            # southern winter months
WIN = WIN_S + ["2026-05"]                                                  # northern winter months
SUM = ["2026-06", "2026-07", "2026-08", "2025-09"]
EARLY = ["2025-09", "2025-10", "2025-11", "2025-12"]
LATE_S = ["2026-04", "2026-05", "2026-06", "2026-07"]
LATE = ["2026-05", "2026-06", "2026-07"]


def winter_test(v, B, win, late, local_max=False):
    wv = {m: v[m] for m in win if m in v}
    if not wv:
        return None
    W = max(wv.values()); pk = max(wv, key=wv.get)
    if W < 0.40 or W - B < 0.25:
        return None
    early_ok = any(m in v and v[m] <= W - 0.20 and m < pk for m in EARLY)
    late_ok = any(m in v and m > pk and v[m] <= B + 0.5 * (W - B) for m in late)
    if local_max:
        nxt = next((m for m in MON if m > pk and m in v), None)
        if nxt is None or v[nxt] >= W:
            return None
    return (W, pk) if early_ok and late_ok else None


def label(rec):
    v = {m: rec["months"][m]["cor"] for m in MON if m in rec["months"] and "cor" in rec["months"][m]}
    if len(v) < 6:
        return "unclear", "fewer than 6 clear months"
    vals = list(v.values())
    if sum(x < 0 for x in vals) >= len(vals) / 2:
        return "water", "NDVI < 0 in half the months"
    if sum(x >= 0.35 for x in vals) >= 10 and min(vals) >= 0.25:
        return "perennial", "green all year"
    B = min(vals)
    hit = winter_test(v, B, WIN_S, LATE_S)
    if hit:
        return "winter_crop", f"peak {hit[0]:.2f} in {hit[1]}, low {B:.2f}"
    hit = winter_test(v, B, WIN, LATE, local_max=True)
    if hit:
        return "winter_crop", f"late peak {hit[0]:.2f} in {hit[1]}, low {B:.2f}"
    W = max([v[m] for m in WIN_S if m in v], default=None)     # summer rule as in the south (Dec-Apr)
    S = max([v[m] for m in SUM if m in v], default=None)
    if (W is None or W < 0.30) and S is not None and S >= 0.40:
        return "summer_only", f"summer peak {S:.2f}, winter max {W}"
    if max(vals) < 0.30:
        return "no_crop", f"max {max(vals):.2f}"
    missing_win = sum(m not in v for m in WIN)
    if missing_win >= 2:
        return "unclear", f"{missing_win} winter months missing"
    return "unclear", f"W={W} S={S} B={B:.2f}"


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("curves")
    ap.add_argument("--out", default=os.path.join(here, "data", "labels_rule.csv"))
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
