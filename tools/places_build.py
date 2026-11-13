"""Build places/iraq_places.pmtiles: village, town and city names for the map labels.

Input: an OpenStreetMap extract of Iraq's place nodes from Overpass, saved as JSON. Query:

    [out:json][timeout:120];
    area["ISO3166-1"="IQ"][admin_level=2]->.a;
    node["place"~"^(city|town|village|hamlet|suburb|locality|isolated_dwelling)$"](area.a);
    out qt;

Either the raw Overpass JSON ({"elements": [...]}) or the trimmed form saved from the browser
({"places": [[osm_id, lon, lat, tags], ...]}) is accepted.

Output: one vector layer "places" with, per point:
  r   rank (1 city, 2 town, 3 village, 4 hamlet or suburb); bigger places win label collisions
  en  name:en, else name
  ar  name:ar, else name
  ku  name:ckb, else name:ku when it is in Arabic script (name:ku is mostly Latin Kurmanji), else name
and a per-feature minzoom: city 6 (7 if population under 100,000), town 9 (8 if 50,000 or more),
village 10, hamlet 11, suburb 12. Localities and isolated dwellings are left out: in Iraq most are
valleys, mountains, ruins and wells, which confuse someone looking for a village.

Needs tippecanoe on the PATH (pip install tippecanoe).
Usage: python tools/places_build.py iraq_places_osm.json places/iraq_places.pmtiles
Data: (c) OpenStreetMap contributors, ODbL 1.0.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ARABIC = re.compile("[؀-ۿ]")
MINZOOM = {"city": 6, "town": 9, "village": 10, "hamlet": 11, "suburb": 12}
RANK = {"city": 1, "town": 2, "village": 3, "hamlet": 4, "suburb": 4}


def records(d):
    if "places" in d:
        for row in d["places"]:
            _, lon, lat, tags = row if len(row) == 4 else (None, *row)
            yield lon, lat, tags
    else:
        for e in d.get("elements", []):
            if e.get("type") == "node":
                yield e.get("lon"), e.get("lat"), e.get("tags", {})


def population(tags):
    try:
        return int(str(tags.get("population", "0")).replace(",", "").split()[0])
    except (ValueError, IndexError):
        return 0


def main(src, out):
    d = json.load(open(src, encoding="utf-8"))
    feats, skipped = [], 0
    for lon, lat, t in records(d):
        place = t.get("place")
        name = t.get("name") or t.get("name:ar") or t.get("name:en") or t.get("name:ckb")
        if place not in MINZOOM or not name or lon is None or lat is None:
            skipped += 1
            continue
        ku = t.get("name:ku")
        ku = ku if ku and ARABIC.search(ku) else None
        mz = MINZOOM[place]
        pop = population(t)
        if place == "town" and pop >= 50000:
            mz = 8
        if place == "city" and 0 < pop < 100000:
            mz = 7
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"r": RANK[place], "en": t.get("name:en") or name,
                           "ar": t.get("name:ar") or name, "ku": t.get("name:ckb") or ku or name},
            "tippecanoe": {"minzoom": mz},
        })
    with tempfile.TemporaryDirectory() as tmp:
        gj = os.path.join(tmp, "places.geojson")
        json.dump({"type": "FeatureCollection", "features": feats}, open(gj, "w", encoding="utf-8"),
                  ensure_ascii=False)
        subprocess.run(["tippecanoe", "-q", "-f", "-o", out, "-l", "places", "-Z6", "-z12", "-r1",
                        "--no-feature-limit", "--no-tile-size-limit",
                        "--attribution=© OpenStreetMap contributors (ODbL)", "-n", "Iraq places (OSM)", gj],
                       check=True)
    print(f"{len(feats)} places written to {out} ({os.path.getsize(out):,} bytes); {skipped} skipped")


if __name__ == "__main__":
    main(*sys.argv[1:3])
