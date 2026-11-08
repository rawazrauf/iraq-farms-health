"""Phase 2 (README section 7): rule labels for the top-up points, a blind pack for the manual look, and the
final labels.

Every top-up point is in the "not cropland" stratum, so a reviewer who knows a curve is a top-up point is not
blind to the map. The rule-unclear top-up curves are therefore mixed with the 57 phase-1 rule-unclear curves,
shuffled under new ids (R001...), and reviewed without the key. The phase-1 re-review is an agreement check
only: phase-1 final labels are not changed.

  python topup_review.py pack   <topup curves json>    -> data/topup_labels_rule.csv, data/review_blind.csv,
                                                          data/review_key.csv
  (fill the your_label column of data/review_blind.csv: winter_crop, summer_only, perennial, no_crop,
   water or unclear, plus an optional note)
  python topup_review.py final                         -> data/topup_labels_final.csv + agreement report
"""
import csv, json, os, random, sys
from label_rules import label, MON

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")
SEED3 = 20261109
LABELS = {"winter_crop", "summer_only", "perennial", "no_crop", "water", "unclear"}


def curve(rec):
    return ",".join(str(round(rec["months"][m]["cor"] * 1000)) if "cor" in rec["months"].get(m, {}) else ""
                    for m in MON)


if sys.argv[1:2] == ["pack"]:
    new = json.load(open(sys.argv[2])); old = json.load(open(os.path.join(D, "curves.json")))
    ids = [r["id"] for r in csv.DictReader(open(os.path.join(D, "topup_points.csv")))]
    rows = []
    for i in ids:
        rec = new.get(i)
        lab, why = label(rec) if rec and "months" in rec else ("unclear", "no data: " + str((rec or {}).get("err"))[:80])
        rows.append((i, lab, why))
    with open(os.path.join(D, "topup_labels_rule.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "rule_label", "rule_reason"]); w.writerows(rows)
    p1 = [r["id"] for r in csv.DictReader(open(os.path.join(D, "labels_final.csv"))) if r["rule_label"] == "unclear"]
    pack = [(i, curve(new[i])) for i, lab, _ in rows if lab == "unclear" and i in new and "months" in new[i]]
    pack += [(i, curve(old[i])) for i in p1]
    random.Random(SEED3).shuffle(pack)
    with open(os.path.join(D, "review_blind.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["rid", "ndvi_corrected_x1000_Sep2025_to_Aug2026", "your_label", "note"])
        for k, (i, c) in enumerate(pack): w.writerow([f"R{k+1:03d}", c, "", ""])
    with open(os.path.join(D, "review_key.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["rid", "id"])
        for k, (i, c) in enumerate(pack): w.writerow([f"R{k+1:03d}", i])
    n_t = sum(1 for i, _ in pack if i.startswith("T"))
    print(f"{len(rows)} top-up points labelled by the rules; review pack: {len(pack)} curves "
          f"({n_t} top-up + {len(p1)} phase-1), shuffled")

elif sys.argv[1:2] == ["final"]:
    rule = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "topup_labels_rule.csv")))}
    keyr = {r["rid"]: r["id"] for r in csv.DictReader(open(os.path.join(D, "review_key.csv")))}
    rev = {keyr[r["rid"]]: r for r in csv.DictReader(open(os.path.join(D, "review_blind.csv")))}
    bad = [i for i, r in rev.items() if r["your_label"] not in LABELS]
    if bad:
        raise SystemExit(f"{len(bad)} review rows without a valid label, e.g. {bad[:3]}")
    with open(os.path.join(D, "topup_labels_final.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "rule_label", "rule_reason", "final_label", "reviewed_by_hand", "review_note"])
        for i, r in rule.items():
            hand = i in rev
            w.writerow([i, r["rule_label"], r["rule_reason"], rev[i]["your_label"] if hand else r["rule_label"],
                        "yes" if hand else "no", rev[i]["note"] if hand else ""])
    p1 = {r["id"]: r["final_label"] for r in csv.DictReader(open(os.path.join(D, "labels_final.csv")))}
    pairs = [(p1[i], rev[i]["your_label"]) for i in rev if i.startswith("S")]
    same = sum(a == b for a, b in pairs)
    print(f"phase-1 re-review agreement: {same} of {len(pairs)}",
          [(i, p1[i], rev[i]["your_label"]) for i in rev if i.startswith("S") and p1[i] != rev[i]["your_label"]])
    from collections import Counter
    print("top-up final labels:", Counter(rev[i]["your_label"] if i in rev else rule[i]["rule_label"] for i in rule))
else:
    print(__doc__)
