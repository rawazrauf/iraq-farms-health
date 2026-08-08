# Methodology

This document explains how **Iraq Farms Health** derives the numbers it shows, and — just as importantly — what those numbers *cannot* tell you. The tool is meant to be trustworthy and verifiable, so this is written to be honest about both its methods and its limits.

If you only read one thing: **the health readings are estimates from satellite imagery, not ground truth. They are a useful signal, not a measurement of your specific crop. Every reading can and should be checked against the source (see [Verification](#verification)).**

---

## 1. What "vegetation health" means here

The tool measures **NDVI** — the Normalized Difference Vegetation Index. NDVI is a long-established, widely used indicator of how much live green vegetation is present in an area. It is calculated from two bands of satellite imagery:

```
NDVI = (NIR − Red) / (NIR + Red)
```

where **NIR** is near-infrared light and **Red** is visible red light. Healthy, dense vegetation strongly reflects near-infrared and absorbs red, producing a high NDVI. Bare soil, water, and stressed or sparse vegetation produce low NDVI.

NDVI ranges from **−1 to +1** in theory. In practice:

- **Below ~0.2** — bare soil, water, built-up land, or very sparse/stressed vegetation.
- **~0.2 to ~0.45** — moderate vegetation (early growth, partial cover, or some stress).
- **Above ~0.45** — dense, healthy vegetation.

The tool maps these to three plain-language bands shown to the user:

| NDVI | Health band | Colour |
|------|-------------|--------|
| < 0.20 | **Poor** | clay / red |
| 0.20 – 0.45 | **Fair** | wheat / yellow |
| ≥ 0.45 | **Good** | green |

> **Important:** these thresholds are general defaults, not calibrated to specific Iraqi crops, growth stages, or seasons. A "Poor" reading in mid-summer may simply mean the field is between plantings, not that anything is wrong. NDVI reflects *greenness*, which is related to but not the same as crop *health* or *yield*.

---

## 2. Data sources

### Satellite imagery — Sentinel-2

Imagery comes from the **Copernicus Sentinel-2** mission (European Space Agency), which images all of Iraq roughly every five days at 10-metre resolution. The tool accesses Sentinel-2 **Level-2A** (surface reflectance) scenes through **Microsoft's Planetary Computer**.

For each field reading, the tool searches recent Sentinel-2 scenes over that field, preferring scenes with low cloud cover, and computes NDVI statistics for the field's exact boundary.

### Field boundaries — Fields of the World (FTW)

Field outlines come from **Fields of the World (FTW)**, an open, machine-learning-derived dataset of agricultural field boundaries covering many countries including all of Iraq. Boundaries are served efficiently to the browser as **PMTiles**.

> **Important:** FTW boundaries are *predictions* from a model, not an official cadastre. Some real fields are missed; some detected "fields" may not be cultivated; and boundaries may not perfectly match a field's true edges — especially in dense, irregular, or small-plot areas. If your field is not outlined, the tool cannot read it. Field outlines are only shown at close zoom (zoom level 13 and above) to avoid clutter and misleading detections over towns.

### Base map & reference layers — Esri

The satellite base map and the roads / place-name / boundary reference layers are **Esri World Imagery** and Esri reference services.

---

## 3. How a field reading is computed

When you tap a field:

1. The field's **boundary polygon** (from FTW) is used as the exact area of interest.
2. The tool asks Planetary Computer's statistics service for NDVI over that polygon, for a recent time window, across candidate Sentinel-2 scenes (least-cloudy first).
3. It reads the **median** NDVI of all the pixels inside the field for the chosen scene.

**Why the median and not the average?** A field can contain a few anomalous pixels — a shadow, a building, a patch of water, or a sensor artefact — that would distort a simple average. The median (the middle value) is robust to those outliers and better represents the typical condition of the field. Any value that falls outside the physically possible NDVI range of −1 to +1 is rejected as invalid, and the tool tries the next available scene.

### The two-year history

The month-by-month chart repeats this process for each of the past 24 months, building a picture of how the field's vegetation rises and falls with the seasons. Months with no clear (cloud-free) imagery are left blank rather than guessed.

### The year-on-year comparison

To compare this year with last year, the tool computes the **area under the NDVI curve** for the most recent 12 months and for the 12 months before that — essentially, the total "greenness over time" of each year — and compares them. This is more meaningful than comparing a single month to the same month a year earlier, because it captures the whole season rather than one snapshot.

- The comparison is only shown when both years have enough clear months of data to be trustworthy.
- A **percentage change** is shown only when last year's baseline was high enough (mean NDVI ≥ 0.20) for a percentage to be meaningful, and the result is capped at ±300%. On a nearly-bare field, a tiny change can produce an enormous, misleading percentage — so in those cases the tool shows the absolute NDVI change instead. This is a deliberate guard against nonsense figures.

---

## 4. The health map overlay

The **Health map** colours whole fields at once. When it is on, the tool samples the current-month NDVI for the fields visible on screen (largest first, up to a capped number to limit load) and fills each field polygon with its health colour.

Colours appear **only inside detected fields** — never over rivers, roads, towns, or bare land. This is deliberate: it means green outside a field is just the satellite image, not a health reading, and it makes the tappable fields obvious. Fields colour in progressively as their readings return; very small fields, or fields with no recent clear imagery, may remain uncoloured (this is honest — the tool does not guess).

---

## 5. Verification

**You do not have to take the tool's word for anything.** Each reading links out to the **[Copernicus Browser](https://dataspace.copernicus.eu/browser/)** — the European Space Agency's own free tool — opened on the same location. There you can view the raw Sentinel-2 imagery, switch to the NDVI layer, draw the same field, and read the official statistics yourself.

During development, the tool's readings were cross-checked against Copernicus Browser's own NDVI statistics to confirm they agree. This kind of independent verification is the recommended way to use any satellite-derived figure: treat the tool as a fast first look, and confirm anything important against the source.

---

## 6. Known limitations

Being clear about limitations is part of being trustworthy. In summary:

- **NDVI is greenness, not yield or crop health directly.** It correlates with vegetation vigour but does not measure crop type, water stress specifics, disease, or harvest quantity.
- **Thresholds are generic**, not calibrated to Iraqi crops or growth calendars. Interpret Poor/Fair/Good as rough guidance.
- **Field boundaries are model predictions.** Fields can be missed, mis-drawn, or falsely detected. If a field isn't outlined, it can't be read.
- **Clouds create gaps.** Sentinel-2 is optical and cannot see through cloud. Cloudy periods leave blanks in the history, and "current" always means the latest *clear* image, which may be several days old.
- **"Current" is not live.** Satellites revisit every few days, and cloud-free imagery may be older still. Readings reflect the most recent usable pass, not today.
- **Resolution is 10 metres.** Very small plots may be represented by few pixels, making their readings noisier and less reliable.
- **Mixed pixels at edges.** Pixels along a field's boundary may include roads, canals, or neighbouring fields, slightly affecting the statistics.

None of these make the tool useless — they define the conditions under which its signal is strong (clear skies, larger fields, seasonal trends) versus weak (cloudy days, tiny plots, single-day precision). Used with that understanding, and verified against the source, it is a genuinely useful window on how Iraq's farmland is doing.

---

## 7. Reproducibility

The entire tool is a single, commented HTML file. Anyone can read exactly how every number is produced — the NDVI expression, the median selection, the range checks, the year-on-year integral, and the thresholds are all in the source, not hidden behind a server. There is no proprietary processing step. Combined with the verification links, this means every figure the tool shows can be traced, reproduced, and independently checked.

---

*Questions, corrections, or improvements to this methodology are welcome — accuracy and honesty about limitations are the point.*
