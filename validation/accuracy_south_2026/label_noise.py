"""Check. How much could the least repeatable step, the manual look at borderline curves, move the results?

72 points were labelled by hand (the rules said "unclear"): 57 in phase 1, 15 in the top-up. The 57 were
labelled twice, blind, a day apart (README section 7). For the estimates only three states matter: winter
crop / not winter crop / unclear. The two rounds give an empirical table of how often a curve in one state
was put in another. This script redraws every hand label from that table (both directions pooled, so no
round is treated as the truth), re-estimates, and repeats. Rule labels (85% of points) never change.

Two outputs per product: the spread from label noise alone, and the spread from label noise plus sampling
(each redraw is also resampled within strata, as bootstrap.py does). Seed fixed for repeatability.
Usage: python label_noise.py [--draws 10000]"""
import argparse, csv, os, random
from collections import Counter, defaultdict
import numpy as np
import estimate as E

ap = argparse.ArgumentParser(); ap.add_argument("--draws", type=int, default=10000); a = ap.parse_args()
D = E.D
state = lambda lab: "winter" if lab == "winter_crop" else "unclear" if lab == "unclear" else "not"
p1 = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "labels_final.csv")))}
tu = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "topup_labels_final.csv")))}
rkey = {r["rid"]: r["id"] for r in csv.DictReader(open(os.path.join(D, "review_key.csv")))}
rev = {rkey[r["rid"]]: r["your_label"] for r in csv.DictReader(open(os.path.join(D, "review_blind.csv")))}

# transition table from the 57 curves labelled twice (round 1 = phase-1 final label, round 2 = blind re-review)
pairs = [(state(p1[i]["final_label"]), state(rev[i])) for i in rev if i.startswith("S")]
T = defaultdict(Counter)
for x, y in pairs: T[x][y] += 1; T[y][x] += 1          # pooled both ways
print(f"{len(pairs)} curves labelled twice; same state both times: {sum(x == y for x, y in pairs)}")
print("round 1 -> round 2:", dict(Counter(f"{x}->{y}" for x, y in pairs)))
for s in ("winter", "not", "unclear"):
    tot = sum(T[s].values()); print(f"  a curve labelled {s:<8} is redrawn as: " + ", ".join(f"{k} {v/tot:.0%}" for k, v in sorted(T[s].items())))

labels = E.load_labels(os.path.join(D, "labels_final.csv"), "final_label"); E.add_topup(labels)
hand = [i for i in labels if (p1.get(i) or tu.get(i))["reviewed_by_hand"] == "yes"]
print(f"{len(hand)} hand-labelled points of {len(labels)}\n")
back = {"winter": "winter_crop", "not": "no_crop", "unclear": "unclear"}
rnd = random.Random(20261112)
def redraw():
    l2 = dict(labels)
    for i in hand:
        row = T[state(labels[i])]; l2[i] = back[rnd.choices(list(row), weights=list(row.values()))[0]]
    return l2

orig_key = E.key
fmt = lambda s, x: f"{x/1e6:.2f} Mha" if s == "ref_area_ha" else f"{x:.3f}"
for name, mp in E.PRODUCTS:
    r0 = E.run(labels, mp, None)
    noise = defaultdict(list); both = defaultdict(list)
    for _ in range(a.draws):
        l2 = redraw()
        r = E.run(l2, mp, None)
        for s in ("UA", "PA", "OA", "ref_area_ha"): noise[s].append(r[s])
        ids = {h: [i for i, k in orig_key.items() if k["stratum"] == h and l2[i] != "unclear"] for h in E.A}
        k2, l3 = {}, {}
        for h, lst in ids.items():
            for j, pid in enumerate(rnd.choices(lst, k=len(lst))):
                k2[f"{h}{j}"] = orig_key[pid]; l3[f"{h}{j}"] = l2[pid]
        E.key = k2
        try:
            r = E.run(l3, mp, None)
            for s in ("UA", "PA", "OA", "ref_area_ha"): both[s].append(r[s])
        except ZeroDivisionError: pass
        E.key = orig_key
    print(name)
    for s in ("UA", "PA", "OA", "ref_area_ha"):
        n_lo, n_md, n_hi = np.percentile(noise[s], [2.5, 50, 97.5]); b_lo, b_hi = np.percentile(both[s], [2.5, 97.5])
        print(f"  {s:<12} headline {fmt(s, r0[s])}   label noise only: median {fmt(s, n_md)}, 95% {fmt(s, n_lo)} - {fmt(s, n_hi)}"
              f"   with sampling: 95% {fmt(s, b_lo)} - {fmt(s, b_hi)}")
