# Iraq Farms Health

**A free, trilingual satellite tool that shows the vegetation health of farm fields across Iraq — designed for smallholder farmers to use on a phone.**

🌐 Live at **[iraqfarmshealth.com](https://iraqfarmshealth.com)**

Tap any field on the map to see how healthy its crops are right now, view a two-year trend, and compare this season to last year. Works in **English**, **Arabic (العربية)**, and **Kurdish (کوردی)**. Every reading can be independently verified against the European Space Agency's Copernicus Browser.

---

## What it does

- **Find my location.** Don't know your field's coordinates? Tap the location button and the map jumps to where you're standing, so you can find your own field on the map.
- **Tap a field, see its health.** Field boundaries come from the open [Fields of the World](https://fieldsofthe.world/) dataset. Tap any field and the tool reads recent Sentinel-2 satellite imagery to calculate its NDVI (a standard measure of plant health).
- **Two-year history.** A month-by-month chart shows how the field's vegetation has changed over the past two years.
- **Year-on-year comparison.** See at a glance whether this season is greener or drier than the last.
- **Moisture reading.** Alongside vegetation health, the tool reads the field's canopy moisture (NDMI) and tells you whether it's wetter or drier than nearby fields.
- **Field size.** Each field's area is shown in donums.
- **Watch it grow.** When a field's data has loaded, its last 12 months play once on the map by themselves (about 5 seconds), ending on today. **Watch month by month** plays the full two years, with pause and a chart you can drag along. Each frame is the field coloured by its NDVI (greenness) in that month's satellite image, from the same scene as that month's reading.
- **Rainfall.** The field's rainfall over the last 12 months against the 12 before, from Open-Meteo's weather archive, with a month-by-month strip in the report.
- **Health map overlay.** Colour every visible field by its current health at once — green for healthy, red for stressed — to spot problems across a whole area.
- **See where it's green, country-wide.** Zoomed out, a NASA MODIS greenness layer shows where vegetation is growing across Iraq right now; zoom in and individual fields take over. The Health map button switches both on and off.
- **Where wheat or barley grew (🌾 Crops).** Shows the European Space Agency's WorldCereal 2021 map of winter cereals in magenta, and a field's card says whether wheat or barley grew there in 2021. It is a past record, not this season.
- **Rivers, lakes and marshes.** A water layer shows how often each place has been under water since 1984 (EU Joint Research Centre), for orientation.
- **Save & rank your fields.** Bookmark fields you care about, and see which of your fields improved most since last year.
- **Share a field.** On a phone, Share opens the phone's share sheet (WhatsApp, Messages…); on a computer it copies a link to the field.
- **Shareable field report.** One image with everything about the field — health, two-year chart, monthly readings, the last 12 months' images, rainfall, moisture, size, how it compares with nearby fields, and a small map with roads and place names. On a phone it opens the share sheet (Save Image, WhatsApp…); on a computer it downloads.
- **Verify anything.** Each reading links out to the free Copernicus Browser, opened on the same field and date, so you can check the numbers yourself.

## Who it's for

Smallholder farmers, agronomists, agricultural suppliers, researchers, and journalists who want a quick, trustworthy read on crop health anywhere in Iraq — with no login, no cost, and nothing to install.

---

## How it works (in brief)

The app is a **single, self-contained HTML file**. It runs entirely in the browser — there is no backend server and no database. Your saved fields and history are stored only on your own device.

- **Base map:** Esri World Imagery (satellite) with Esri reference layers for roads, place names, and boundaries.
- **Field boundaries:** Fields of the World (FTW) 2025 field polygons, from FTW's Iraq-only [PMTiles](https://protomaps.com/docs/pmtiles) file on [source.coop](https://source.coop/ftw/global-data), copied unchanged to Cloudflare R2 and served from `tiles.iraqfarmshealth.com` (the outlines appear in under a second instead of 6–7 s from the 2.1 TB global file). To refresh it, upload a new `Iraq.pmtiles` to the `ifh-tiles` bucket as `fields/Iraq.pmtiles`.
- **Vegetation & moisture data:** Sentinel-2 L2A imagery via Microsoft's [Planetary Computer](https://planetarycomputer.microsoft.com/), which computes NDVI and NDMI statistics per field.
- **Country-wide greenness (low zoom):** NASA MODIS Terra 8-day NDVI via NASA GIBS, shown until individual fields appear.
- **Rainfall:** [Open-Meteo](https://open-meteo.com/)'s historical weather archive (ECMWF's ERA5 and ERA5-Land reanalyses and IFS model, grids of about 9–25 km), one request per field.
- **Winter cereals 2021 (🌾 Crops):** ESA WorldCereal 2021 winter-cereals product, served as map tiles by VITO's Terrascope.
- **Surface water:** JRC Global Surface Water occurrence tiles (EU Joint Research Centre / Google).
- **Village and town names:** [OpenStreetMap](https://www.openstreetmap.org/) place names (about 12,700 cities, towns, villages, hamlets and suburbs) in the visitor's language: Arabic, Sorani Kurdish where tagged (otherwise the local name), or English. Built by `tools/places_build.py` into `places/iraq_places.pmtiles` (1.8 MB; a phone fetches only the tiles in view). Cities from zoom 6–7, towns 8–9, villages 10, hamlets 11.
- **Place search:** the search box suggests villages, towns and neighbourhoods as you type, from the same OpenStreetMap extract: `tools/places_search_build.py` writes `places/iraq_places_search.json` (0.96 MB, about 300 KB compressed), loaded the first time someone uses the search box. Arabic, Sorani and Latin spellings are matched to each other. Only when nothing matches and Enter is pressed is the text sent to OpenStreetMap's [Nominatim](https://nominatim.org/) search, once per search, within its [usage policy](https://operations.osmfoundation.org/policies/nominatim/).
- **Map rendering:** [MapLibre GL JS](https://maplibre.org/).

For a full description of the data sources, the NDVI calculation, and the tool's limitations, see **[METHODOLOGY.md](METHODOLOGY.md)**.

---

## Crop map and how it was checked

The site also shows a 2025-26 winter-cereal map of Iraq (`crops/2026/`), made with the ESA WorldCereal models at 10 m resolution. Its accuracy has been checked against each location's own Sentinel-2 history:

- **Southern tiles (67 tiles, 10.5 Mha), stratified random sample of 575 points:** where the map says "confident cereal", a winter crop grew 96% of the time (95% CI 92–99%). The map catches 71% (65–77%) of the winter-crop area. Winter-crop area 1.91 Mha (1.75–2.06), against 1.41 Mha mapped.
- **Northern tiles:** field checks showed rain-fed cereal is often under-counted. These tiles are being re-run with a later season and will then be assessed the same way.

The method, data and scripts are in **[validation/](validation/README.md)**, so anyone can repeat the checks and get the same results.

---

## Running it yourself

Because it's a single static file, hosting is trivial:

1. Download `index.html`.
2. Serve it over HTTPS (GitHub Pages, Netlify, or any static host). Opening the file directly from disk (`file://`) will not work reliably, because browsers restrict the network requests the tool depends on. (In particular, the "Find my location" button requires HTTPS.)

This repository is deployed via **GitHub Pages** with a custom domain.

### Files

| File | Purpose |
|------|---------|
| `index.html` | The entire application — commented source and what the site serves. |
| `robots.txt`, `sitemap.xml` | Search-engine crawler files. |
| `favicon.svg` | Site icon. |
| `preview.jpg` | The picture shown when a link to the site is shared (WhatsApp, Facebook, X). |
| `CNAME` | The custom domain for GitHub Pages (iraqfarmshealth.com). |
| `LICENSE` | MIT licence for the code. |
| `README.md` | This file. |
| `METHODOLOGY.md` | How the data is derived, and its limitations. |
| `crops/` | The published crop map layers (map cells, statistics, boundaries). |
| `tools/` | Notebooks that build and publish the crop map (WorldCereal on CDSE openEO). |
| `validation/` | How the crop map was checked: method, data, scripts and results. |

The map library (MapLibre GL JS) and PMTiles are loaded from a public CDN (jsDelivr), pinned to specific versions for stability, so they are not committed to this repo.

---

## Data sources & credits

- **Satellite imagery:** [Copernicus Sentinel-2](https://sentinel.esa.int/web/sentinel/missions/sentinel-2) (European Space Agency), accessed via [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/). Contains modified Copernicus Sentinel data 2024–2026.
- **Field boundaries:** [Fields of the World](https://fieldsofthe.world/) (FTW).
- **Crop map 2025-26:** [ESA WorldCereal](https://esa-worldcereal.org/) models, run on the [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/) (openEO).
- **Winter cereals 2021 (🌾 Crops):** [ESA WorldCereal 2021](https://esa-worldcereal.org/) products (CC BY 4.0), served by [VITO Terrascope](https://terrascope.be/).
- **Rainfall:** [Open-Meteo](https://open-meteo.com/) historical weather API (CC BY 4.0), built on ECMWF's ERA5 / ERA5-Land reanalyses and IFS model. Generated using Copernicus Climate Change Service information.
- **Surface water:** [JRC Global Surface Water](https://global-surface-water.appspot.com/) (EC Joint Research Centre / Google).
- **Country-wide greenness:** NASA MODIS Terra NDVI via [NASA GIBS](https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api).
- **Base imagery & reference layers:** [Esri World Imagery](https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9) (Esri, Maxar, Earthstar Geographics) and Esri reference layers.
- **Village and town names:** © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) (ODbL 1.0). Extract of 13 Nov 2026; `places/iraq_places.pmtiles` and `places/iraq_places_search.json` are available under the same licence. Search fallback: [Nominatim](https://nominatim.openstreetmap.org/) (OpenStreetMap Foundation).
- **District boundaries (crop page statistics):** [geoBoundaries](https://www.geoboundaries.org/) (CC BY 4.0).
- **Independent verification:** [Copernicus Browser](https://dataspace.copernicus.eu/browser/) (ESA / Copernicus Data Space Ecosystem).
- **Mapping:** [MapLibre GL JS](https://maplibre.org/), [PMTiles](https://protomaps.com/docs/pmtiles).

The map lists the credits for what is on screen under its ⓘ button, and the field report names its sources in its footer.

## Privacy

- **No account, no personal details.** The tool has no login and asks for no name, phone number or email.
- **On your device.** Saved fields, your ranking list and your language choice are kept in your browser's local storage, on your device only.
- **"My location"** is used only to move the map to where you are. It is not stored or sent anywhere by the tool, but, like any position on the map, it ends up in the page address (see below).
- **What the data services see.** To read a field, the browser sends that field's outline to Microsoft Planetary Computer (satellite readings), its centre point to Open-Meteo (rainfall), and asks Terrascope for the 2021 crop-map tiles around it. Map pictures come from Esri, NASA and Google; fonts from Google; the map library from jsDelivr. These services see the request and your internet address, as with any website.
- **Usage counts.** The site uses [GoatCounter](https://www.goatcounter.com/) (since 14 Nov 2026, replacing Microsoft Clarity): no cookies, no recordings. It counts each visit as `/` (the map position and field in the page address are not sent), with the referring site, device and browser type, screen size and country, and a few actions by name only (`field-open`, `fields-in-visit-N` when a visit reaches 1, 2, 3, 5, 10 and 20 different fields, `random-farm`, `watch-months`, `save-field`, `share`, `report`, `my-location`, the guide, the language, and the kind of search and whether it found anything). It never receives which field was opened, where on the map, or what was typed. The same notice in English, Arabic and Kurdish is at [iraqfarmshealth.com/privacy/](https://iraqfarmshealth.com/privacy/).

## License & use

- **Code** (`index.html`, `crops/`, `tools/`, `validation/` scripts): [MIT](LICENSE).
- **Crop map data** (`crops/2026/`, `crops/2026p/`): CC BY 4.0. Credit: "Crop types: ESA WorldCereal system, run by Iraq Farms Health on Copernicus Data Space. Contains modified Copernicus Sentinel data 2025–2026."
- **Validation data** (`validation/`): CC BY 4.0. Credit: "Iraq Farms Health".
- **Third-party data** shown in the app (Esri imagery, Fields of the World, WorldCereal 2021, JRC water, NASA GIBS, Open-Meteo) stays under its providers' own terms; follow the links above.

---

*Part of a portfolio of open-data civic tools for Iraq.*
