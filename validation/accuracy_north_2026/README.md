# Accuracy assessment of the 2025-26 crop map: northern tiles

A stratified random accuracy assessment of the northern part of the Iraq Farms Health winter-cereal map for the 2025-26 season. It follows the southern assessment ([`../accuracy_south_2026`](../accuracy_south_2026)) and Olofsson et al. (2014), with the changes listed in section 3.

**Status:** protocol written and sample drawn on 27 Nov 2026, **before any northern reference curve was fetched or labelled.** Nothing in sections 1–6 is to be changed after the curves come in; any later change is added as a dated note and reported both ways.

**Results (27 Nov 2026; second labeller's check added 28 Nov, section 8):** the curve labels alone could not separate rain-fed crops from the spring green-up of natural grassland, so the reference was amended twice after the key was opened (section 7). With winter crop counted only on farmed land (amendment 2; unclear points left out; 95% intervals):

| Map product | Map area | User's accuracy (winter crop) | Producer's accuracy | Overall accuracy |
|---|---|---|---|---|
| Confident cereal (the map's default) | 1.71 Mha | **0.76** (0.67–0.84) | **0.52** (0.47–0.57) | 0.81 |
| Confident + doubtful cereal ("top crop") | 3.16 Mha | 0.61 (0.55–0.68) | 0.77 (0.72–0.82) | 0.78 |

**Winter crop on farmland in the northern tiles:** 2.50 Mha (95% CI 2.24–2.75 Mha; 2.41–2.79 Mha with the unclear points counted either way), against 1.71 Mha of confident cereal mapped. Kurdistan Region 0.77 Mha (UA 0.83, PA 0.57); federal north 1.73 Mha (UA 0.72, PA 0.50). The south, for comparison: UA 0.96, PA 0.71.

**The reference is probably conservative.** On the 57 spot-check points a second labeller found winter crop on farmland at 21 points and Claude at 12 (they agree on 11 of Claude's 12). With the second labeller's answers on those points: UA 0.80, PA 0.52, 2.64 Mha. So the area and the user's accuracy above are more likely too low than too high; the producer's accuracy does not move (section 8).

---

## 1. What is assessed

- **Map:** the publish of 27 Nov 2026 (`index.json` `generated_utc` "2026-11-27 07:17"): 213 tiles (north run 65, season pilot 3, main run 145) in 112 cells.
  - It was never the `crops/2026/` folder of this repository, which held the 7 Nov publish until the map moved to Cloudflare R2 on 28 Nov 2026; the folder was then removed from the repository and its history.
  - The assessed copy is `crops_2026_20261127_0717.zip`, 312,149,487 bytes, SHA-256 `9e87f0f7b8df12a6f6e1b87a7b862be1bec1778dc42293970478b95f701008db`. It is attached to the release [`crops-2026-north-assessed`](https://github.com/rawazrauf/iraq-farms-health/releases/tag/crops-2026-north-assessed) (published 28 Nov 2026; tag on commit `744a73b`, moved to the rewritten copy of that commit by the history clean-up the same day). The release copy was downloaded back and checked: byte-identical, all 128 files match `data/assessed_map_sha256.txt`, and the sample redraws from it byte for byte.
  - The SHA-256 of each of its 128 files is in `data/assessed_map_sha256.txt`.
  - The scripts refuse any other map (they check `generated_utc`, the tile count and the cell count) unless `--any-map` is given.
- **Population:** every map pixel in the tiles whose centre lies at or north of 34.8°N, clipped to Iraq's boundary (`boundaries.geojson`).
  - A tile's centre is the middle of its bounding box, as in the south. The two assessments together cover every tile once.
  - That gives 68 tiles (65 from the north run `iraq_winter2026_north`, 3 from the season pilot `iraq_pilot_season_jun`; both used the season 1 Nov 2025 – 30 Jun 2026) and 8,350,833 ha: 4.54 Mha in the federal governorates and 3.81 Mha in the Kurdistan Region.
- **Pixel codes:** as in the south. 0 = not cropland; 1 + class index = confident; +100 = less sure; +200 = doubtful cereal (cereal is the top crop but P(wheat)+P(barley) < 70%, or a patch under 0.1 ha).

## 2. Strata and sample

| Stratum | Pixel codes | Area (ha) | Share | Sample size |
|---|---|---|---|---|
| confident cereal | wheat, barley, rye or oats, code < 200 | 1,710,507 | 20.5% | 100 |
| doubtful cereal | wheat, barley, rye or oats, code > 200 | 1,445,737 | 17.3% | 100 |
| other crop | any other crop class except `no_crop` | 583,376 | 7.0% | 60 |
| no crop | `no_crop` | 825,421 | 9.9% | 60 |
| not cropland | 0 | 3,785,792 | 45.3% | 250 |
| **total** | | **8,350,833** | | **570** |

**Why these sizes, compared with the south:**
- Doubtful cereal and other crop are two to three times larger than in the south, and in the south they held most of the winter crop the map missed. They get 100 and 60 points.
- In the south, the winter crop hidden in "not cropland" was the largest single source of uncertainty in the area estimate and needed a 200-point top-up. Here not cropland gets 250 points from the start.

**How the points were drawn:** exactly as in the south.
- Within each stratum, its points are shared out among the map cells by a multinomial draw weighted by the stratum's ground area in each cell, then placed on uniform random pixels of that stratum.
- Seed `20261127`. The points are shuffled and numbered N001–N570, so the numbering says nothing about the class.
- No field polygons are used.
- Re-running `strata_area.py` and `draw_sample.py` on the assessed map reproduces every output file byte for byte (checked 27 Nov 2026). Every point was also re-read from the map and gives its recorded pixel code.

**Files:**
- `data/points.csv`: id, lat, lon. It is the only file the curve and labelling steps read.
- `data/map_key.csv`: id → stratum, pixel code and cell file. Not opened until all labels are final.
- `data/design.json`, `data/strata_area.json`: sizes, areas, seed and map identity.
- `data/spotcheck_ids.csv`: the second labeller's subset (section 5).

## 3. Reference labels (blind to the map)

As in the south ([`../accuracy_south_2026`](../accuracy_south_2026), "Reference labels"), with two changes.

**The same:**
- Each point's own Sentinel-2 L2A history, Sep 2025 – Aug 2026, one value per month, read as a single 10 m pixel through Microsoft Planetary Computer with `../accuracy_south_2026/fetch_curves.py` (clipped offset-corrected NDVI).
- Rules in the same order: water, perennial, winter crop, summer crop only, no crop, unclear. Same thresholds.
- The reference says **winter crop or not**, not cereal.

**Change 1, the northern winter test.** The north run's season ends on 30 June, and late rain-fed fields peak in May. A point is a **winter crop** if either:
- the southern winter test passes unchanged (peak in Dec–Apr), or
- the late test passes: the highest value of Dec–May is ≥ 0.40 and at least 0.25 above the year's lowest value; a Sep–Dec month before the peak is at least 0.20 below it (green-up inside the season); a May–Jul month after the peak falls to at most halfway between the lowest value and the peak (dry-down by July); and the first clear month after the peak is lower than the peak (so a spring-sown summer crop still rising in May does not pass).

So a crop that emerges in Feb–Apr, peaks in Apr–May and is dry by June or July counts as a winter crop. That matches the season the northern map was made for (late barley, spring chickpea). In the south such curves were judged "summer only" by hand.

**Change 2, the summer test is reached only after both winter tests fail.** It is otherwise unchanged (Dec–Apr below 0.30, Jun–Sep peak ≥ 0.40). The missing-month check for "unclear" counts Dec–May.

**Test on the southern curves (27 Nov 2026, before any northern curve existed):** on all 575 southern curves, `label_rules.py` here gives the same label as the southern rules for 570. The other 5 (S023, S079, S096, S184, S298: peak in May, dry by June) change from "unclear" to "winter crop".

## 4. Manual review of unclear points

- Every point the rules call "unclear" gets a manual look at its curve, blind to the map, using `data/review_criteria.txt`. The criteria were written on 27 Nov 2026, before any northern curve was fetched.
- They are the southern criteria with the season running to May and ending by July, plus northern notes: snow or cloud gaps in Jan–Feb, grazing or fodder cuts inside the season, a winter crop followed by a summer crop.
- The unclear points are shuffled before review. Rule and manual labels are both kept, with a one-line reason for each manual label.

## 5. Second labeller

- In the south the manual look was the least repeatable step: a blind re-review agreed with the first on only 31 of 57 curves.
- So a random 10% of the northern points (57, seed `20261128`, listed in `data/spotcheck_ids.csv`) is to be labelled independently by someone other than Claude, with the same rules and criteria, blind to the map and to Claude's labels.
- Agreement is reported. Claude's labels are used for the estimates unless the protocol is amended before the key is opened.

## 6. Estimation

- As in the south (Olofsson et al. 2014): area-weighted error matrix from the stratum weights; overall accuracy; user's and producer's accuracy for "confident cereal" and for "confident + doubtful cereal" against "winter crop"; error-adjusted winter-crop area with a 95% interval.
- Unclear points are reported both ways (all winter crop / none winter crop) as bounds, and left out of the headline.
- The Kurdistan Region and the federal north are reported as sub-areas (domain estimates). They were not sampled separately, so their intervals are wider.
- Declared for later, with thresholds to be fixed before looking: the forage test and the land-use check against very-high-resolution imagery on the northern sample, as done in the south.

## 7. What happened, in order (27 Nov 2026)

**Curves.** Fetched by Rawaz in Colab with `fetch_north.ipynb`: 570 of 570 points, no errors; 477 have all 12 months. `data/curves.json`, SHA-256 `3449a5a22f6e4f5392df4fa2833a44eed386b9d622688485fa37b31922a76feb`.

**Curve labels, blind to the map.**
- Rules (`label_rules.py`): winter crop 322 (27 of them through the late test), no crop 146, unclear 88, summer only 9, water 4, perennial 1.
- Manual look at the 88 unclear (shuffled, seed `20261129`, `data/review_blind.csv`): winter crop 32, unclear 26, no crop 22, perennial 6, summer only 2. Two readings of the criteria were fixed during this look, still blind: an "isolated single-month spike" is a peak that is the only month ≥ 250 with both neighbouring months less than 100 above the Sep–Nov level; "falling back half way" means half way from the peak back to the Sep–Nov level.
- Final (`data/labels_final.csv`): winter crop 354, no crop 168, unclear 26, summer only 11, perennial 7, water 4. Its SHA-256 (`02dd7442…3caf3181`) was recorded in the project notes before the key was opened.

**Key opened: the reference did not work as written.** 132 of the 234 "not cropland" points had a winter-crop curve, 110 of them in the Kurdistan Region, most peaking in May. In the north, natural grassland and rangeland green up in spring and dry by June, exactly like a rain-fed crop, so an NDVI curve alone cannot tell them apart (in the southern desert the question never arose). Taken at face value the curve labels gave 5.47 Mha of "winter crop" in an 8.35 Mha area and a producer's accuracy of 0.30. Those figures are kept in `expected_output.txt` but are not a measure of the crop map.

**Amendment 1: land use from imagery** (written before looking: `data/landuse_criteria.txt`).
- A winter-crop curve counts only where the land is farmed. Every point with a winter-crop or unclear curve (380) was looked at on Esri World Imagery (zoom 16 and 18 side by side, ten points a sheet, shuffled with seed `20261130`, no map class shown) and judged farmed, not farmed or unsure at the marked point.
- Result: farmed 123, not farmed 163, unsure 94 (`data/landuse.csv`, with a one-line note for each).
- By map class, of the winter-crop curves: confident cereal 62 farmed / 8 not / 23 unsure; doubtful 30 / 13 / 25; other crop 22 / 7 / 15; no crop 0 / 11 / 6; not cropland 5 / 107 / 20.
- This look was done by Claude after the key had been opened. No class was shown and the order was shuffled, but it is not blind in the sense the curve labels were.
- With unsure land left out, the bounds were too wide to use: winter-crop area 1.78–3.45 Mha.

**Amendment 2: unsure land resolved with Fields of the World** (written before any outline was read; appended to `data/landuse_criteria.txt`).
- For the 94 unsure points only: inside an FTW 2025 field polygon → farmed, outside → not farmed. FTW's Iraq file was read in the browser from the copy the app serves (`tiles.iraqfarmshealth.com/fields/Iraq.pmtiles`, zoom 13), with a point-in-polygon test on the tile geometry. 43 of the 94 fall inside a field.
- **FTW agrees with the imagery less than hoped.** On the 286 points with a decided imagery label, FTW 2025 agrees on 202 (71%): it misses 41 of 123 farmed points and includes 43 of 163 unfarmed ones. FTW 2024 agrees on 250 (87%). The 2025 layer was declared as the rule, so it gives the headline; 2024 is reported as the sensitivity check below.

**Amended results** (`amend_labels.py`, then `estimate.py`; unclear left out; the bounds count unclear points all one way or all the other):

| | Amendment 1 (unsure land = unclear) | **Amendment 2 (FTW 2025, headline)** | Sensitivity (FTW 2024) |
|---|---|---|---|
| Confident cereal UA | 0.83 (bounds 0.62–0.87) | **0.76** (0.74–0.76) | 0.80 |
| Confident cereal PA | 0.59 (0.43–0.60) | **0.52** (0.47–0.52) | 0.54 |
| Confident + doubtful UA / PA | 0.64 / 0.84 | **0.61 / 0.77** | 0.65 / 0.81 |
| Winter crop on farmland | 2.42 Mha (1.78–3.45) | **2.50 Mha** (2.41–2.79) | 2.52 Mha |

By map class (amendment 2, unclear left out), the share of points with winter crop on farmland: confident cereal 76%, doubtful 44%, other crop 49%, no crop 5%, not cropland 6%.

**Reading.**
- Winter crop on farmland in the northern tiles is about 2.5 Mha, against 1.71 Mha of confident cereal mapped. That holds across all three versions within ± 0.1 Mha once the unsure land is resolved.
- The default map misses about half of it: producer's accuracy 0.52 (south 0.71). As in the south, most of the missed area is in doubtful cereal (0.63 Mha) and other crop (0.29 Mha); the 70% rule is the main reason.
- Where the map says confident cereal, a winter crop grew on farmland about three times in four (0.76; south 0.96). Some of the difference may be reference error: the imagery is undated, and FTW disagrees with it on 29% of points.
- Confident + doubtful cereal catches 77% of the area but is right only 61% of the time.

**Still open:** in-season imagery (to-do item 30) would settle the land use and the cereal question on a subsample.

## 8. Second labeller (28 Nov 2026)

**Who and how.** Rawaz Rauf (project lead) labelled the 57 spot-check points on 28 Nov 2026 with `spotcheck_north.html`, a page that shows each point's curve (chart and monthly values) and Esri imagery (zoom 16 and 18) with links to Google Maps and Google Earth, in a new shuffled order (seed `20261201`). It shows no map class and none of Claude's labels. For each point he gave a curve label and a land-use label, with a note (`data/spotcheck_second_labeller.csv`). He used Google Earth's dated imagery and his knowledge of the area as well.

**Not fully independent.** He knows the project and had seen the overall results (but not any point's label or map class) before labelling. The comparison is a check on Claude's reading, not an independent accuracy assessment.

**Agreement** (`spotcheck_compare.py`):

| | Agree |
|---|---|
| Curve label, exact | 38 of 57 |
| Curve, winter crop or not | 45 of 57 |
| Land use, where both decided | 16 of 19 (30 points looked at by both) |
| Final reference, winter crop on farmland or not | 46 of 57 |

**The disagreements nearly all go one way.** The second labeller found winter crop on farmland at 21 points, Claude at 12. He agrees with 11 of Claude's 12 (the exception, N217, he read as sparse forest). Claude missed 10 of his 21:
- **Thin crops below the written threshold (N005, N015, N047, N336, N541).** Curves peak at only 250–302, rising in March–April, on land he judged farmed. The written criteria (a winter peak of at least 350; a curve below 330 is no crop) call them no crop. Poor rain-fed barley can stay this low, so the criteria may miss thin crops. That is a question for the next protocol, decided before labelling (see the to-do item on revisiting the 70% rule), not a reason to relabel now.
- **Land calls where Claude was too strict (N268, N409, N443, N489, N495).** Points on a field corner or track, a hillside field and a slope, which Claude judged unsure or not farmed. FTW 2025 resolved two of them (N489, N495, both confident cereal with strong curves) to not farmed.
- Five points with forest or sparse trees he labelled perennial where Claude's curve label was winter crop. The land is not farmed in both readings, so the final reference does not change.

**Effect** (labels_amended2 with his answers on the 57 points; unclear left out):

| | Claude (headline) | With the second labeller's answers |
|---|---|---|
| Confident cereal UA | 0.76 (0.67–0.84) | 0.80 (0.72–0.88) |
| Confident cereal PA | 0.52 (0.47–0.57) | 0.52 (0.47–0.57) |
| Confident + doubtful UA / PA | 0.61 / 0.77 | 0.63 / 0.76 |
| Winter crop on farmland | 2.50 Mha (2.24–2.75) | 2.64 Mha (2.38–2.89) |

This swaps only 10% of the sample. If the same pattern holds across all points, Claude's reference is conservative throughout: the area and the user's accuracy are probably underestimates, while the finding that the default map catches only about half of the winter crop holds either way. The published labels are not changed: re-labelling after seeing these answers would be a third amendment made with hindsight.

## Steps

```
pip install -r requirements.txt
# 1-2. Population, strata and sample (already done; re-running reproduces the files)
python strata_area.py --crops <unzipped assessed map>/2026
python draw_sample.py --crops <unzipped assessed map>/2026
# 3. Reference curves (Colab: fetch_north.ipynb, about 1.5 h)
python ../accuracy_south_2026/fetch_curves.py --points data/points.csv --out data/curves.json
# 4. Rule labels (never reads map_key.csv); the manual labels are in data/labels_final.csv
python label_rules.py data/curves.json --out data/labels_rule.csv
# 5. Region of each point (for the sub-area estimates)
python point_regions.py --crops <unzipped assessed map>/2026
# 6-7. Land-use amendments and estimates (output: expected_output.txt)
python amend_labels.py
python estimate.py
python estimate.py data/labels_amended2.csv --column amended_label
# 8. Second labeller (spotcheck_north.html is the page that was used)
python spotcheck_compare.py
python estimate.py data/labels_amended2_second_labeller.csv --column amended_label
```

## Limits

The same as in the south: the reference comes from the same satellite as the map, so agreement may be somewhat overstated; the reference is winter crop, not cereal, so user's accuracy and the area are upper bounds for cereal; and the label rules, though fixed in advance, are Claude's reading of NDVI curves. The second labeller's check (section 8) suggests that reading is conservative: it misses thin crops on farmland and is strict about field edges.
