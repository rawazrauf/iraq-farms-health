"""Step 5. Accuracy and area estimates (Olofsson et al. 2014, stratified random sample).
Map positive = a set of strata; reference positive = label "winter_crop".
Unclear points: left out (headline), or all counted as winter crop / as not (bounds).

Usage: python estimate.py [labels csv, default data/labels_final.csv] [--column final_label] [--topup [csv]]
--topup adds the phase-2 not-cropland points (README section 7): data/topup_map_key.csv and their labels
(default data/topup_labels_final.csv). Within the stratum both phases are uniform random draws, so the
points are pooled into one sample of that stratum; stratum areas are unchanged."""
import argparse, csv, json, math, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
design = json.load(open(os.path.join(D, "design.json")))
key = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "map_key.csv")))}
A = design["area_ha"]; Atot = sum(A.values()); W = {h: a / Atot for h, a in A.items()}


def run(labels, map_pos, unclear_as):
    n = defaultdict(int); y = defaultdict(lambda: defaultdict(int))     # y[h][(map, ref)]
    for pid, k in key.items():
        h = k["stratum"]; lab = labels[pid]
        if lab == "unclear":
            if unclear_as is None: continue
            ref = unclear_as
        else:
            ref = lab == "winter_crop"
        mp = h in map_pos
        n[h] += 1; y[h][(mp, ref)] += 1
    p = defaultdict(float)                     # area-weighted cell proportions
    for h in A:
        if not n[h]: continue
        for c, cnt in y[h].items(): p[c] += W[h] * cnt / n[h]
    oa = p[(True, True)] + p[(False, False)]
    ua = p[(True, True)] / (p[(True, True)] + p[(True, False)])
    pa = p[(True, True)] / (p[(True, True)] + p[(False, True)])
    ref_area_prop = p[(True, True)] + p[(False, True)]
    se_area2 = se_oa2 = 0.0                    # Olofsson 2014 eqs 5 and 10
    for h in A:
        nh = n[h]
        if nh < 2: continue
        refs = [ref for (mp, ref), c in y[h].items() for _ in range(c)]
        mps = [mp for (mp, ref), c in y[h].items() for _ in range(c)]
        pr = sum(refs) / nh; se_area2 += W[h] ** 2 * pr * (1 - pr) / (nh - 1)
        po = sum(m == r for m, r in zip(mps, refs)) / nh
        se_oa2 += W[h] ** 2 * po * (1 - po) / (nh - 1)
    mpos = [h for h in A if h in map_pos]      # UA: map-positive strata only
    Wp = sum(W[h] for h in mpos); se_ua2 = 0.0
    for h in mpos:
        nh = n[h]
        if nh < 2: continue
        pr = y[h][(True, True)] / nh
        se_ua2 += (W[h] / Wp) ** 2 * pr * (1 - pr) / (nh - 1)
    Xhat = sum(A[h] * (y[h][(True, True)] + y[h][(False, True)]) / n[h] for h in A if n[h])
    Yhat = sum(A[h] * y[h][(True, True)] / n[h] for h in A if n[h])
    R = Yhat / Xhat; se_pa2 = 0.0              # PA: ratio estimator (Olofsson 2014 eq. 7 form)
    for h in A:
        nh = n[h]
        if nh < 2: continue
        yv = [1 if (mp and r) else 0 for (mp, r), c in y[h].items() for _ in range(c)]
        xv = [1 if r else 0 for (mp, r), c in y[h].items() for _ in range(c)]
        ym, xm = sum(yv) / nh, sum(xv) / nh
        s2y = sum((a - ym) ** 2 for a in yv) / (nh - 1); s2x = sum((b - xm) ** 2 for b in xv) / (nh - 1)
        sxy = sum((a - ym) * (b - xm) for a, b in zip(yv, xv)) / (nh - 1)
        se_pa2 += A[h] ** 2 * (s2y + R ** 2 * s2x - 2 * R * sxy) / nh
    return {"n": dict(n), "y": {h: dict(v) for h, v in y.items()}, "OA": oa, "OA_ci": 1.96 * math.sqrt(se_oa2),
            "UA": ua, "UA_ci": 1.96 * math.sqrt(se_ua2), "PA": pa, "PA_ci": 1.96 * math.sqrt(se_pa2) / Xhat,
            "ref_area_ha": ref_area_prop * Atot, "ref_area_ci_ha": 1.96 * math.sqrt(se_area2) * Atot,
            "map_area_ha": sum(A[h] for h in map_pos)}


def load_labels(path, column):
    return {r["id"]: r[column] for r in csv.DictReader(open(path))}


def add_topup(labels, path=None, column="final_label"):
    """Pool the phase-2 points into `key` and `labels` (in place)."""
    tk = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "topup_map_key.csv")))}
    tl = load_labels(path or os.path.join(D, "topup_labels_final.csv"), column)
    missing = set(tk) - set(tl)
    if missing:
        raise SystemExit(f"{len(missing)} top-up points have no label, e.g. {sorted(missing)[:3]}")
    key.update(tk); labels.update({i: tl[i] for i in tk})
    return labels


PRODUCTS = (("confident cereal", {"confident_cereal"}),
            ("confident + doubtful cereal", {"confident_cereal", "doubtful_cereal"}))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("labels", nargs="?", default=os.path.join(D, "labels_final.csv"))
    ap.add_argument("--column", default="final_label")
    ap.add_argument("--topup", nargs="?", const="", default=None, help="pool the phase-2 points")
    a = ap.parse_args()
    labels = load_labels(a.labels, a.column)
    if a.topup is not None:
        add_topup(labels, a.topup or None, a.column)
        print(f"Phase 1 + phase-2 top-up ({sum(1 for i in key if i.startswith('T'))} not-cropland points)\n")
    for name, mp in PRODUCTS:
        for rule, lab in ((None, "unclear left out"), (True, "unclear = winter crop"), (False, "unclear = not")):
            r = run(labels, mp, rule)
            print(f"{name:<28} {lab:<22} OA {r['OA']:.3f}±{r['OA_ci']:.3f}  UA {r['UA']:.3f}±{r['UA_ci']:.3f}  "
                  f"PA {r['PA']:.3f}±{r['PA_ci']:.3f}  winter-crop area {r['ref_area_ha']:,.0f} ± "
                  f"{r['ref_area_ci_ha']:,.0f} ha (map {r['map_area_ha']:,.0f})")
    print("\nWinter crop by map class (unclear left out):")
    print(f"{'map class':<18}{'points':>8}{'winter crop':>13}{'share':>8}{'winter-crop area (ha)':>24}")
    for h in A:
        pts = [labels[i] for i, k in key.items() if k["stratum"] == h and labels[i] != "unclear"]
        wc = sum(l == "winter_crop" for l in pts)
        print(f"{h:<18}{len(pts):>8}{wc:>13}{wc/len(pts):>8.0%}{A[h]*wc/len(pts):>24,.0f}")
