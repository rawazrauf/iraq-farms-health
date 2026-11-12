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

## Runs and season (updated 12 Nov 2026)
- **Main run** `iraq_winter2026`: WorldCereal's own crop calendar, so 206 of 218 tiles have the season 1 Dec 2025 – 31 May 2026 (data window Jun 2025 – May 2026); 12 tiles on the northern border and in the far east run to June–August. FAO/GEOGLAM puts Iraq's wheat end of season at 1 July, so the calendar cuts the season about a month early for late fields.
- **Season pilot** `iraq_pilot_season_jun` (4 tiles, 1 Nov 2025 – 30 Jun 2026; results in `validation/season_pilot/`): the later season helped in the north (7 of 18 wrong fields became right) but did not pass the pre-agreed rule; the south was unchanged. Decision (2 Nov): re-run every tile centred at or north of 34.8°N with the later season. Published as `crops/2026p/`.
- **North run** `iraq_winter2026_north` (`RUN_MODE = "north"`): 65 tiles (the 68 northern tiles minus the 3 northern pilot tiles), season 1 Nov 2025 – 30 Jun 2026, or later where WorldCereal's calendar ends later (8 tiles end 31 Jul or 31 Aug; `NORTH_SEASON_END = "later"`). Runs from 1 Dec 2026, when credits renew. 17 of these tiles were already finished by the main run and are re-run.
- **Publishing merges the runs**: north > pilot > main for each tile. `sources.json` records which run each tile came from.

## Status
- **Published 7 Nov 2026 12:54 UTC** (repo commit `969b4aa`; the map assessed in `validation/accuracy_south_2026/`): 87 of 218 tiles, 84 from the main run and 3 from the pilot. 67 cells, 178 MB.
  - The 84 main-run tiles are the 67 southern tiles that were assessed plus 17 northern tiles finished before northern tiles were held back.
  - Southern tiles not yet in the published layer: 83 of the 150 planned south of 34.8°N (main run; to be confirmed against the run folder's status).
- 8 Nov: `overview.tif` rewritten with nodata 0 and a colour table (same pixels); `iraq_crops.qml` labels escaped (`&lt;`), so QGIS loads it.
- 8 Nov: labels that can't be right in a winter map are shown differently on the crop page and in the app (the data keep WorldCereal's codes): summer-only crops (rice, maize, sorghum, sunflower, cotton and others, ~3,200 ha) as "not a winter crop"; tobacco and rapeseed as "other crop" (label often wrong). See `METHODOLOGY.md` §8.
- The 2025-26 layer is **not shown to the public in the app** (debug mode only) until the north is processed and validated.
- Earlier: 26 Oct overview bug fixed (MODE resampling includes 0); 27 Oct zoom-hint bug fixed; 28 Oct first publish (37 tiles); 29 Oct switch to the wheat + barley probability.

## Credits (CDSE openEO)
- A standard Copernicus General account gets 10,000 openEO credits on the 1st of every month. The balance is in the Billing tab of the openEO Algorithm Plaza.
- A 40 km tile costs ~205 credits (estimate × 0.96 after 45 tiles). Failed jobs are charged too; refused jobs (402) are not.
- The north run is expected to take ~13,300 credits: all of December's 10,000 and ~3,300 in January.
- `CREDIT_BUDGET` should be ~9,500, below the monthly balance.
- Options if more are needed: an account upgrade to 20,000 per month, if eligible, or buying credits through CREODIAS.
- The batch tool counts only jobs that ran and failed (error, canceled) as attempts, so refusals keep a tile's retries. A batch where no job could start is renamed `batch_NN_nostart_*` and the tool stops (NO_START).

## Early comparison with WorldCereal 2021 (37 tiles, 5.94 Mha processed, 2026-10-28)
- An early agreement check, not an accuracy figure. The accuracy assessment of the 67 southern tiles is in `validation/accuracy_south_2026/`; its headline: where the map says confident cereal, a winter crop grew 96% of the time (95% CI 92–99%), and the map catches 71% (65–77%) of the winter-crop area.
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

