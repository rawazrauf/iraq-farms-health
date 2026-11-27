"""Step 6. Accuracy and area estimates (Olofsson et al. 2014, stratified random sample), northern tiles.
Map positive = a set of strata; reference positive = label "winter_crop".
Unclear points: left out (headline), or all counted as winter crop / as not (bounds).
Sub-areas (Kurdistan Region, federal north) are domain estimates: ratio estimators over the whole stratified sample.

Usage: python estimate.py [labels csv, default data/labels_final.csv] [--column final_label]"""
import argparse, csv, json, math, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
design = json.load(open(os.path.join(D, "design.json")))
key = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "map_key.csv")))}
region = {r["id"]: r["region"] for r in csv.DictReader(open(os.path.join(D, "point_regions.csv")))}
A = design["area_ha"]; Atot = sum(A.values()); W = {h: a / Atot for h, a in A.items()}


def run(labels, map_pos, unclear_as):
    """Same estimators as validation/accuracy_south_2026/estimate.py."""
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
    p = defaultdict(float)
    for h in A:
        if not n[h]: continue
        for c, cnt in y[h].items(): p[c] += W[h] * cnt / n[h]
    oa = p[(True, True)] + p[(False, False)]
    ua = p[(True, True)] / (p[(True, True)] + p[(True, False)])
    pa = p[(True, True)] / (p[(True, True)] + p[(False, True)])
    ref_area_prop = p[(True, True)] + p[(False, True)]
    se_area2 = se_oa2 = 0.0
    for h in A:
        nh = n[h]
        if nh < 2: continue
        refs = [ref for (mp, ref), c in y[h].items() for _ in range(c)]
        mps = [mp for (mp, ref), c in y[h].items() for _ in range(c)]
        pr = sum(refs) / nh; se_area2 += W[h] ** 2 * pr * (1 - pr) / (nh - 1)
        po = sum(m == r for m, r in zip(mps, refs)) / nh
        se_oa2 += W[h] ** 2 * po * (1 - po) / (nh - 1)
    mpos = [h for h in A if h in map_pos]
    Wp = sum(W[h] for h in mpos); se_ua2 = 0.0
    for h in mpos:
        nh = n[h]
        if nh < 2: continue
        pr = y[h][(True, True)] / nh
        se_ua2 += (W[h] / Wp) ** 2 * pr * (1 - pr) / (nh - 1)
    Xhat = sum(A[h] * (y[h][(True, True)] + y[h][(False, True)]) / n[h] for h in A if n[h])
    Yhat = sum(A[h] * y[h][(True, True)] / n[h] for h in A if n[h])
    R = Yhat / Xhat; se_pa2 = 0.0
    for h in A:
        nh = n[h]
        if nh < 2: continue
        yv = [1 if (mp and r) else 0 for (mp, r), c in y[h].items() for _ in range(c)]
        xv = [1 if r else 0 for (mp, r), c in y[h].items() for _ in range(c)]
        ym, xm = sum(yv) / nh, sum(xv) / nh
        s2y = sum((a - ym) ** 2 for a in yv) / (nh - 1); s2x = sum((b - xm) ** 2 for b in xv) / (nh - 1)
        sxy = sum((a - ym) * (b - xm) for a, b in zip(yv, xv)) / (nh - 1)
        se_pa2 += A[h] ** 2 * (s2y + R ** 2 * s2x - 2 * R * sxy) / nh
    return {"n": dict(n), "OA": oa, "OA_ci": 1.96 * math.sqrt(se_oa2),
            "UA": ua, "UA_ci": 1.96 * math.sqrt(se_ua2), "PA": pa, "PA_ci": 1.96 * math.sqrt(se_pa2) / Xhat,
            "ref_area_ha": ref_area_prop * Atot, "ref_area_ci_ha": 1.96 * math.sqrt(se_area2) * Atot,
            "map_area_ha": sum(A[h] for h in map_pos)}


