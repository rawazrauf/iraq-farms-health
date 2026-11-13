"""Forage test, step 3. Do the "winter crop" reference points hide fodder that is cut and regrows?

The reference labels use one reading a month, which cannot show a cut. This reads every clear date
(data/forage_series.json, about every 5 days) at 50 random winter-crop points and at the 12 "perennial"
points, which serve as a control: fodder such as alfalfa is expected there, so the test should find cuts.

Rules, applied to each point's series (NDVI, 1 Nov 2025 - 15 Jun 2026):
  0. One-date outliers are removed first: a reading at least 0.15 below (or above) both neighbours, when
     the neighbours are within 20 days and agree with each other within 0.15. These are cloud, shadow or haze.
  1. CUT AND REGROWTH: from a reading of 0.45 or more, NDVI falls by 0.20 or more within 15 days; readings
     at least 0.15 below the starting value span 5 days or more (so a haze episode of one or two scenes is
     not a cut); and at least two readings in the 45 days after the low are 0.15 or more above it.
  2. ABRUPT END: from 0.50 or more, a fall of 0.35 or more within 10 days, with no regrowth as in rule 1.
     Before 1 April this is called a green harvest (the crop was removed while green); from 1 April it is
     called a fast end, which NDVI alone cannot tell apart from quick ripening in hot weather.
A fall in November is the end of the previous crop and is not counted for the winter-crop points
(events must start on or after 1 December for the test group).

The thresholds were fixed after a first look at the series (the 5-day span was added when a regional
haze episode on 4-5 April 2026 showed up as false cuts), so they are not blind. The script also lists
that episode: points whose NDVI is 0.15 or more below both the reading before and the reading after
on 4 or 5 April.
Usage: python forage_test.py [--series data/forage_series.json] [--detail]"""
import argparse, csv, json, os
from datetime import date

here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--series", default=os.path.join(here, "data", "forage_series.json"))
ap.add_argument("--detail", action="store_true", help="print every event")
a = ap.parse_args()
sample = list(csv.DictReader(open(os.path.join(here, "data", "forage_sample.csv"))))
series = json.load(open(a.series))
T0 = date(2025, 11, 1)
day = lambda d: (date.fromisoformat(d) - T0).days
DEC1, APR1 = day("2025-12-01"), day("2026-04-01")


def despike(s):
    s = list(s); n = 0; changed = True
    while changed:
        changed = False
        for i in range(1, len(s) - 1):
            (da, va), (db, vb), (dc, vc) = s[i - 1], s[i], s[i + 1]
            if db - da <= 20 and dc - db <= 20 and abs(va - vc) < 0.15 and (
                    (va - vb >= 0.15 and vc - vb >= 0.15) or (vb - va >= 0.15 and vb - vc >= 0.15)):
                del s[i]; n += 1; changed = True
                break
    return s, n


def events(s, start):
    out, i = [], 0
    while i < len(s) - 1:
        d0, v0 = s[i]
        if d0 < start or v0 < 0.45:
            i += 1; continue
        w15 = [k for k in range(i + 1, len(s)) if s[k][0] - d0 <= 15]
        j = min(w15, key=lambda k: s[k][1]) if w15 else None
        if j is not None and v0 - s[j][1] >= 0.20:
            dj, vj = s[j]
            low = [d for d, v in s if d0 < d <= dj + 12 and v <= v0 - 0.15]
            up = [v for d, v in s if dj < d <= dj + 45 and v >= vj + 0.15]
            if low and max(low) - min(low) >= 5 and len(up) >= 2:
                out.append(("cut", d0, v0, dj, vj)); i = j; continue
            w10 = [k for k in w15 if s[k][0] - d0 <= 10]
            j2 = min(w10, key=lambda k: s[k][1]) if w10 else None
            if j2 is not None and v0 >= 0.50 and v0 - s[j2][1] >= 0.35 and len(up) < 2:
                out.append(("green_harvest" if d0 < APR1 else "fast_end", d0, v0, s[j2][0], s[j2][1])); i = j2; continue
        i += 1
    return out


def upper95(k, n):                      # Clopper-Pearson upper limit (two-sided 95%), by bisection
    from math import comb
    if k == n: return 1.0
    lo, hi = k / n, 1.0
    for _ in range(60):
        p = (lo + hi) / 2
        if sum(comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(k + 1)) > 0.025: lo = p
        else: hi = p
    return hi


iso = lambda d: date.fromordinal(T0.toordinal() + d).isoformat()[5:]
res, haze = {}, []
for r in sample:
    raw = [(day(d), v) for d, v in series[r["id"]]["obs"]]
    for i in range(1, len(raw) - 1):
        if iso(raw[i][0]) in ("04-04", "04-05") and raw[i - 1][1] - raw[i][1] >= 0.15 and raw[i + 1][1] - raw[i][1] >= 0.15 \
                and iso(raw[i - 1][0]) not in ("04-04", "04-05"):
            haze.append(r["id"]); break
    s, n = despike(raw)
    res[r["id"]] = (len(raw), n, events(s, DEC1 if r["group"] == "test" else 0))

for grp, title in (("test", "winter-crop points"), ("control", "perennial points (control)")):
    ids = [r["id"] for r in sample if r["group"] == grp]; n = len(ids)
    nobs = sorted(res[i][0] for i in ids)
    print(f"{title}: {n}; clear dates per point {nobs[0]}-{nobs[-1]}, median {nobs[n // 2]}; "
          f"one-date outliers removed: {sum(res[i][1] for i in ids)}")
    has = lambda kind: [i for i in ids if any(e[0] == kind for e in res[i][2])]
    cut, gh, fe = has("cut"), has("green_harvest"), has("fast_end")
    gh = [i for i in gh if i not in cut]; fe = [i for i in fe if i not in cut and i not in gh]
    ncut = {i: sum(e[0] == "cut" for e in res[i][2]) for i in cut}
    print(f"  cut and regrowth: {len(cut)} of {n} ({len(cut) / n:.0%}, 95% upper limit {upper95(len(cut), n):.0%})  "
          + " ".join(f"{i}x{ncut[i]}" for i in cut))
    print(f"  green harvest before 1 April, no regrowth: {len(gh)}  " + " ".join(gh))
    print(f"  cut or green harvest: {len(cut) + len(gh)} of {n} ({(len(cut) + len(gh)) / n:.0%}, "
          f"95% upper limit {upper95(len(cut) + len(gh), n):.0%})")
    print(f"  fast end from 1 April (not counted as forage): {len(fe)}  " + " ".join(fe))
    print(f"  none of these: {n - len(cut) - len(gh) - len(fe)}")
    if a.detail:
        for i in ids:
            for k, d0, v0, d1, v1 in res[i][2]:
                print(f"    {i} {k:<13} {iso(d0)} {v0:.2f} -> {iso(d1)} {v1:.2f}")
print(f"haze episode of 4-5 April 2026 (one-scene dip of 0.15 or more): {len(haze)} points  " + " ".join(haze))