## Research-grade path
- **Done for the south (8 Nov 2026):** stratified random sample of 575 pixels, labelled blind from each pixel's Sentinel-2 history under a written protocol, Olofsson et al. (2014) estimators with 95% confidence intervals. Method, data and scripts in `validation/accuracy_south_2026/`.
- **Still needed:** the same for the north after the north run; an independent second labeller for the borderline curves; cereal vs other winter crops, and wheat vs barley, on a subsample (very high-resolution imagery or farmer answers).
- Farmer reports via Iraq Farms Health would help only if the fields are chosen at random, with farmers reporting on them. Volunteered reports are supporting evidence only. Rules: don't show the map's answer first, keep reports anonymous and separate from subsidies, ask for consent.
- Prior work: Gibson et al. 2015 (MODIS cropland), Qader/Dash/Atkinson (MODIS crop area and production; WorldPop with the University of Sulaimani and the KRG Ministry of Agriculture), conflict studies (Eklund 2017, Jaafar & Woertz 2016). No national 10 m crop-type map of Iraq with validation was found.
- Likely venue: a data paper (ESSD, Scientific Data).

## Data format
- `cells/z9_<x>_<y>.tif`: EPSG:3857 COGs. Each file is one web-map z9 tile (≈78 km), 6656 px at 11.76 m, DEFLATE, MODE overviews that include 0.
  - Cells published on 7 Nov carry no nodata tag and no colour table. From the next publish, `write_cog()` builds the overviews first, then sets nodata 0 and the colour table (`cog_colormap()`, the QML's colours), so GIS programs show the classes in colour without the QML.
- Pixel codes (also in `index.json` → `codes`):
  - 0 = not cropland / not processed
  - 1 + WorldCereal class index (1 wheat, 2 barley … 24 no_crop)
  - +100 where WorldCereal's own confidence is below 60%
  - +200 = doubtful cereal (wheat + barley probability below 70%, or a speck under 0.1 ha)
- `overview.tif` (national, 76 m; nodata 0 and colour table since 8 Nov), `iraq_crops.vrt` + `iraq_crops_ovr1..5.vrt`, `iraq_crops.qml` (labels written with `quoteattr`), `legend.csv`, `index.json`, `compare_2021.json`, `stats*.json/csv`, `boundaries.geojson`, `sources.json`.

## Statistics
- Counted at native 10 m in UTM from each tile, masked to its own UTM zone, and summed by district (geoBoundaries gbOpen IRQ ADM2) → governorate → region.
- Per class: `ha`, `ha_sure` and, for cereals, `ha_cereal70`.
- District → governorate: the ADM1 unit each district overlaps most, plus overrides for Baghdad's outer districts, Hindiya → Karbala, and Halabcha → Halabja.
- Kurdistan Region = Duhok, Erbil, Sulaymaniyah, Halabja.

## Hosting
- Same repo, `crops/2026/`, served by GitHub Pages (HTTP range requests and CORS work, so the page and GIS programs stream the COGs directly).
- Each publish adds a full new copy of the cells to the git history (~180 MB). History was 453 MB on 10 Nov; the December republish would bring it to ~640 MB, against GitHub's ~1 GB limit. Where the cells should live (history purge, a separate data repo, or Source Cooperative) is an open decision, to settle before the December republish.
- The page loads `crop-layer.js?v=…`; bump `?v=` in `crops/index.html` whenever `crop-layer.js` changes.

## Pending
- Southern main-run tiles still to run, then the north run from 1 Dec.
- Republish (north > pilot > main), rerun `worldcereal_compare_2021.ipynb`, then check: the crop page's "Season windows", a cell and the overview in GeoLibre and QGIS, a browser download, and summer-crop or tobacco-type labels on the shores of Mosul Dam, Dukan and Darbandikhan.
- Northern field checks re-scored; northern accuracy assessment; then revisit the 70% rule.
- Iraq Farms Health shows the 2025-26 layer to the public only after that, and only on Rawaz's go (debug-only until then).
- Arabic and Kurdish strings on the crop page: native check (Kurdish by Rawaz).
