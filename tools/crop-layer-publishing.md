# Crop layer publishing (WorldCereal 2025-26)

## Pipeline
1. `worldcereal_iraq.ipynb` (Colab): runs ESA WorldCereal's default model (2.8.1, with WorldCereal's own majority-vote smoothing: 5×5 for crop type, 3×3 for cropland) tile by tile on CDSE. Results go to Drive at `iraq-farms-health/worldcereal/iraq_winter2026/`.
   - At the end of each batch, the raw tiles are compacted and deleted.
   - Compact bands: class, class_confidence, p_wheat, p_barley. From batch 2 on, also p_rye and p_oats; bands 1–4 keep the same order.
2. `worldcereal_publish.ipynb` (Colab, read-only on the run): turns finished tiles into `publish/2026/` in Drive, plus a zip.
   - Safe to re-run at any time; the numbers are provisional until every planned tile is done.
   - Re-running wipes the Drive `publish/2026/` folder, including any `compare_2021.json`.
3. `worldcereal_compare_2021.ipynb` (Colab, run straight after publish): compares our map with ESA's official WorldCereal 2021 on a ~16 m grid.
   - 2021 layers: winter cereals and temporary crops, read from the Terrascope WMTS.
   - Uses only tiles in the published `index.json`. Tiles that finished after publish are skipped and reported in the log.
   - Rules: top_crop, p50, p70_all, p70 (the default).
4. Upload `publish/2026/` to the repo as `crops/2026/`. The page `crops/index.html` + `crops/crop-layer.js` (iraqfarmshealth.com/crops/) streams it.

## Decision: "confident cereal" = wheat + barley ≥ 70% (2026-10-29)
- A pixel counts as confident cereal when all three hold:
  - it is a cereal class (wheat, barley, rye or oats)
  - P(wheat)+P(barley) ≥ 70%
  - it sits in an 8-connected patch of at least 0.1 ha (`MIN_PATCH_HA`)
- Why wheat + barley only:
  - Batch 1's raw files were deleted and its compact copies have no rye or oats probabilities.
  - The earlier four-cereal sum silently became wheat + barley once tiles were compacted.
  - Using wheat + barley everywhere gives the same result for raw and compact tiles; this was tested.
- Effect: the four-cereal and wheat + barley rules differ a lot near the threshold, mainly in the rain-fed north, where the model spreads probability over rye and oats. One Duhok hill cell went from 10.7% to 0.3%.
- Everything else classed as cereal gets code +200 ("doubtful cereal"):
  - hidden on the map by default, with a legend checkbox to show it
  - kept in downloads
- Statistics use `ha_cereal70`. WorldCereal's top-crop total is shown as a secondary line.
- The Check tab and the difference map use rule p70 by default. A legend switch selects the top-crop map.
- The speck filter removes only ~1%, because WorldCereal already smooths with a 5×5 majority vote. 0.1 ha is kept; a larger threshold would remove real smallholder plots, for example around Hilla.
- The threshold may need revisiting visually (Erbil, Hilla) now that it is stricter.

## Status
- 2026-10-28: 37 of 218 tiles published (39 cells, 113 MB).
  - Batch 1 is closed: 37 finished; 3 failed and are queued for one retry in batch 2.
  - Batch 2 (42 tiles, ~8,920 credits) is running; 139 tiles are left after it.
  - Each tile takes ~2–2¾ h on CDSE, 2 at a time.
- 2026-10-29: switched to wheat + barley probability.
  - Batch 2's compaction now keeps rye and oats too.
  - The 37-tile publish/compare run from 2026-10-28 was all-compact, so its numbers already follow this rule.
- 2026-10-27: zoom-hint bug fixed. With 256 px tiles, MapLibre requests tile zoom round(map zoom + 1).
- 2026-10-26: overview bug fixed (MODE resampling now includes 0; cells carry no nodata).

