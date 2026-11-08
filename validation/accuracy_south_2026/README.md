# Accuracy assessment of the 2025-26 crop map: southern tiles

A stratified random accuracy assessment of the Iraq Farms Health winter-cereal map for the 2025-26 season, following Olofsson et al. (2014). The protocol was written down before any point was labelled. This folder holds everything needed to repeat it: the sample, the reference curves, the labels with their reasons, and the scripts.

**Headline (95% intervals, unclear points left out):**

| Map product | Map area | User's accuracy (winter crop) | Producer's accuracy | Overall accuracy |
|---|---|---|---|---|
| Confident cereal (the map's default) | 1.41 Mha | **0.96** (0.92–0.99) | **0.70** (0.61–0.79) | 0.94 |
| Confident + doubtful cereal ("top crop") | 2.11 Mha | 0.79 (0.74–0.84) | 0.86 (0.76–0.96) | 0.93 |

**Winter-crop area in the southern tiles:** 1.93 Mha (95% CI 1.69–2.17 Mha). For comparison, the map has 1.41 Mha of confident cereal there.

The reference label is *winter crop*, not *cereal*. Because of that, the user's accuracy is an upper bound for cereal, and so is the area figure (see [Limits](#limits)).

---

## 1. What was assessed

- **Map:** `crops/2026/` exactly as published on 7 Nov 2026 at 12:54 UTC, which is repository commit `969b4aa`.
  - Later publishes change `crops/2026/`. The north re-run, for example, replaces northern tiles.
  - To reproduce the results, first run `git checkout 969b4aa -- crops/2026`.
- **Population:** every map pixel in the finished tiles of the main run (`iraq_winter2026`) whose centre lies south of 34.8°N, clipped to Iraq's boundary (`boundaries.geojson`).
  - A tile's centre is the middle of its bounding box.
  - That gives 67 tiles and 10,515,621 ha.
  - The north re-run does not touch these tiles, so the result stays valid for them.
- **Pixel codes:**
  - 0 = not cropland.
  - 1 + class index = confident.
  - +100 = less sure.
  - +200 = doubtful cereal, meaning cereal is the top crop but P(wheat)+P(barley) < 70%.

## 2. Strata and sample

| Stratum | Pixel codes | Area (ha) | Sample size |
|---|---|---|---|
| confident cereal | wheat, barley, rye or oats, code < 200 | 1,406,717 | 100 |
| doubtful cereal | wheat, barley, rye or oats, code > 200 | 699,965 | 75 |
| other crop | any other crop class except `no_crop` | 166,783 | 50 |
| no crop | `no_crop` | 286,560 | 50 |
| not cropland | 0 | 7,955,595 | 100 |

**How the points were drawn:**
- Within each stratum, the stratum's points are first shared out among the map's cells by a multinomial draw weighted by the stratum's area in each cell.
- Within each cell, the points are then placed on uniform random pixels of that stratum.
- Areas are ground areas: a Web Mercator pixel is scaled by cos²(latitude).
- The seed is `20261107`.
- The points are then shuffled and numbered S001–S375. The numbering therefore says nothing about the class.
- The sample uses no field polygons. That avoids a bias toward large fields, and it means not-cropland pixels get sampled too.

**Where the results go:**
- `data/points.csv` holds id, lat and lon. It is the only file the labelling step reads.
- `data/map_key.csv` maps each id to its stratum, pixel code and cell file.

## 3. Reference labels (blind to the map)

Each point is labelled from its own Sentinel-2 L2A history, read as a single 10 m pixel through Microsoft Planetary Computer, before the map key is opened.

**Monthly values:**
- The window is Sep 2025 – Aug 2026, with one value per month.
- For each month, up to 4 scenes are tried, clearest first by scene cloud cover.
- The first scene whose pixel is clear by Sentinel-2's scene classification is used. Clear means SCL 4 vegetation, 5 bare soil, 6 water or 7 unclassified.

**NDVI is computed two ways:**
- Raw: `(B08−B04)/(B08+B04)`.
- Corrected: `(B08−B04)/(B08+B04−2000)` on processing baseline ≥ 04.00. Those scenes carry a +1000 offset that Planetary Computer does not remove; see [`../ndvi_offset`](../ndvi_offset).
- **The rules use the corrected value.**

**Rules, applied in order.** In these rules, W = highest value Dec–Apr, S = highest Jun–Sep, and B = lowest of all months.

0. Fewer than 6 clear months → **unclear**.
1. **water:** NDVI < 0 in at least half of the months.
2. **perennial** (orchard, palms, reeds, alfalfa): NDVI ≥ 0.35 in at least 10 months, with no month below 0.25.
3. **winter crop:** all of the following must hold.
   - W ≥ 0.40 and W − B ≥ 0.25.
   - A month in Sep–Dec, before the peak, is at least 0.20 below W. This is the green-up.
   - A month in Apr–Jul, after the peak, is at most B + 0.5·(W − B). This is the dry-down.
4. **summer only:** W < 0.30 and S ≥ 0.40.
5. **no crop:** every month < 0.30.
6. **unclear:** anything else. This includes a weak winter peak (0.30–0.40) and 2 or more missing months in Dec–Apr.

**Results of labelling:**
- The rules labelled 318 points.
- The 57 "unclear" points each got a manual look at the curve, still blind to the map. The outcome was:
  - 9 winter crop;
  - 19 no crop;
  - 15 summer only;
  - 5 perennial;
  - 9 still unclear.
- `data/labels_final.csv` keeps the rule label, the rule's reason, the final label and the reviewer's note for every point.

## 4. Estimation

- Uses the Olofsson et al. (2014) estimators for a stratified sample, with the stratum area weights from `data/design.json`.
- Reports overall accuracy, user's and producer's accuracy, and the error-adjusted winter-crop area with 95% confidence intervals. In every case the map side is "confident cereal" (or confident + doubtful) and the reference side is "winter crop".
- Unclear points are left out of the headline. They are also counted all one way and all the other way, as bounds. Doing so changes no figure by more than 0.02 or 42,000 ha.
- As a check, a 4,000-draw stratified bootstrap (`bootstrap.py`, seed 20261107) agrees with the analytic intervals.

**Winter crop by map class (unclear left out):**

| Map class | Points with a winter crop | Winter-crop area there |
|---|---|---|
| confident cereal | 95 of 99 (96%) | 1.35 Mha |
| doubtful cereal | 31 of 69 (45%) | 0.31 Mha |
| other crop | 26 of 50 (52%) | 0.09 Mha |
| no crop | 3 of 48 (6%) | 0.02 Mha |
| not cropland | 2 of 100 (2%) | 0.16 Mha |

**Reading:**
- **Commission is low.** Where the default map says cereal, a winter crop almost always grew.
- **Omission is the main error.** About 30% of the winter-crop area falls outside the confident-cereal class.
  - Most of it is in doubtful cereal (the 70% rule) and in "other crop" (cereal-shaped curves mapped as vegetables or pulses). The field checks found the same; see [`../field_checks`](../field_checks).
- **The largest single uncertainty in the area figure** is the 0.16 Mha in "not cropland". It comes from 2 points in a very large class.

## 5. Reproduce it

**Requirements:** Python ≥ 3.9 with `numpy rasterio shapely>=2 pyproj requests`, for example via `pip install numpy rasterio shapely pyproj requests`.

The commands below run from this folder.

```bash
git checkout 969b4aa -- ../../crops/2026      # the map that was assessed (restore later with: git checkout HEAD -- ../../crops/2026)

# A. Sample: rebuilds data/strata_area.json, points.csv, map_key.csv, design.json (about 2 min)
python strata_area.py --out /tmp/redo
python draw_sample.py --out /tmp/redo
cmp /tmp/redo/points.csv data/points.csv && cmp /tmp/redo/map_key.csv data/map_key.csv   # identical

# B. Reference curves from Planetary Computer (blind: reads points.csv only; about 1 h for 375 points)
python fetch_curves.py --out data/curves_fetched.json
python compare_curves.py data/curves_fetched.json        # against the archived curves

# C. Labels, estimates, bootstrap
python label_rules.py data/curves.json                  # archived curves -> same 318 rule labels
python estimate.py data/labels_final.csv
python bootstrap.py data/labels_final.csv
```

**Expected outputs:**
- `expected_output.txt` holds the expected output of `estimate.py` and `bootstrap.py`.
- Step A reproduces the sample byte for byte. This was checked on 7 Nov 2026.

**On the curves:**
- `data/curves.json` holds the curves that were actually used. These are corrected NDVI for each point and month.
- Raw NDVI, scene dates and SCL values were not archived for this run. A fresh `fetch_curves.py` run records all of them.
- Planetary Computer can reprocess scenes, so a fresh fetch may differ slightly. `compare_curves.py` reports by how much, and whether any rule label changes.
- `fetch_curves.py` is a Python port of the browser function that produced the archived curves; see its header.
- **Port checked 8 Nov 2026:** `fetch_curves.py --only S001,S002,S003,S010` in Colab, then `compare_curves.py`. All 48 months were identical to the archived curves (maximum difference 0.000), and all 4 rule labels were the same.

## 6. Independent check

`data/spotcheck_blind.csv` holds a random 10% of the points (38) with their corrected-NDVI curves and no map class.

**How to use it:**
1. A second person labels them with the rules in section 3, filling in the `your_label` column without opening `map_key.csv` or `labels_final.csv`.
2. Compare their labels with `labels_final.csv`.

This had not been done when the results were published.

## Limits

- **Winter crop, not cereal.** A Sentinel-2 curve can't separate wheat from barley, or cereal from winter pulses, vegetables or fodder. So:
  - User's accuracy against "winter crop" is an upper bound on user's accuracy for cereal.
  - The winter-crop area is an upper bound on the cereal area.
- Turning these into cereal figures needs very-high-resolution imagery or field visits on a subsample.
- **One labeller.** The labels were made by one labeller, Claude, working for the project. The rules are written so that someone else can apply them; section 6 is the test of that.
- **South only.** The northern tiles are being re-run with a later season; see [`../season_pilot`](../season_pilot). They will be assessed the same way after that run.
- **One pixel per point.** At 10 m, a pixel on a field edge mixes neighbours. This affects the map and the reference alike.

## Files

| File | What it is |
|---|---|
| `common.py` | Settings (seed, sample sizes, 34.8°N rule) and the pixel-code → stratum function |
| `strata_area.py` | Step A1: area of each stratum, total and per map cell |
| `draw_sample.py` | Step A2: the stratified random sample |
| `fetch_curves.py` | Step B: Sentinel-2 history of each point (Planetary Computer) |
| `compare_curves.py` | Compares a fresh fetch with the archived curves |
| `label_rules.py` | Step C1: the written labelling rules |
| `estimate.py` | Step C2: Olofsson et al. (2014) estimators |
| `bootstrap.py` | Check: stratified bootstrap |
| `data/points.csv` | 375 points: id, lat, lon |
| `data/map_key.csv` | Map stratum, pixel code and cell file of each point |
| `data/design.json` | Seed, sample sizes, stratum areas |
| `data/strata_area.json` | Stratum areas per map cell (input to the draw) |
| `data/curves.json` | Archived reference curves (corrected NDVI, Sep 2025 – Aug 2026) |
| `data/curves_ndvi_corrected.csv` | The same curves as a table |
| `data/labels_final.csv` | Rule label and reason, final label, manual-review note |
| `data/spotcheck_blind.csv` | 38 points for an independent labeller |

**Reference:** Olofsson, P., Foody, G. M., Herold, M., Stehman, S. V., Woodcock, C. E., & Wulder, M. A. (2014). Good practices for estimating area and assessing accuracy of land change. *Remote Sensing of Environment*, 148, 42–57.
