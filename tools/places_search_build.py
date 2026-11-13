"""Build places/iraq_places_search.json: the names behind the search box's suggestions.

Input: the same OpenStreetMap extract that places_build.py uses (see its docstring for the
Overpass query). Same places as the map labels: cities, towns, villages, hamlets and suburbs;
localities and isolated dwellings are left out.

Output: compact JSON, loaded by the app the first time someone uses the search box:
  {"v": 1, "f": [...field names...], "p": [[lon, lat, type, name, en, ar, ku, kmr, near], ...]}
  lon, lat  4 decimals (about 10 m)
  type      1 city, 2 town, 3 village, 4 hamlet, 5 suburb
  name      the OSM name tag
  en ar ku  name:en, name:ar and Sorani (name:ckb, else name:ku in Arabic script), each left
            empty when it is the same as name, to keep the file small
  kmr       name:ku in Latin script (Kurmanji), searched but not shown
  near      index of the nearest city or town within 40 km (-1 if none), shown as "near ..."
            so villages that share a name can be told apart

Usage: python tools/places_search_build.py iraq_places_osm.json places/iraq_places_search.json
Data: (c) OpenStreetMap contributors, ODbL 1.0.
"""
import json
import math
import re
import sys

ARABIC = re.compile("[؀-ۿ]")
TYPE = {"city": 1, "town": 2, "village": 3, "hamlet": 4, "suburb": 5}


def records(d):
    if "places" in d:
        for row in d["places"]:
            _, lon, lat, tags = row if len(row) == 4 else (None, *row)
            yield lon, lat, tags
    else:
        for e in d.get("elements", []):
            if e.get("type") == "node":
                yield e.get("lon"), e.get("lat"), e.get("tags", {})


def km(a, b):
    dx = (a[0] - b[0]) * 111.32 * math.cos(math.radians((a[1] + b[1]) / 2))
    dy = (a[1] - b[1]) * 110.57
    return math.hypot(dx, dy)


def main(src, out):
    d = json.load(open(src, encoding="utf-8"))
    rows = []
    for lon, lat, t in records(d):
        typ = TYPE.get(t.get("place"))
        name = t.get("name") or t.get("name:ar") or t.get("name:en") or t.get("name:ckb")
        if not typ or not name or lon is None or lat is None:
            continue
        ku_tag = t.get("name:ku") or ""
        ku = t.get("name:ckb") or (ku_tag if ARABIC.search(ku_tag) else "")
        kmr = ku_tag if ku_tag and not ARABIC.search(ku_tag) else ""
        same = lambda v: "" if (not v or v == name) else v
        rows.append([round(lon, 4), round(lat, 4), typ, name,
                     same(t.get("name:en")), same(t.get("name:ar")), same(ku), same(kmr), -1])
    # biggest first, so the app's ties go to cities and towns
    rows.sort(key=lambda r: (r[2], r[3]))
    hubs = [i for i, r in enumerate(rows) if r[2] <= 2]
    for r in rows:
        if r[2] <= 2:
            continue
        best, bd = -1, 40.0
        for i in hubs:
            h = rows[i]
            if abs(h[1] - r[1]) > 0.4 or abs(h[0] - r[0]) > 0.5:
                continue
            dist = km((r[0], r[1]), (h[0], h[1]))
            if dist < bd:
                best, bd = i, dist
        r[8] = best
    doc = {"v": 1, "source": "OpenStreetMap contributors, ODbL 1.0",
           "f": ["lon", "lat", "type", "name", "en", "ar", "ku", "kmr", "near"], "p": rows}
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
    near = sum(1 for r in rows if r[8] >= 0)
    print(f"{len(rows)} places written to {out}; {near} have a nearby town")


if __name__ == "__main__":
    main(*sys.argv[1:3])