def domain(labels, map_pos, dom):
    """Ratio and total estimators restricted to points in region `dom` (unclear left out).
    Returns UA, PA, OA with 95% half-widths, winter-crop area and mapped area of the domain."""
    def ratio(yf, xf):
        Y = X = 0.0; parts = []
        for h in A:
            pts = [(pid, k) for pid, k in key.items() if k["stratum"] == h and labels[pid] != "unclear"]
            nh = len(pts)
            if not nh: continue
            yv = [yf(pid, k) for pid, k in pts]; xv = [xf(pid, k) for pid, k in pts]
            Y += A[h] * sum(yv) / nh; X += A[h] * sum(xv) / nh; parts.append((h, nh, yv, xv))
        if not X: return None, None, X
        R = Y / X; v = 0.0
        for h, nh, yv, xv in parts:
            if nh < 2: continue
            ym, xm = sum(yv) / nh, sum(xv) / nh
            s2y = sum((a - ym) ** 2 for a in yv) / (nh - 1); s2x = sum((b - xm) ** 2 for b in xv) / (nh - 1)
            sxy = sum((a - ym) * (b - xm) for a, b in zip(yv, xv)) / (nh - 1)
            v += A[h] ** 2 * (s2y + R ** 2 * s2x - 2 * R * sxy) / nh
        return R, 1.96 * math.sqrt(v) / X, X
    ind = lambda pid: region[pid] == dom
    ref = lambda pid: labels[pid] == "winter_crop"
    mp = lambda k: k["stratum"] in map_pos
    ua = ratio(lambda p, k: ind(p) and mp(k) and ref(p), lambda p, k: ind(p) and mp(k))
    pa = ratio(lambda p, k: ind(p) and mp(k) and ref(p), lambda p, k: ind(p) and ref(p))
    oa = ratio(lambda p, k: ind(p) and (mp(k) == ref(p)), lambda p, k: ind(p))
    # domain totals: area of winter crop and of the domain
    tot = 0.0; v = 0.0
    for h in A:
        pts = [pid for pid, k in key.items() if k["stratum"] == h and labels[pid] != "unclear"]
        nh = len(pts); yv = [1 if ind(p) and ref(p) else 0 for p in pts]; ym = sum(yv) / nh
        tot += A[h] * ym
        if nh > 1: v += A[h] ** 2 * sum((a - ym) ** 2 for a in yv) / (nh - 1) / nh
    return {"UA": ua[:2], "PA": pa[:2], "OA": oa[:2], "ref_area_ha": tot, "ref_area_ci_ha": 1.96 * math.sqrt(v),
            "domain_area_ha": oa[2], "map_area_ha": ua[2]}


PRODUCTS = (("confident cereal", {"confident_cereal"}),
            ("confident + doubtful cereal", {"confident_cereal", "doubtful_cereal"}))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("labels", nargs="?", default=os.path.join(D, "labels_final.csv"))
    ap.add_argument("--column", default="final_label")
    a = ap.parse_args()
    labels = {r["id"]: r[a.column] for r in csv.DictReader(open(a.labels))}
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
    print("\nSub-areas (domain estimates, unclear left out):")
    for dom in ("Kurdistan Region", "federal north"):
        npts = sum(1 for i in key if region[i] == dom)
        for name, mp in PRODUCTS:
            r = domain(labels, mp, dom)
            print(f"{dom:<17} ({npts} pts) {name:<28} OA {r['OA'][0]:.3f}±{r['OA'][1]:.3f}  UA {r['UA'][0]:.3f}±{r['UA'][1]:.3f}  "
                  f"PA {r['PA'][0]:.3f}±{r['PA'][1]:.3f}  winter-crop area {r['ref_area_ha']:,.0f} ± {r['ref_area_ci_ha']:,.0f} ha "
                  f"(map {r['map_area_ha']:,.0f} of {r['domain_area_ha']:,.0f})")
