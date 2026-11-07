"""Check. Stratified bootstrap of the headline figures: resample points with replacement within each
stratum (sizes fixed), re-estimate, report the 2.5-97.5 percentiles. Seed fixed for repeatability.
Usage: python bootstrap.py [labels csv] [--draws 4000]"""
import argparse, os, random
import numpy as np
import estimate as E

ap = argparse.ArgumentParser()
ap.add_argument("labels", nargs="?", default=os.path.join(E.D, "labels_final.csv"))
ap.add_argument("--column", default="final_label")
ap.add_argument("--draws", type=int, default=4000)
a = ap.parse_args()
labels = E.load_labels(a.labels, a.column)
ids = {h: [i for i, k in E.key.items() if k["stratum"] == h and labels[i] != "unclear"] for h in E.A}
rnd = random.Random(20261107)
orig_key = E.key
for name, mp in E.PRODUCTS:
    stats = {"UA": [], "PA": [], "OA": [], "ref_area_ha": []}
    for _ in range(a.draws):
        k2, l2 = {}, {}
        for h, lst in ids.items():
            for j, pid in enumerate(rnd.choices(lst, k=len(lst))):
                nid = f"{h}{j}"; k2[nid] = orig_key[pid]; l2[nid] = labels[pid]
        E.key = k2
        try:
            r = E.run(l2, mp, None)
        except ZeroDivisionError:
            continue
        for s in stats: stats[s].append(r[s])
    E.key = orig_key
    r0 = E.run(labels, mp, None)
    print(name)
    for s, v in stats.items():
        lo, hi = np.percentile(v, [2.5, 97.5])
        f = (lambda x: f"{x/1e6:.2f} Mha") if s == "ref_area_ha" else (lambda x: f"{x:.3f}")
        print(f"  {s:<12} estimate {f(r0[s])}   bootstrap 95% {f(lo)} - {f(hi)}")
