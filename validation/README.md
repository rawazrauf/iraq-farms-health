# Validation of the Iraq Farms Health crop map

This folder holds how the 2025-26 winter-cereal map (`crops/2026/`) was checked, the data behind each check, and the scripts to repeat them. Anyone following the same steps on the same inputs should get the same numbers. Where that isn't fully possible (for example, if Planetary Computer reprocesses scenes), the folder says so and includes a script that measures the difference.

| Study | What it answers | Kind of evidence |
|---|---|---|
| [`accuracy_south_2026`](accuracy_south_2026) | How accurate is the map in the 67 finished southern tiles, and how much winter-crop area is there? | Stratified random sample, 575 pixels (375 + a 200-point top-up of "not cropland"), Olofsson et al. (2014) estimators |
| [`field_checks`](field_checks) | Where and how does the map go wrong, field by field? | 202 fields read from their Sentinel-2 curves and monthly images |
| [`season_pilot`](season_pilot) | Does a later season window (to 30 June) fix the northern errors? | Same fields, before and after, against pre-agreed pass rules |
| [`coverage`](coverage) | How much farmland falls outside the processed tiles? | FTW farmland checked against the tile plan: 99.6% covered |
| [`ndvi_offset`](ndvi_offset) | Does the app's NDVI need the Sentinel-2 +1000 offset removed? | Yes: Copernicus Browser matched the corrected formula on 140 of 140 dates; fixed in build 2026.11.07-b |

**Related tools elsewhere in the repo:**
- `tools/worldcereal_compare_2021.ipynb`: agreement with ESA WorldCereal 2021, by governorate.
- `tools/worldcereal_coverage_gaps.ipynb`: the notebook behind [`coverage`](coverage).
- `METHODOLOGY.md`: how the map and the app's field readings are made.

## Main results so far (8 Nov 2026)
- **South (accuracy assessment, 575 points).** Where the default map says "confident cereal", a winter crop grew 96% of the time (95% CI 92–99%). The map catches 71% (65–77%) of the winter-crop area. The winter-crop area in the southern tiles is 1.91 Mha (1.75–2.06), against 1.41 Mha mapped. A 200-point top-up of the "not cropland" class (8 Nov) narrowed the intervals by about a third without moving the estimates. Most of the missing area is in the "doubtful cereal" class (the 70% confidence rule) and in "other crop".
- **North (field checks).** Rain-fed cereal is often under-confident or confused with vegetables or pulses, and late fields are missed more often. A later season helps but doesn't fix it all, so the northern tiles are being re-run with that season. They will then be assessed like the south.

## Order of events
The order matters for judging the results:
1. Field checks first (29 Oct – 1 Nov 2026). They found the error patterns and led to the season pilot.
2. The accuracy protocol was written before the sample was labelled (7 Nov 2026). The sample was labelled blind to the map, and the map key was only opened for the estimates.

## Data sources
- **Sentinel-2 L2A:** Copernicus/ESA, via Microsoft Planetary Computer.
- **Crop map:** ESA WorldCereal 2.8.1 models, run on CDSE openEO.
- **Field boundaries:** Fields of the World.

Attribution terms are listed in the repo's main `README.md`.
