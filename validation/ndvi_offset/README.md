# Sentinel-2 +1000 offset on Planetary Computer: open question

**Status: undecided (7 Nov 2026).** The app's NDVI has not been changed.

## Background
Since ESA processing baseline 04.00 (January 2022), Sentinel-2 L2A reflectance values carry an additive offset of +1000 (`BOA_ADD_OFFSET`). A true reflectance of 0 is stored as 1000.
- In a normalized difference such as NDVI, the offset doesn't cancel. It inflates the denominator and pulls NDVI toward 0.
- The more vegetation, the larger the effect.
- With the offset removed, NDVI is `(B08−B04)/(B08+B04−2000)`.

## Evidence that Planetary Computer serves the offset
These are point reads through Planetary Computer's `/item/point` endpoint, made on 7 Nov 2026:
- Open sea water reads B08 ≈ 1,200. Near-infrared reflectance of water is close to 0.
- The same bare-soil spot reads about 1,000 higher in 2026 scenes than in 2021 scenes. The 2021 scenes predate baseline 04.00.
- The 2025-26 scenes read were on baselines 05.11–05.12.

As an illustration (arithmetic, not a measured read), a dense crop reading B04 = 1,150 and B08 = 4,300 gives:
- raw NDVI = 0.58;
- corrected NDVI = 0.91.

## Evidence the other way
The app's code (`index.html`, at the definition of `NDVI_EXPR`) records an earlier check:
- On one test field, Copernicus Browser's Statistical Info gave about 0.51–0.56.
- That matched the uncorrected formula.
- The corrected formula gave 0.79.
- The app therefore uses `(B08−B04)/(B08+B04)`.

## What depends on it
- **Iraq Farms Health's field health classes** use the uncorrected NDVI. The Poor/Fair/Good thresholds (0.20 / 0.45) were set on that scale, so correcting the formula would mean re-setting them.
- **The accuracy labels** ([`../accuracy_south_2026`](../accuracy_south_2026)) use the corrected NDVI, and the labelling rules' thresholds are on that scale. A fresh `fetch_curves.py` run records both values for every month.

## Proposed test
1. Read Copernicus Browser's NDVI (Statistical Info) for one field on one date.
2. Compute both formulas from Planetary Computer for the same field and the same scene.
3. Whichever formula matches Copernicus Browser's documented harmonized values settles it.
