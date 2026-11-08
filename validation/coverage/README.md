# Coverage: farmland outside the processed tiles (7 Nov 2026)

## Question
How much of Iraq's farmland falls outside the 40 km tiles that the crop map processes? Farmland in no tile can't appear on the map at all.

## Method
- Notebook: `tools/worldcereal_coverage_gaps.ipynb`.
- Farmland is taken from Fields of the World (FTW) polygons with confidence ≥ 0.22, clipped to Iraq.
- Each polygon is checked against the planned tiles of run `iraq_winter2026`, with each tile clipped to its UTM zone.
- Results are reported by governorate, and separately within about 10 km of the 42°E and 48°E zone boundaries, where tiles meet.
- The notebook was first tested on synthetic data with a known answer: it reported 50% untiled for a case built to be 50% untiled.

## Result
| | km² | share |
|---|---|---|
| FTW farmland in Iraq | 117,018 | |
| inside planned tiles | 116,572 | 99.6% |
| in no tile | 446 | 0.4% |
| of which within ~10 km of 42°E / 48°E | 52 | (of 1,058 km² of farmland there) |

| Governorate | Farmland (km²) | In no tile (km²) | Share |
|---|---|---|---|
| Al-Anbar | 5,382 | 240 | 4.5% |
| Al-Muthanna | 2,810 | 58 | 2.1% |
| Maysan | 7,669 | 40 | 0.5% |
| Al-Basrah | 1,636 | 36 | 2.2% |
| Ninawa | 12,807 | 35 | 0.3% |
| An-Najaf | 1,656 | 15 | 0.9% |
| Dhi Qar | 7,512 | 9 | 0.1% |
| Salah al-Din | 9,650 | 6 | 0.1% |
| Dohuk | 3,460 | 3 | 0.1% |
| Wasit | 9,797 | 1 | 0.0% |
| Diyala | 11,533 | 1 | 0.0% |
| Erbil, Karbala, Babil, Baghdad, Al-Qadisiyah, Kirkuk, Al-Sulaimaniyah | | 0 | 0.0% |

The map (`gaps_map.png`) shows farmland inside a tile in green and farmland in no tile in red.

## Reading
- The untiled farmland is scattered in small patches. Most of it lies across the western desert of Al-Anbar, with smaller patches in the far south-east and the far south.
- There is no single cluster that one or two extra tiles would capture.
- The tile seams are not a significant source of gaps.
- FTW at confidence ≥ 0.22 includes some land that isn't farmed, so 446 km² is an upper bound on the farmland missed.

**Decision:** no extra tiles. The crop map's totals leave out up to 0.4% of FTW farmland nationally. In Al-Anbar that rises to 4.5%, and in Al-Basrah and Al-Muthanna to about 2%. Governorate figures for those three should be read with this in mind.

Since 8 Nov 2026 the crop page's governorate table marks these three with † and gives the shares in a note under the table (English, Arabic, Kurdish).
