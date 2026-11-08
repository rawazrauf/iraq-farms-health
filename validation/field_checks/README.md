# Field checks (fields 10–212)

These are field-by-field checks of the 2025-26 crop map. Each field's own Sentinel-2 greenness curve and monthly images were read in Iraq Farms Health's debug mode (`https://iraqfarmshealth.com/?debug=1`). They were done between 29 Oct and 1 Nov 2026.

They are **qualitative evidence**. They are not an accuracy figure. For that, see [`../accuracy_south_2026`](../accuracy_south_2026).

**NDVI scale.** The greenness values in the log were read with app builds before 2026.11.07-b, which did not remove Sentinel-2's +1000 offset, so they are about 0.2–0.3 lower on green crops than Copernicus Browser or the current app (see [`../ndvi_offset`](../ndvi_offset)). They are consistent with each other, and the judgements rest on the shape and timing of each curve, which the offset doesn't change.

## Files
- `field_checks_log.md`: the full log, one row per field. Each row gives:
  - coordinates;
  - what was really there, and how that was judged (greenness curve, month images);
  - how confident the judgement is;
  - what the 2025-26 map said (confident-cereal share, WorldCereal top crop);
  - the ESA 2021 map;
  - the verdict.

  Notes and lessons from the checks follow the table.
- `browser_scripts.md`: the JavaScript used to pick and read fields in the debug page. It needs IFH build 2026.10.30-k or later.

## How a field was chosen
- **Random draws (most fields):**
  1. A random cropland pixel was drawn from the processed tiles of `crops/2026/iraq_crops.vrt`.
  2. The app was opened at that point (`?lat=…&lon=…&z=16&debug=1`).
  3. The field under the point was read. If there was none, a random field of 1–500 ha in view was read instead.
- **Picked by hand:** a few early fields (11, 14).
- **Targeted late-field tests (188–211):** fields were screened for April NDVI ≥ 0.35, May ≥ 0.30 and July ≤ 0.20 before the map was read. These test one hypothesis (late fields are missed) and are reported separately.

These draws are biased toward larger fields, and they never sample pixels the map calls not cropland. That's why they give no accuracy figure.

## How a field was scored
- **Cereal field:**
  - Yes if confident cereal ≥ 50% of the field.
  - Partly if confident < 50% but WorldCereal's top crop is ≥ 50% cereal.
  - No otherwise.
- **Not-cereal field:** Yes if confident cereal < 50%.
- **Not scored** when the curve can't decide. That covers weak growth (thin cereal vs grass), mixed tree cover, merged polygons, and a green-up that only starts in March (late cereal vs spring crop).

## Tally (as logged)
| | Yes | Partly | No | Not scored | Pending |
|---|---|---|---|---|---|
| Random and hand-picked (10–187) | 106 | 33 | 11 | 26 | 2 |
| Targeted late fields (188–211) | 6 | 10 | 4 | 4 | 0 |

Field 212 (8 Nov 2026) is a single case, not part of either set: the "rice" near Lake Hamrin, which turned out to be lake shore flooded in April. It is the evidence for showing summer-crop labels as "not a winter crop" on the crop page.

Scored random and hand-picked fields by region (34.8°N):

| Region | Yes | Partly | No |
|---|---|---|---|
| North | 54 | 28 | 11 |
| South | 52 | 5 | 0 |

## Main findings
- Irrigated cereal in the centre and south is reliably mapped.
- In the rain-fed north:
  - The 70% confidence rule often leaves a clear cereal field below 50% confident ("Partly").
  - Some cereal-shaped crops are read as vegetables, pulses or not cropland ("No").
- Late northern fields are wrong more often: 27 of 36 against 26 of 61 earlier northern cereal fields (Fisher's exact test, p ≈ 0.003). This led to the season pilot ([`../season_pilot`](../season_pilot)).
- Data-quality issues found along the way (bad scenes, sliver scenes, giant FTW polygons) are listed under "Data-quality notes" in the log. They were fixed in later app builds.
