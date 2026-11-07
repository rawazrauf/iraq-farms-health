# Sentinel-2 +1000 offset on Planetary Computer

**Status:** resolved on 7 Nov 2026. From build 2026.11.07-b, Iraq Farms Health removes the offset.

## The question
Since ESA processing baseline 04.00 (25 January 2022), every Sentinel-2 L2A band has been stored with an added offset of 1,000. Reflectance = (DN − 1000) / 10,000.

The offset does not cancel in a normalized difference such as NDVI. Instead it inflates the denominator and pulls NDVI towards 0, and the greener the crop, the bigger the effect. Without the offset, NDVI is `(B08−B04)/(B08+B04−2000)`.

Iraq Farms Health (IFH) reads Sentinel-2 from Microsoft Planetary Computer and links every reading to Copernicus Browser for verification. The open question was whether either platform removes the offset.

## What the documentation says
- **ESA:** the offset (`BOA_ADD_OFFSET`) is fixed at −1000 for L2A from processing baseline 04.00, and it must be applied before computing any index.
  - [ESA STEP forum](https://forum.step.esa.int/t/info-introduction-of-additional-radiometric-offset-in-pb04-00-products/35431)
  - [CDSE forum](https://forum.dataspace.copernicus.eu/t/ndvi-with-radiometric-offset-of-sentinel-2-l2a/5243)
- **Microsoft Planetary Computer:** the offset "propagates to the L2A data hosted by the Planetary Computer", so it is **not removed**. Microsoft's own fix is to clip each band at 1000 and subtract 1000.
  - [baseline-change notebook](https://nbviewer.org/github/microsoft/PlanetaryComputerExamples/blob/main/datasets/sentinel-2-l2a/baseline-change.ipynb)
- **Sentinel Hub / Copernicus Browser:** `harmonizeValues` is on by default and Copernicus Browser doesn't override it, so the offset **is removed** before NDVI is computed.
  - [CDSE forum](https://forum.dataspace.copernicus.eu/t/sentinel-2-baseline-04-00-offset-csde-stac-derived-ndvi-doesnt-match-copernicus-browser-ndvi/5417)
  - [Sentinel Hub forum](https://forum.sentinel-hub.com/t/sentinel-hub-vs-planetary-computer-l2a/5883)

## Measured evidence (7 Nov 2026)
Copernicus Browser's Statistical Info was exported for two fields. For both, Planetary Computer was read for the same scenes, with and without the offset removed.

**1. Field 154 of the field-check log, near Dibis (Kirkuk), irrigated wheat.** Export: `copernicus_export_field_154.csv`.

| Scene | Copernicus Browser median | Planetary Computer, uncorrected | Planetary Computer, offset removed |
|---|---|---|---|
| 17 Apr 2026 (S2A) | 0.891 | 0.624 | 0.894 |
| 18 Mar 2026 (S2A) | 0.851 | 0.586 | 0.847 |

**2. Field FTW-PP1CC5, near Kufa (Najaf), irrigated, a winter crop and then a summer crop.**
- Copernicus export: `copernicus_export_field_PP1CC5.csv`.
- Planetary Computer values over the field's outline (`field_PP1CC5_outline.geojson`, 11.74 ha): `comparison_field_PP1CC5.csv`.
- Coverage: every clear date from Sep 2024 to Sep 2026, 140 dates in all, on Sentinel-2A, 2B and 2C, processing baselines 05.11–05.13.

| | Uncorrected | Offset removed |
|---|---|---|
| Median gap from Copernicus Browser (140 dates) | 0.078 | **0.001** |
| Largest gap | 0.288 | 0.026 |
| Median gap on green dates (Copernicus ≥ 0.5, n = 45) | 0.219 | **0.007** |
| Dates where this formula is the closer one | 0 | **140** |

On this field, IFH showed 0.53 for 28 Mar 2026 and 0.52 for 29 Sep 2026. Copernicus Browser gave 0.758 and 0.776. The offset-removed values were 0.765 and 0.776.

**Conclusion:** Copernicus Browser removes the offset and Planetary Computer does not. Before build 2026.11.07-b, IFH's NDVI read 0.2–0.3 too low on green crops and disagreed with its own verification links.

## History
- **August 2026:** the same gap was found on one field, 0.54 in IFH against 0.74/0.81 in Copernicus Browser.
- **The correction worked:** with the offset removed, IFH read 0.79.
- **It was later dropped:** over dark pixels `B08+B04−2000` approaches zero, and one field read 210,059. The expression engine had no `max` or `abs` with which to guard against that.
- **A comment in the code** then recorded that the plain formula "matched" Copernicus. That comment appears to mix up two separate checks.
- **7 Nov 2026:** both tests above, plus the documentation, settle it.

## What changed in build 2026.11.07-b
- **NDVI** = `(B08′ − B04′) / (B08′ + B04′ + 1)`, where `band′ = where(band > 1000, band − 1000, 0)`.
  - This is Microsoft's clip-and-subtract method. The `+1` keeps the denominator above zero, so the value always stays within [−1, 1].
  - It was tested on dark targets (Mosul Dam lake, the Tigris in Baghdad): no blow-ups.
- **NDMI:** the same correction, applied to B08 and B11.
- **Scenes on a processing baseline before 04.00** keep the plain formula. None fall inside the app's two-year window.
- **Health bands moved to the corrected scale:**
  - Poor < 0.30 ≤ Fair < 0.60 ≤ Good. Previously 0.20 / 0.45 on the old scale.
  - Moisture: dry < 0 ≤ moderate < 0.30 ≤ good. Previously 0.20.
  - On field PP1CC5, an old 0.20 corresponds to about 0.29 corrected, and an old 0.45 to about 0.62–0.75.
- **Saved fields and the Ranking list** from older builds lose their colour and year-on-year figure until the field is opened again, because those numbers were on the old scale.

## Reproduce it
```bash
python compare_copernicus.py --summary comparison_field_PP1CC5.csv
python compare_copernicus.py --outline field_PP1CC5_outline.geojson \
       --copernicus copernicus_export_field_PP1CC5.csv --out my_comparison.csv   # needs internet, requests
```

To test any other field:
1. Draw it in Copernicus Browser, open Statistical Info and export the CSV.
2. Save the field's outline as GeoJSON.
3. Run the second command on those two files.