## Validation findings (37 tiles, 5.94 Mha processed, 2026-10-28)
- Cropland extent: 2.43 Mha in 2021 against 2.45 Mha in 2025-26 (F1 0.61).
- Change against 2021 under each rule:

  | Rule | All processed | Other governorates | Kurdistan Region |
  |---|---|---|---|
  | top_crop | ×1.44 | ×1.31 | ×2.23 |
  | p50 (wheat + barley) | ×1.23 | ×1.13 | ×1.78 |
  | p70_all (wheat + barley) | ×0.87 | ×0.83 | ×1.14 |
  | p70 (default) | ×0.86 | ×0.82 | ×1.12 |

- The Kurdistan Region / other gap depends on the rule: ~×1.7 under top_crop, ~×1.37 under p70 (wheat + barley). Earlier claims that it was stable held only for the four-cereal sum.
- Context: 2021 was a drought year; 2025-26 had above-normal rain.
- Irrigated governorates come out below 2021 even under top_crop (Wasit, Diyala, Qadisiyah, Babil). There is a large coherent "2021 only" block north-east of Hilla. Possibly less irrigation water; check against the Ministry of Agriculture's winter plan.
- Weakest agreement: Sulaymaniyah (F1 0.27) and Babil (0.38). Best: Najaf (F1 0.82).
- Barley is likely over-mapped against COSIT; the wheat/barley split is unvalidated.

## Research-grade path (discussed 2026-10-27)
- Needed: a sample-based accuracy assessment (Olofsson et al. 2014) and area estimates with 95% confidence intervals.
  - Stratified random sample of ~500–1,000 points by map class.
  - Labels from free Sentinel-2 season curves plus Google Earth / Esri very high-resolution imagery, under a written protocol.
  - Farmer answers for wheat versus barley.
- Farmer reports via Iraq Farms Health: useful only if the fields are chosen at random, with farmers reporting on them.
  - Volunteered reports are supporting evidence only.
  - Rules: don't show the map's answer first, keep reports anonymous and separate from subsidies, ask for consent.
  - In-season reporting with photos for 2026-27 (by about February).
- Prior work: Gibson et al. 2015 (MODIS cropland), Qader/Dash/Atkinson (MODIS crop area and production; WorldPop with the University of Sulaimani and the KRG Ministry of Agriculture), conflict studies (Eklund 2017, Jaafar & Woertz 2016). No national 10 m crop-type map of Iraq with validation was found.
- Likely venue: a data paper (ESSD, Scientific Data).

## Data format
- `cells/z9_<x>_<y>.tif`: EPSG:3857 COGs. Each file is one web-map z9 tile (≈78 km), 6656 px at 11.76 m, DEFLATE, MODE overviews that include 0, no nodata tag.
- Pixel codes:
  - 0 = not cropland / not processed
  - 1 + WorldCereal class index (1 wheat, 2 barley … 24 no_crop)
  - +100 where WorldCereal's own confidence is below 60%
  - +200 = doubtful cereal (wheat + barley probability below 70%, or a speck under 0.1 ha)
- `overview.tif` (national, 76 m), `iraq_crops.vrt` + `iraq_crops_ovr1..5.vrt`, `iraq_crops.qml`, `legend.csv`, `index.json`, `compare_2021.json`.

## Statistics
- Counted at native 10 m in UTM from each tile, masked to its own UTM zone, and summed by district (geoBoundaries gbOpen IRQ ADM2) → governorate → region.
- Per class: `ha`, `ha_sure` and, for cereals, `ha_cereal70`.
- District → governorate: the ADM1 unit each district overlaps most, plus overrides for Baghdad's outer districts, Hindiya → Karbala, and Halabcha → Halabja.
- Kurdistan Region = Duhok, Erbil, Sulaymaniyah, Halabja.

## Hosting
- Same repo, `crops/2026/`. Estimated ~300–450 MB per season; GitHub Pages' site limit is 1 GB.

## Pending
- Iraq Farms Health: switch its crop layer to `crops/crop-layer.js` once the data is validated.
- Kurdish and Arabic strings on the page need a native check.
- Sampling and labelling tool for the accuracy assessment.
