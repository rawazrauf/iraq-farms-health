# Season pilot: a later season window for the north (Nov 2026)

## Question
Does running WorldCereal with a season of 1 Nov 2025 – 30 Jun 2026 fix the northern cereal fields that the main run got wrong? The main run's season was 1 Dec 2025 – 31 May 2026.

## Design (fixed before the run)
- **Run:**
  - `iraq_pilot_season_jun`: 4 tiles, WorldCereal 2.8.1, season `tc-s1`, 1 Nov 2025 – 30 Jun 2026. The data window is 1 Jul 2025 – 30 Jun 2026.
  - Batch notebook: `tools/worldcereal_iraq.ipynb`. Published as `crops/2026p/`.
- **Tiles:**
  - Rabia west (E0240_N4040);
  - Rabia–Tal Afar (E0280_N4040);
  - Nineveh plain (E0360_N4000);
  - Najaf–Kufa (E0440, a southern control).
- **Fields:** the logged field checks ([`../field_checks`](../field_checks)) inside these tiles. Both layers were read with the same app build (2026.11.02-a) on the same field outlines: `?debug=1&crops=2026p` for the pilot, `?debug=1` for the main layer. "Reality" is the label already in the log; it was not re-judged.
- **Scoring:** as in the field checks (Yes / Partly / No).
- **Pass rules:**
  - North: at least half of the Partly/No fields become Yes, and at most 1 Yes field gets worse.
  - South: no change.

## Result
- 42 logged fields were in the 4 tiles.
- Not used:
  - 10, 29 and 172, which are not scored in the log;
  - 114, whose centre lies outside the Najaf tile.
- Six fields came back with a different outline than logged. Both layers were read on the new outline.
- **North: not passed.**
  - 7 of 18 Partly/No fields became Yes; the rule needed 9.
  - No Yes field got worse (0 of 13).
- **South: passed.** All 7 scorable fields stayed Yes, and confident cereal moved by at most ±3 points.

| Tile | Partly/No → Yes | Other moves | Yes → worse |
|---|---|---|---|
| Rabia west | 3 of 6 (197, 203, 207) | 178 No → Partly; 199 Partly → No | 0 of 8 |
| Rabia–Tal Afar | 4 of 6 (21, 125, 137, 191) | 194, 195 unchanged | 0 of 1 |
| Nineveh plain | 0 of 6 | 97, 102 No → Partly; 100, 103, 110, 181 confident +19 to +34 points | 0 of 4 |
| Najaf–Kufa | n/a | none | 0 of 7 |

- **North totals:** main run Yes 13 · Partly 13 · No 5. Pilot: Yes 20 · Partly 9 · No 2.
- **Mean confident cereal in northern cereal fields:** 35% → 57%.
- **Whole tiles, pixel by pixel:** confident cereal rose as follows.

  | Tile | Change |
  |---|---|
  | Rabia west | +82% |
  | Rabia–Tal Afar | +105% |
  | Nineveh plain | +34% |
  | Najaf–Kufa | +2% |

  Total cropland barely changed.

## Decision
The pilot fell short of the pre-agreed north rule, but it improved every northern tile and made no field worse. On 2 Nov 2026 the project chose to re-run every tile centred at or north of 34.8°N with the later season, before revisiting the 70% rule.

- **Run folder:** `iraq_winter2026_north`, set with `RUN_MODE = "north"` in the batch notebook.
- **Season (decided 7 Nov 2026):** 1 Nov 2025 – 30 Jun 2026, as in the pilot. 8 tiles whose WorldCereal calendar season ends later (31 Jul or 31 Aug; the Zakho–Duhok belt, north of Erbil, and the Sulaymaniyah–Shahrazur side) keep that later end, so the latest fields are not cut short (`NORTH_SEASON_END = "later"`). The pilot itself tested only the 30 Jun end.
- **Publishing:** `tools/worldcereal_publish.ipynb` merges the north run, the pilot (its 3 northern tiles only) and the main run, in that order. It records each tile's run in `crops/2026/sources.json`.

The north will get the same accuracy assessment as the south after that run.
