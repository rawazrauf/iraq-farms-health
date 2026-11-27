# Accuracy assessment of the 2025-26 crop map: northern tiles

A stratified random accuracy assessment of the northern part of the Iraq Farms Health winter-cereal map for the 2025-26 season. It follows the southern assessment ([`../accuracy_south_2026`](../accuracy_south_2026)) and Olofsson et al. (2014), with the changes listed in section 3.

**Status:** protocol written and sample drawn on 27 Nov 2026, **before any northern reference curve was fetched or labelled.** Nothing in sections 1–6 is to be changed after the curves come in; any later change is added as a dated note and reported both ways.

---

## 1. What is assessed

- **Map:** the publish of 27 Nov 2026 (`index.json` `generated_utc` "2026-11-27 07:17"): 213 tiles (north run 65, season pilot 3, main run 145) in 112 cells.
  - This is **not** the `crops/2026/` folder in this repository at the time of writing, which still holds the 7 Nov publish.
  - The assessed copy is `crops_2026_20261127_0717.zip`, 312,149,487 bytes, SHA-256 `9e87f0f7b8df12a6f6e1b87a7b862be1bec1778dc42293970478b95f701008db`. It is to be attached to a GitHub release, as the southern map was.
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

## Steps

```
pip install -r requirements.txt
# 1-2. Population, strata and sample (already done; re-running reproduces the files)
python strata_area.py --crops <unzipped assessed map>/2026
python draw_sample.py --crops <unzipped assessed map>/2026
# 3. Reference curves (Colab: fetch_north.ipynb, about 1.5 h)
python ../accuracy_south_2026/fetch_curves.py --points data/points.csv --out data/curves.json
# 4. Rule labels (never reads map_key.csv)
python label_rules.py data/curves.json --out data/labels_rule.csv
```

## Limits

The same as in the south: the reference comes from the same satellite as the map, so agreement may be somewhat overstated; the reference is winter crop, not cereal, so user's accuracy and the area are upper bounds for cereal; and the label rules, though fixed in advance, are Claude's reading of NDVI curves.
