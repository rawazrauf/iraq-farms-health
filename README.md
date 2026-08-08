# Iraq Farms Health

**A free, trilingual satellite tool that shows the vegetation health of farm fields across Iraq — designed for smallholder farmers to use on a phone.**

🌐 Live at **[www.iraqfarmshealth.com](https://www.iraqfarmshealth.com)**

Tap any field on the map to see how healthy its crops are right now, view a two-year trend, and compare this season to last year. Works in **English**, **Arabic (العربية)**, and **Kurdish (کوردی)**. Every reading can be independently verified against the European Space Agency's Copernicus Browser.

---

## What it does

- **Tap a field, see its health.** Field boundaries come from the open [Fields of the World](https://fieldsofthe.world/) dataset. Tap any field and the tool reads recent Sentinel-2 satellite imagery to calculate its NDVI (a standard measure of plant health).
- **Two-year history.** A month-by-month chart shows how the field's vegetation has changed over the past two years.
- **Year-on-year comparison.** See at a glance whether this season is greener or drier than the last.
- **Health map overlay.** Colour every visible field by its current health at once — green for healthy, red for stressed — to spot problems across a whole area.
- **Save & rank your fields.** Bookmark fields you care about, and see which of your fields improved most since last year.
- **Verify anything.** Each reading links out to the free Copernicus Browser, opened on the same field and date, so you can check the numbers yourself.

## Who it's for

Smallholder farmers, agronomists, agricultural suppliers, researchers, and journalists who want a quick, trustworthy read on crop health anywhere in Iraq — with no login, no cost, and nothing to install.

---

## How it works (in brief)

The app is a **single, self-contained HTML file**. It runs entirely in the browser — there is no backend server and no database. Your saved fields and history are stored only on your own device.

- **Base map:** Esri World Imagery (satellite) with Esri reference layers for roads, place names, and boundaries.
- **Field boundaries:** Fields of the World (FTW) global field polygons, served as [PMTiles](https://protomaps.com/docs/pmtiles).
- **Vegetation data:** Sentinel-2 L2A imagery via Microsoft's [Planetary Computer](https://planetarycomputer.microsoft.com/), which computes NDVI statistics per field.
- **Map rendering:** [MapLibre GL JS](https://maplibre.org/).

For a full description of the data sources, the NDVI calculation, and the tool's limitations, see **[METHODOLOGY.md](METHODOLOGY.md)**.

---

## Running it yourself

Because it's a single static file, hosting is trivial:

1. Download `index.html`.
2. Serve it over HTTPS (GitHub Pages, Netlify, or any static host). Opening the file directly from disk (`file://`) will not work reliably, because browsers restrict the network requests the tool depends on.

This repository is deployed via **GitHub Pages** with a custom domain.

### Files

| File | Purpose |
|------|---------|
| `index.html` | The entire application — commented source and what the site serves. |
| `robots.txt`, `sitemap.xml` | Search-engine crawler files. |
| `favicon.svg` | Site icon. |
| `README.md` | This file. |
| `METHODOLOGY.md` | How the data is derived, and its limitations. |

The map library (MapLibre GL JS) and PMTiles are loaded from a public CDN (jsDelivr), pinned to specific versions for stability, so they are not committed to this repo.

---

## Data sources & credits

- **Satellite imagery:** [Copernicus Sentinel-2](https://sentinel.esa.int/web/sentinel/missions/sentinel-2) (European Space Agency), accessed via [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/).
- **Field boundaries:** [Fields of the World](https://fieldsofthe.world/) (FTW).
- **Base imagery & reference layers:** [Esri World Imagery](https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9).
- **Independent verification:** [Copernicus Browser](https://dataspace.copernicus.eu/browser/) (ESA / Copernicus Data Space Ecosystem).
- **Mapping:** [MapLibre GL JS](https://maplibre.org/), [PMTiles](https://protomaps.com/docs/pmtiles).

## Privacy

The tool has no login and collects no personal data. Saved fields and history stay on your device (browser local storage). The site uses Microsoft Clarity for anonymous, aggregated usage analytics (to understand how the tool is used and improve it).

## License & use

This is a civic, public-good project. The satellite data and field boundaries are provided under the licenses of their respective sources (see links above); please respect those terms. Attribution to the underlying data providers (ESA/Copernicus, Esri, Fields of the World) is required and is shown in the app.

---

*Part of a portfolio of open-data civic tools for Iraq.*
