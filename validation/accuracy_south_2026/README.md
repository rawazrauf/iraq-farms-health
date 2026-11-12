# Accuracy assessment of the 2025-26 crop map: southern tiles

A stratified random accuracy assessment of the Iraq Farms Health winter-cereal map for the 2025-26 season, following Olofsson et al. (2014). The protocol was written down before any point was labelled. This folder holds everything needed to repeat it: the sample, the reference curves, the labels with their reasons, and the scripts.

**Headline (575 points: the 375 of phase 1 plus a 200-point top-up of the "not cropland" stratum, section 7; 95% intervals, unclear points left out):**

| Map product | Map area | User's accuracy (winter crop) | Producer's accuracy | Overall accuracy |
|---|---|---|---|---|
| Confident cereal (the map's default) | 1.41 Mha | **0.96** (0.92–0.99) | **0.71** (0.65–0.77) | 0.94 |
| Confident + doubtful cereal ("top crop") | 2.11 Mha | 0.79 (0.74–0.84) | 0.87 (0.82–0.93) | 0.93 |

**Winter-crop area in the southern tiles:** 1.91 Mha (95% CI 1.75–2.06 Mha). For comparison, the map has 1.41 Mha of confident cereal there.

Phase 1 alone (375 points, published 7 Nov 2026) gave the same picture with wider intervals: producer's accuracy 0.70 (0.61–0.79) and an area of 1.93 Mha (1.69–2.17). See sections 4 and 7.

The reference label is *winter crop*, not *cereal*. Because of that, the user's accuracy is an upper bound for cereal, and so is the area figure (see [Limits](#limits)).

Two things to keep in mind when reading these figures, both set out below:
- **The reference comes from the same satellite as the map.** The labels are read from each point's Sentinel-2 curve; the map is made from Sentinel-2 (with Sentinel-1 and weather data). They are not independent, so agreement may be somewhat overstated (see [Limits](#limits)).
- **The two rows are two settings of one map, not two maps.** The 70% confidence rule trades missed crop for wrong crop (section 8).

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

*This section gives the phase-1 results (375 points), as published on 7 Nov 2026. The headline at the top now pools them with the phase-2 top-up; see section 7.*

- Uses the Olofsson et al. (2014) estimators for a stratified sample, with the stratum area weights from `data/design.json`.
- Reports overall accuracy, user's and producer's accuracy, and the error-adjusted winter-crop area with 95% confidence intervals. In every case the map side is "confident cereal" (or confident + doubtful) and the reference side is "winter crop".
- Unclear points are left out of the headline. They are also counted all one way and all the other way, as bounds. In phase 1, doing so changes no figure by more than 0.02 or 42,000 ha (the pooled bounds are wider; section 7).
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

# D. Phase 2: the not-cropland top-up (section 7)
python topup_draw.py                                     # same 200 points, byte for byte
python fetch_curves.py --points data/topup_points.csv --out data/topup_curves_new.json   # or fetch_topup.ipynb
python topup_review.py final                             # final labels from the archived blind review
python estimate.py --topup
python bootstrap.py --topup
python label_noise.py                        # section 9: effect of the hand labels' repeatability
```

**Expected outputs:**
- `expected_output.txt` holds the expected output of `estimate.py`, `bootstrap.py` and `label_noise.py`.
- Step A reproduces the sample byte for byte. This was checked on 7 Nov 2026.

**On the curves:**
- `data/curves.json` holds the curves that were actually used. These are corrected NDVI for each point and month.
- Raw NDVI, scene dates and SCL values were not archived for this run. A fresh `fetch_curves.py` run records all of them.
- Planetary Computer can reprocess scenes, so a fresh fetch may differ slightly. `compare_curves.py` reports by how much, and whether any rule label changes.
- `fetch_curves.py` is a Python port of the browser function that produced the archived curves; see its header.
- **Port checked 8 Nov 2026:** `fetch_curves.py --only S001,S002,S003,S010` in Colab, then `compare_curves.py`. All 48 months were identical to the archived curves (maximum difference 0.000), and all 4 rule labels were the same.
- **Out-of-range values (found 8 Nov 2026).** The curves were fetched with an unclipped formula, (B08 − B04) / (B08 + B04 − 2000). When the red band is near or below the 1,000 offset, that gives values near or above 1, which is not physical.
  - In `data/curves.json`, 13 of 4,498 months read above 0.95, and 8 of those above 1.0: S003, S037, S047, S077, S124, S151, S166 (2 months), S275, S338, S345 (2 months) and S351.
  - **Effect on the labels:** none. Capping those months at 1.0 or at 0.95 gives exactly the same rule labels for all 375 points.
  - **Effect if the months are dropped instead:** one label changes. S166 (map: not cropland) goes from perennial to unclear. With unclear points left out, overall accuracy goes from 0.940 to 0.939, the winter-crop area from 1.928 to 1.930 Mha, and user's and producer's accuracy are unchanged at 0.96 and 0.70.
  - **The published results therefore stand.** Since 8 Nov, `fetch_curves.py` clips each band at the offset before removing it, as the app does: NDVI = (N − R) / (N + R + 1) with R = max(B04 − 1000, 0) and N = max(B08 − 1000, 0). A fresh fetch of the southern points will differ from the archive in those 13 months, and elsewhere only by a few thousandths (from the +1 in the denominator). Later assessments, including the north, use the clipped formula.

## 6. Independent check

`data/spotcheck_blind.csv` holds a random 10% of the points (38) with their corrected-NDVI curves and no map class.

**How to use it:**
1. A second person labels them with the rules in section 3, filling in the `your_label` column without opening `map_key.csv` or `labels_final.csv`.
2. Compare their labels with `labels_final.csv`.

This had not been done when the results were published.

## 7. Top-up of the "not cropland" stratum (phase 2)

**Declared on 8 Nov 2026, before any top-up curve was fetched or labelled.** The points were drawn the same day (the draw uses no labels); nothing below was changed after seeing results.

**Why:**
- "Not cropland" covers 76% of the southern area but had 100 of the 375 points.
- 2 of those 100 points were winter crop. Each therefore stands for about 80,000 ha, and these two points drive most of the width of the area and producer's-accuracy intervals.
- Projection, if the new points look like the old ones: 200 more points in this stratum would narrow the winter-crop area interval from ±0.24 to about ±0.16 Mha, and producer's accuracy from ±0.09 to about ±0.06. Spreading the same effort over all strata would barely help.

**Sample:**
- 200 extra points, all in the "not cropland" stratum (pixel code 0), in the same population: the 67 southern main-run tiles of the map as published at commit `969b4aa`, clipped to Iraq. The crop cells have not changed since.
- Same two-step draw as phase 1 (multinomial over map cells by the stratum's area, then uniform pixels), seed `20261108`. Pixels used in phase 1 are left out.
- `topup_draw.py` writes `data/topup_points.csv` (T001–T200: id, lat, lon only), `data/topup_map_key.csv` and `data/topup_design.json`. Re-running it gives byte-identical files.

**Reference curves:** `fetch_curves.py --points data/topup_points.csv`, with the clipped NDVI formula (see "On the curves" in section 5).

**Labels:**
- The same rules as section 3, applied by `label_rules.py`.
- Points the rules call unclear get the same manual look as in phase 1. But every top-up point is "not cropland", so a reviewer who knows a curve is a top-up point is not blind to the map.
- To keep the review blind, `topup_review.py pack` mixes the rule-unclear top-up curves with the 57 phase-1 rule-unclear curves, shuffles them under new ids (seed `20261109`) and hides which is which. The reviewer labels them all without the key.
- The phase-1 curves in the pack are an agreement check only. Phase-1 final labels are not changed; the agreement is reported.

**Estimation:**
- Within the stratum, both phases are independent uniform draws, so the 300 points are pooled as one sample of the stratum (n = 300). The other strata and all stratum areas are unchanged.
- `estimate.py --topup` and `bootstrap.py --topup` give the pooled figures, with unclear points left out (headline) and counted both ways (bounds), as in section 4.
- Both sets of figures will be published: phase 1 alone (section 4, unchanged) and phase 1 + top-up. The pooled figures become the headline, whatever they show.
- No further top-up will be decided from these results. The northern assessment will give "not cropland" more points from the start.

**Results (8 Nov 2026):**
- **Curves:** all 200 points fetched (Colab, `fetch_topup.ipynb`); 198 with 12 clear months, 2 with 11. Saved as `data/topup_curves.json`.
- **Rule labels:** 168 no crop, 7 perennial, 5 water, 3 summer only, 2 winter crop, 15 unclear (`data/topup_labels_rule.csv`).
- **Blind review:** the 15 unclear top-up curves were shuffled with the 57 phase-1 unclear curves (72 in all). The criteria were written down before the pack was opened (`data/review_criteria.txt`). Outcome for the top-up curves: 5 no crop, 1 perennial, 1 winter crop, 8 still unclear.
- **Final top-up labels:** 173 no crop, 8 perennial, 5 water, 3 summer only, 3 winter crop, 8 unclear (`data/topup_labels_final.csv`).
- **The stratum, pooled:** 5 of 292 labelled "not cropland" points are winter crop (1.7%), against 2 of 100 in phase 1.

**Pooled estimates** (`estimate.py --topup`; the analytic intervals and a 4,000-draw bootstrap agree):

| | Phase 1 (375 points) | Pooled (575 points) |
|---|---|---|
| Overall accuracy (confident cereal) | 0.940 ± 0.023 | 0.942 ± 0.015 |
| User's accuracy (confident cereal) | 0.960 ± 0.039 | 0.960 ± 0.039 |
| Producer's accuracy (confident cereal) | 0.700 ± 0.086 | 0.709 ± 0.056 |
| Producer's accuracy (confident + doubtful) | 0.863 ± 0.099 | 0.874 ± 0.057 |
| Winter-crop area | 1.93 ± 0.24 Mha | 1.91 ± 0.16 Mha |

The intervals narrowed by about a third, as projected; the estimates hardly moved.

**Unclear points.** 8 top-up points stay unclear, and in this stratum each stands for about 26,500 ha. Counted all as winter crop, the area would be 2.16 Mha and producer's accuracy 0.63; counted all as not, 1.86 Mha and 0.72. The bounds are wider than in phase 1 for that reason.

**Agreement of the re-review with phase 1.** The 57 phase-1 curves in the pack got the same label as in phase 1 in 31 cases (54%). Most differences are between "summer only" and "unclear", which doesn't matter here. For the winter-crop question, 6 of 57 differ, all in one direction: S005, S102, S172, S289, S305 and S345 were not winter crop (or unclear) in phase 1 and are winter crop in the re-review.
- As declared, the phase-1 labels are not changed.
- **Sensitivity:** with the re-review labels for those 57 points, the pooled producer's accuracy would be 0.685 and the area 1.97 Mha. Both are inside the intervals above.
- **What it means:** the manual look at borderline curves is the least repeatable step in this assessment. The rules themselves are deterministic. An independent labeller (section 6) is the way to measure this properly.

## 8. The 70% rule is a choice between two kinds of error

The map misses about 0.56 Mha of the winter crop (29% of 1.91 Mha). Where that area sits, from the pooled sample (`estimate.py --topup`):

| Map class of the missed winter crop | Points with a winter crop | Area |
|---|---|---|
| doubtful cereal (cereal is the top crop, but below the 70% rule) | 31 of 69 | 0.31 Mha |
| not cropland | 5 of 292 | 0.14 Mha |
| other crop | 26 of 50 | 0.09 Mha |
| no crop | 3 of 48 | 0.02 Mha |

- **More than half of the missed area was seen by the model and set aside by the 70% rule.** It is in the data files as "doubtful cereal" (code +200) and can be switched on in the crop page's legend.
- **The rule moves the map along one trade-off:**

  | Setting | Of what the map marks, a winter crop grew on | Of the winter crop, the map marks |
  |---|---|---|
  | Confident cereal only (default) | 96% (92–99%) | 71% (65–77%) |
  | Confident + doubtful cereal | 79% (74–84%) | 87% (82–93%) |

  The default favours being right where the map says cereal; the other setting favours finding more of the crop. Neither is "the accuracy of the map" on its own. Which to use depends on the purpose: showing a farmer "wheat or barley grew here" calls for the first; estimating area calls for the error-adjusted estimate (1.91 Mha), which does not depend on the setting.
- **The "not cropland" figure rests on 5 points**, each standing for about 27,000 ha, so it is the least certain line of the table.
- The rule itself will be revisited once the north is assessed.

## 9. How much could the hand labels move the results?

The manual look at borderline curves is the least repeatable step (section 7). `label_noise.py` measures what that could do to the estimates.

- **What it does.** 72 of the 575 points were labelled by hand. The 57 that were labelled twice give a table of how often a curve put in one state (winter crop / not / unclear) was put in another the second time. The script redraws every hand label from that table (both rounds pooled, so neither is treated as the truth), re-estimates, and repeats 10,000 times. The 503 rule labels never change. A second pass also resamples the points, to combine label noise with sampling error.
- **The table** (57 curves, round 1 → round 2): not → not 21, not → unclear 17, winter → winter 9, unclear → winter 5, unclear → not 2, unclear → unclear 2, not → winter 1. Between the two definite answers there is 1 change in 57; the rest move in or out of "unclear".
- **Result** (confident cereal):

  | | Headline | Label noise only (median, 95%) | Label noise + sampling (95%) |
  |---|---|---|---|
  | User's accuracy | 0.960 | 0.950 (0.940–0.960) | 0.908–0.990 |
  | Producer's accuracy | 0.709 | 0.690 (0.663–0.714) | 0.629–0.751 |
  | Overall accuracy | 0.942 | 0.936 (0.929–0.943) | 0.918–0.952 |
  | Winter-crop area | 1.91 Mha | 1.94 Mha (1.87–2.02) | 1.77–2.14 Mha |

- **Reading.** Label noise shifts the estimates a little, towards more winter crop and a slightly lower producer's accuracy (0.69 against 0.71), because curves first called unclear or "not" were more often called winter crop the second time than the reverse. It widens the intervals modestly: the area interval becomes 1.77–2.14 Mha against 1.75–2.06. No conclusion changes. The headline keeps the declared labels and intervals; these figures are the fuller statement of uncertainty.
- **What it does not cover.** Both rounds were by the same labeller, so this measures repeatability, not correctness. An independent labeller (section 6) and independent imagery (Limits) are still needed.

## Limits

- **The reference is not independent of the map.** Olofsson et al. (2014) ask for reference data of higher quality than the map and independent of it. Here the reference labels are read from Sentinel-2 curves, and the map is WorldCereal's model run on Sentinel-2 (with Sentinel-1 radar and weather data). The method differs: a person and written rules reading a whole year, including the months after the season, against a model. But the sensor is shared, so anything that distorts Sentinel-2 at a point (dust, a cloud gap in a key month, an unusual season) can push the map and the label the same way, and agreement may be overstated. What would fix it: checking a subsample against very-high-resolution imagery, and comparing the area estimates with official statistics by governorate. Sentinel-1 would not help, because the map already uses it.

- **Winter crop, not cereal.** A Sentinel-2 curve can't separate wheat from barley, or cereal from winter pulses, vegetables or fodder. So:
  - User's accuracy against "winter crop" is an upper bound on user's accuracy for cereal.
  - The winter-crop area is an upper bound on the cereal area.
- Turning these into cereal figures needs very-high-resolution imagery or field visits on a subsample.
- **One labeller.** The labels were made by one labeller, Claude, working for the project. The rules are written so that someone else can apply them; section 6 is the test of that.
- **The manual look is not very repeatable.** In the phase-2 blind re-review, the same labeller agreed with his own phase-1 labels on 54% of the borderline curves, and on 51 of 57 for the winter-crop question (section 7). The rule labels, which cover 85% of all points, are fully repeatable. Section 9 puts numbers on what this could do to the estimates.
- **Fodder cut several times a winter is counted as a winter crop.** The rules look at one reading per month, which cannot show the repeated cuts of berseem clover. Alfalfa mostly falls under "perennial". How much fodder is inside the winter-crop figure is not known; reading every clear scene (every 5 days) on a subsample would show it.
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
| `label_noise.py` | Check: effect of the hand labels' repeatability on the estimates (section 9) |
| `topup_draw.py` | Phase 2: the 200-point "not cropland" top-up (section 7) |
| `topup_review.py` | Phase 2: rule labels, blind review pack, final labels |
| `fetch_topup.ipynb` | Phase 2: Colab notebook that runs `fetch_curves.py` on the top-up points |
| `data/points.csv` | 375 points: id, lat, lon |
| `data/map_key.csv` | Map stratum, pixel code and cell file of each point |
| `data/design.json` | Seed, sample sizes, stratum areas |
| `data/strata_area.json` | Stratum areas per map cell (input to the draw) |
| `data/curves.json` | Archived reference curves (corrected NDVI, Sep 2025 – Aug 2026) |
| `data/curves_ndvi_corrected.csv` | The same curves as a table |
| `data/labels_final.csv` | Rule label and reason, final label, manual-review note |
| `data/topup_points.csv` | 200 top-up points: id, lat, lon |
| `data/topup_map_key.csv` | Map stratum, pixel code and cell file of each top-up point |
| `data/topup_design.json` | Top-up seed, size and points per cell |
| `data/topup_curves.json` | Top-up reference curves (clipped corrected NDVI, Sep 2025 – Aug 2026, with raw bands and scene ids) |
| `data/topup_labels_rule.csv` | Rule label and reason for each top-up point |
| `data/review_criteria.txt` | Criteria for the manual look, written before the blind pack was opened |
| `data/review_blind.csv` | The blind review pack: anonymous curves with the reviewer's labels and notes |
| `data/review_key.csv` | Which point each anonymous curve belongs to |
| `data/topup_labels_final.csv` | Final top-up labels (rule label, or the blind review where the rules said unclear) |
| `data/spotcheck_blind.csv` | 38 points for an independent labeller |

**Reference:** Olofsson, P., Foody, G. M., Herold, M., Stehman, S. V., Woodcock, C. E., & Wulder, M. A. (2014). Good practices for estimating area and assessing accuracy of land change. *Remote Sensing of Environment*, 148, 42–57.
