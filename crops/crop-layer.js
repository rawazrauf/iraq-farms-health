/* Iraq crop layer — shared by /crops/ and Iraq Farms Health.
 *
 * Streams the published WorldCereal crop codes (cloud-optimised GeoTIFFs in EPSG:3857,
 * aligned to web-map tiles) straight from static hosting with HTTP range requests:
 *   - as a MapLibre raster layer through the "wcrop://{z}/{x}/{y}" protocol,
 *   - as single-pixel lookups (what was mapped here?),
 *   - as GeoTIFF downloads of an area of interest.
 * Needs geotiff.js loaded first (global `GeoTIFF`).
 *
 * Pixel codes: 0 = not cropland / not processed; 1 + WorldCereal class index;
 * +100 when WorldCereal's own confidence was below the threshold ("less sure").
 */
(function (global) {
  "use strict";
  const R = 20037508.342789244;
  const LESS = 100;

  const CropLayer = {
    base: "",
    index: null,
    opts: { show: { wheat: true, barley: true, other: true, nocrop: true }, fadeLess: true, mode: "crops" },
    // ESA WorldCereal 2021 v100 winter cereals (official product), the same service Iraq Farms Health uses.
    WC21_URL: "https://wmts.terrascope.be/wmts?service=WMTS&request=GetTile&version=1.0.0"
      + "&layer=esa-worldcereal-wintercereals-10m-2021-v1_classification&style=default&format=image%2Fpng"
      + "&tilematrixset=EPSG:3857&TileMatrix={z}&TileRow={y}&TileCol={x}&TIME=2021-01-01"
      + "&name=classification&assets=classification&nodata=255&colormap=" + encodeURIComponent('{"100":"#ff0000"}'),
    DIFF_COLORS: { both: [46, 125, 50, 235], only2026: [227, 181, 5, 235], only2021: [123, 63, 160, 235], y2021: [186, 113, 53, 225] },
    _wc21: new Map(),
    _proc: new Map(),
    _tiffs: new Map(),
    _codes: new Map(),
    _lut: null,
    _blank: null,

    /** Load index.json from the data folder (URL ending in "/"). */
    async init(base) {
      this.base = base.endsWith("/") ? base : base + "/";
      const r = await fetch(this.base + "index.json", { cache: "no-cache" });
      if (!r.ok) throw new Error("Crop layer index not found (" + r.status + ")");
      this.index = await r.json();
      this.cellSet = new Map(this.index.cells.map(c => [c.x + "/" + c.y, c]));
      // processed footprint (finished tiles), in Web Mercator, for the 2021 comparison
      this._footprint = (this.index.processed || []).map(t => t.ring.map(([lon, lat]) => this.lonLatTo3857(lon, lat)));
      const cl = this.classes();
      this._winter = new Set(cl.map((c, i) => ["wheat", "barley", "rye", "oats"].includes(c) ? i + 1 : 0).filter(Boolean));
      this._buildLut();
      return this.index;
    },

    classes() { return this.index.codes.classes; },
    colors() { return this.index.codes.colors; },

    /** Group used by the on/off toggles. */
    groupOf(code) {
      if (!code) return null;
      const c = this.classes()[(code % LESS) - 1];
      if (c === "wheat") return "wheat";
      if (c === "barley") return "barley";
      if (c === "no_crop") return "nocrop";
      return "other";
    },

    describe(code) {
      if (!code) return { cls: null, less: false };
      return { cls: this.classes()[(code % LESS) - 1] || null, less: code > LESS };
    },

    setOptions(o) {
      Object.assign(this.opts, o);
      if (o && o.show) this.opts.show = Object.assign({}, this.opts.show, o.show);
      this._buildLut();
    },

    _buildLut() {
      if (!this.index) return;
      const lut = new Uint8ClampedArray(256 * 4);
      const cols = this.colors();
      for (let v = 1; v < 256; v++) {
        const ci = (v % LESS) - 1;
        if (ci < 0 || ci >= cols.length || v >= 2 * LESS) continue;
        const g = this.groupOf(v);
        if (!this.opts.show[g]) continue;
        const h = cols[ci];
        lut[v * 4] = parseInt(h.slice(1, 3), 16);
        lut[v * 4 + 1] = parseInt(h.slice(3, 5), 16);
        lut[v * 4 + 2] = parseInt(h.slice(5, 7), 16);
        lut[v * 4 + 3] = v > LESS && this.opts.fadeLess ? 115 : (g === "nocrop" ? 150 : 235);
      }
      this._lut = lut;
    },

    _open(file) {
      if (!this._tiffs.has(file)) {
        this._tiffs.set(file, GeoTIFF.fromUrl(this.base + file, { allowFullFile: false, cacheSize: 200 })
          .then(async t => {
            const n = await t.getImageCount();
            const imgs = [];
            for (let i = 0; i < n; i++) imgs.push(await t.getImage(i));
            const o = imgs[0].getOrigin(), r0 = imgs[0].getResolution();
            return imgs.map(im => {
              const r = im.getResolution(imgs[0]);
              return { im, ox: o[0], oy: o[1], rx: Math.abs(r[0] || r0[0]), ry: Math.abs(r[1] || r0[1]),
                       w: im.getWidth(), h: im.getHeight() };
            });
          })
          .catch(e => { this._tiffs.delete(file); throw e; }));
      }
      return this._tiffs.get(file);
    },

    /** Read crop codes for a 3857 box into an out x out grid (nearest neighbour). */
    async _readBox(file, b, outW, outH, signal) {
      const levels = await this._open(file);
      const want = (b[2] - b[0]) / outW;
      // finest level that is not finer than needed
      let L = levels[0];
      for (const lv of levels) if (lv.rx <= want * 1.001) L = lv;
      const wx0 = (b[0] - L.ox) / L.rx, wx1 = (b[2] - L.ox) / L.rx;
      const wy0 = (L.oy - b[3]) / L.ry, wy1 = (L.oy - b[1]) / L.ry;
      const ix0 = Math.max(0, Math.floor(wx0)), ix1 = Math.min(L.w, Math.ceil(wx1));
      const iy0 = Math.max(0, Math.floor(wy0)), iy1 = Math.min(L.h, Math.ceil(wy1));
      const out = new Uint8Array(outW * outH);
      if (ix1 <= ix0 || iy1 <= iy0) return out;
      const ras = await L.im.readRasters({ window: [ix0, iy0, ix1, iy1], samples: [0], interleave: true, signal });
      const rw = ix1 - ix0;
      const sx = (wx1 - wx0) / outW, sy = (wy1 - wy0) / outH;
      for (let j = 0; j < outH; j++) {
        const iy = Math.floor(wy0 + (j + 0.5) * sy);
        if (iy < iy0 || iy >= iy1) continue;
        const row = (iy - iy0) * rw;
        for (let i = 0; i < outW; i++) {
          const ix = Math.floor(wx0 + (i + 0.5) * sx);
          if (ix >= ix0 && ix < ix1) out[j * outW + i] = ras[row + ix - ix0];
        }
      }
      return out;
    },

    tileBounds(z, x, y) {
      const s = 2 * R / 2 ** z;
      return [-R + x * s, R - (y + 1) * s, -R + (x + 1) * s, R - y * s];
    },

    /** Crop codes of web-map tile z/x/y (256 x 256), or null where nothing was published. */
    async tileCodes(z, x, y, signal) {
      const key = z + "/" + x + "/" + y;
      if (this._codes.has(key)) return this._codes.get(key);
      const idx = this.index, cz = idx.cell_zoom;
      let p;
      if (z <= idx.overview.zoom) {
        p = this._readBox(idx.overview.file, this.tileBounds(z, x, y), 256, 256, signal);
      } else {
        const d = z - cz, cell = this.cellSet.get((x >> d) + "/" + (y >> d));
        p = cell ? this._readBox(cell.file, this.tileBounds(z, x, y), 256, 256, signal) : Promise.resolve(null);
      }
      const codes = await p;
      const empty = !codes || !codes.some(v => v);
      const val = empty ? null : codes;
      if (this._codes.size > 600) this._codes.delete(this._codes.keys().next().value);
      this._codes.set(key, val);
      return val;
    },

    /** Can the 2021 comparison be shown? Needs the processed footprint in index.json. */
    canCompare() { return !!(this._footprint && this._footprint.length); },
    isWinterCereal(code) { return !!code && this._winter.has(code % LESS); },

    /** ESA WorldCereal 2021 winter cereals for tile z/x/y → Uint8Array (1 = cereal), or null on failure. */
    async wc21Tile(z, x, y, signal) {
      const key = z + "/" + x + "/" + y;
      if (this._wc21.has(key)) return this._wc21.get(key);
      const p = (async () => {
        const url = this.WC21_URL.replace("{z}", z).replace("{x}", x).replace("{y}", y);
        const r = await fetch(url, { signal });
        if (r.status === 204 || r.status === 404) return new Uint8Array(65536);
        if (!r.ok) throw new Error("WorldCereal 2021 tile " + r.status);
        const bmp = await createImageBitmap(await r.blob());
        const c = document.createElement("canvas"); c.width = c.height = 256;
        const g = c.getContext("2d", { willReadFrequently: true });
        g.drawImage(bmp, 0, 0, 256, 256);
        const d = g.getImageData(0, 0, 256, 256).data, m = new Uint8Array(65536);
        for (let i = 0; i < 65536; i++) m[i] = d[i * 4 + 3] > 0 && d[i * 4] > 128 ? 1 : 0;
        return m;
      })().catch(e => { this._wc21.delete(key); return null; });
      if (this._wc21.size > 600) this._wc21.delete(this._wc21.keys().next().value);
      this._wc21.set(key, p);
      return p;
    },

    /** 1 where tile z/x/y lies inside a processed tile. */
    procTile(z, x, y) {
      const key = z + "/" + x + "/" + y;
      if (this._proc.has(key)) return this._proc.get(key);
      const b = this.tileBounds(z, x, y), s = (b[2] - b[0]) / 256, m = new Uint8Array(65536);
      for (const ring of this._footprint) {
        let w = Infinity, e = -Infinity, so = Infinity, n = -Infinity;
        for (const [px, py] of ring) { w = Math.min(w, px); e = Math.max(e, px); so = Math.min(so, py); n = Math.max(n, py); }
        if (e < b[0] || w > b[2] || n < b[1] || so > b[3]) continue;
        const pts = ring.map(([px, py]) => [(px - b[0]) / s, (b[3] - py) / s]);
        for (let j = 0; j < 256; j++) {
          const yy = j + 0.5, xs = [];
          for (let k = 0; k < pts.length - 1; k++) {
            const [ax, ay] = pts[k], [bx, by] = pts[k + 1];
            if ((ay <= yy) !== (by <= yy)) xs.push(ax + (yy - ay) / (by - ay) * (bx - ax));
          }
          xs.sort((a, c) => a - c);
          for (let k = 0; k + 1 < xs.length; k += 2) {
            const i0 = Math.max(0, Math.ceil(xs[k] - 0.5)), i1 = Math.min(256, Math.ceil(xs[k + 1] - 0.5));
            for (let i = i0; i < i1; i++) m[j * 256 + i] = 1;
          }
        }
      }
      if (this._proc.size > 600) this._proc.delete(this._proc.keys().next().value);
      this._proc.set(key, m);
      return m;
    },

    async _pngRGBA(fill) {
      const c = document.createElement("canvas");
      c.width = c.height = 256;
      const img = new ImageData(256, 256);
      fill(img.data);
      c.getContext("2d").putImageData(img, 0, 0);
      const blob = await new Promise(res => c.toBlob(res, "image/png"));
      return blob.arrayBuffer();
    },

    async _png(codes) {
      const c = document.createElement("canvas");
      c.width = c.height = 256;
      if (codes) {
        const img = new ImageData(256, 256), d = img.data, lut = this._lut;
        for (let i = 0; i < codes.length; i++) {
          const v = codes[i] * 4;
          if (!v) continue;
          d[i * 4] = lut[v]; d[i * 4 + 1] = lut[v + 1]; d[i * 4 + 2] = lut[v + 2]; d[i * 4 + 3] = lut[v + 3];
        }
        c.getContext("2d").putImageData(img, 0, 0);
      }
      const blob = await new Promise(res => c.toBlob(res, "image/png"));
      return blob.arrayBuffer();
    },

    /** Register the "wcrop" protocol with MapLibre. Layer tiles: ["wcrop://{z}/{x}/{y}"]. */
    registerProtocol(maplibregl) {
      maplibregl.addProtocol("wcrop", async (params, abort) => {
        const m = params.url.match(/^wcrop:\/\/(\d+)\/(\d+)\/(\d+)/);
        if (!m || !this.index) return { data: await this._png(null) };
        const z = +m[1], x = +m[2], y = +m[3], sig = abort && abort.signal, mode = this.opts.mode;
        if (mode === "y2021" || mode === "diff") {
          const [w21, codes] = await Promise.all([this.wc21Tile(z, x, y, sig),
                                                  mode === "diff" ? this.tileCodes(z, x, y, sig) : null]);
          const C = this.DIFF_COLORS;
          if (mode === "y2021") {
            return { data: await this._pngRGBA(d => { if (w21) for (let i = 0; i < 65536; i++) if (w21[i]) d.set(C.y2021, i * 4); }) };
          }
          if (!w21) return { data: await this._pngRGBA(() => {}) };   // 2021 tile unavailable: show nothing rather than a false "2026 only"
          const proc = this.procTile(z, x, y);
          return { data: await this._pngRGBA(d => {
            for (let i = 0; i < 65536; i++) {
              if (!proc[i]) continue;
              const a = w21 ? w21[i] : 0, b = codes ? this.isWinterCereal(codes[i]) : false;
              if (a && b) d.set(C.both, i * 4); else if (b) d.set(C.only2026, i * 4); else if (a && w21) d.set(C.only2021, i * 4);
            }
          }) };
        }
        const codes = await this.tileCodes(z, x, y, sig);
        if (!codes) {
          this._blank = this._blank || await this._png(null);
          return { data: this._blank.slice(0) };
        }
        return { data: await this._png(codes) };
      });
    },

    lonLatTo3857(lon, lat) {
      const x = lon * R / 180;
      const y = Math.log(Math.tan((90 + Math.max(-85, Math.min(85, lat))) * Math.PI / 360)) * R / Math.PI;
      return [x, y];
    },

    /** Code at a point, read at full resolution (z14). */
    async sample(lon, lat) {
      const [mx, my] = this.lonLatTo3857(lon, lat);
      const z = this.index.max_zoom, s = 2 * R / 2 ** z;
      const tx = Math.floor((mx + R) / s), ty = Math.floor((R - my) / s);
      const codes = await this.tileCodes(z, tx, ty);
      if (!codes) return 0;
      const px = Math.floor(((mx + R) / s - tx) * 256), py = Math.floor(((R - my) / s - ty) * 256);
      return codes[py * 256 + px] || 0;
    },

    /** Pixel size (Web Mercator metres) at overview level L of the cells (0 = full detail, ~10 m on the ground). */
    levelRes(L) { return (this.index.cell_res || 2 * R / (256 * 2 ** this.index.max_zoom)) * 2 ** L; },

    /**
     * Read an area: box in EPSG:3857 [minx, miny, maxx, maxy], at level L (0 = full detail).
     * Returns {data, width, height, x0, y1, res}. Optional mask(i, j) -> bool keeps a pixel.
     */
    async readArea(b, L, onProgress, signal) {
      const res = this.levelRes(L);
      const x0 = Math.floor((b[0] + R) / res) * res - R, y1 = R - Math.floor((R - b[3]) / res) * res;
      const width = Math.ceil((b[2] - x0) / res), height = Math.ceil((y1 - b[1]) / res);
      const data = new Uint8Array(width * height);
      const box = [x0, y1 - height * res, x0 + width * res, y1];
      const cz = this.index.cell_zoom, s = 2 * R / 2 ** cz;
      const cells = this.index.cells.filter(c => {
        const cb = [-R + c.x * s, R - (c.y + 1) * s, -R + (c.x + 1) * s, R - c.y * s];
        return cb[0] < box[2] && cb[2] > box[0] && cb[1] < box[3] && cb[3] > box[1];
      });
      let done = 0;
      for (const c of cells) {
        const cb = [-R + c.x * s, R - (c.y + 1) * s, -R + (c.x + 1) * s, R - c.y * s];
        const ib = [Math.max(cb[0], box[0]), Math.max(cb[1], box[1]), Math.min(cb[2], box[2]), Math.min(cb[3], box[3])];
        const w = Math.round((ib[2] - ib[0]) / res), h = Math.round((ib[3] - ib[1]) / res);
        if (w > 0 && h > 0) {
          const part = await this._readBox(c.file, ib, w, h, signal);
          const ox = Math.round((ib[0] - box[0]) / res), oy = Math.round((box[3] - ib[3]) / res);
          for (let j = 0; j < h; j++) {
            const src = j * w, dst = (oy + j) * width + ox;
            for (let i = 0; i < w; i++) if (part[src + i]) data[dst + i] = part[src + i];
          }
        }
        done++;
        if (onProgress) onProgress(done / cells.length);
      }
      return { data, width, height, x0: box[0], y1: box[3], res };
    },

    /** Zero every pixel outside a (multi)polygon given in lon/lat (GeoJSON geometry). */
    maskToPolygon(area, geom) {
      const rings = [];
      const polys = geom.type === "Polygon" ? [geom.coordinates] : geom.coordinates;
      for (const poly of polys) for (const ring of poly)
        rings.push(ring.map(([lon, lat]) => {
          const [mx, my] = this.lonLatTo3857(lon, lat);
          return [(mx - area.x0) / area.res, (area.y1 - my) / area.res];
        }));
      const { data, width, height } = area;
      const xs = [];
      for (let j = 0; j < height; j++) {
        const y = j + 0.5;
        xs.length = 0;
        for (const r of rings)
          for (let k = 0, n = r.length; k < n - 1; k++) {
            const [ax, ay] = r[k], [bx, by] = r[k + 1];
            if ((ay <= y) !== (by <= y)) xs.push(ax + (y - ay) / (by - ay) * (bx - ax));
          }
        xs.sort((a, b) => a - b);
        let prev = 0;
        for (let k = 0; k + 1 < xs.length; k += 2) {
          const s = Math.max(0, Math.min(width, Math.ceil(xs[k] - 0.5)));
          const e = Math.max(0, Math.min(width, Math.ceil(xs[k + 1] - 0.5)));
          data.fill(0, j * width + prev, j * width + s);
          prev = e;
        }
        data.fill(0, j * width + prev, (j + 1) * width);
      }
      return area;
    },

    /** Hectares per code in an area (pixel area corrected for Web Mercator scale). */
    areaStats(area) {
      const counts = new Float64Array(256);
      const { data, width, height, y1, res } = area;
      for (let j = 0; j < height; j++) {
        const my = y1 - (j + 0.5) * res;
        const lat = Math.atan(Math.sinh(my / R * Math.PI));
        const ha = (res * Math.cos(lat)) ** 2 / 1e4;
        for (let i = 0, o = j * width; i < width; i++) { const v = data[o + i]; if (v) counts[v] += ha; }
      }
      return counts;
    },

    /** Paletted, DEFLATE-compressed GeoTIFF (EPSG:3857) as a Blob. */
    async toGeoTIFF(area, description) {
      const { data, width, height, x0, y1, res } = area;
      const rps = Math.max(1, Math.floor(262144 / width));
      const strips = [];
      const canDeflate = typeof CompressionStream !== "undefined";
      for (let r = 0; r < height; r += rps) {
        const raw = data.subarray(r * width, Math.min(height, r + rps) * width);
        if (canDeflate) {
          const cs = new Blob([raw]).stream().pipeThrough(new CompressionStream("deflate"));
          strips.push(new Uint8Array(await new Response(cs).arrayBuffer()));
        } else strips.push(raw.slice());
      }
      // colour map: TIFF wants 3 x 256 SHORTs (R..., G..., B...)
      const cmap = new Uint16Array(768), cols = this.colors();
      for (let v = 1; v < 2 * LESS && v < 256; v++) {
        const ci = (v % LESS) - 1;
        if (ci < 0 || ci >= cols.length) continue;
        let rgb = [1, 3, 5].map(k => parseInt(cols[ci].slice(k, k + 2), 16));
        if (v > LESS) rgb = rgb.map(c => Math.round(c + (255 - c) * 0.55));
        cmap[v] = rgb[0] * 257; cmap[256 + v] = rgb[1] * 257; cmap[512 + v] = rgb[2] * 257;
      }
      const desc = (description || "Iraq crop types (ESA WorldCereal)") + "\0";
      const nodata = "0\0";
      const geokeys = new Uint16Array([1, 1, 0, 3, 1024, 0, 1, 1, 1025, 0, 1, 1, 3072, 0, 1, 3857]);
      const tags = [
        [256, 4, [width]], [257, 4, [height]], [258, 3, [8]], [259, 3, [canDeflate ? 8 : 1]],
        [262, 3, [3]], [270, 2, desc], [273, 4, null], [277, 3, [1]], [278, 4, [rps]], [279, 4, strips.map(s => s.length)],
        [284, 3, [1]], [320, 3, cmap], [339, 3, [1]],
        [33550, 12, [res, res, 0]], [33922, 12, [0, 0, 0, x0, y1, 0]], [34735, 3, geokeys], [42113, 2, nodata],
      ];
      const size = { 2: 1, 3: 2, 4: 4, 12: 8 };
      const count = t => typeof t[2] === "string" ? t[2].length : (t[0] === 273 ? strips.length : t[2].length);
      const ifdSize = 2 + tags.length * 12 + 4;
      let extra = 8 + ifdSize;
      const extraOff = {};
      for (const t of tags) {
        const n = count(t) * size[t[1]];
        if (n > 4) { extraOff[t[0]] = extra; extra += n + (n & 1); }
      }
      let dataOff = extra;
      const stripOffs = strips.map(s => { const o = dataOff; dataOff += s.length; return o; });
      const buf = new ArrayBuffer(dataOff), dv = new DataView(buf), u8 = new Uint8Array(buf);
      u8[0] = 0x49; u8[1] = 0x49; dv.setUint16(2, 42, true); dv.setUint32(4, 8, true);
      dv.setUint16(8, tags.length, true);
      const writeVals = (off, t, vals) => {
        const ty = t[1];
        if (typeof vals === "string") { for (let i = 0; i < vals.length; i++) u8[off + i] = vals.charCodeAt(i); return; }
        vals.forEach((v, i) => {
          if (ty === 3) dv.setUint16(off + i * 2, v, true);
          else if (ty === 4) dv.setUint32(off + i * 4, v, true);
          else if (ty === 12) dv.setFloat64(off + i * 8, v, true);
        });
      };
      tags.forEach((t, k) => {
        const e = 10 + k * 12, vals = t[0] === 273 ? stripOffs : t[2], n = count(t);
        dv.setUint16(e, t[0], true); dv.setUint16(e + 2, t[1], true); dv.setUint32(e + 4, n, true);
        if (n * size[t[1]] > 4) { dv.setUint32(e + 8, extraOff[t[0]], true); writeVals(extraOff[t[0]], t, vals); }
        else writeVals(e + 8, t, vals);
      });
      dv.setUint32(10 + tags.length * 12, 0, true);
      strips.forEach((s, i) => u8.set(s, stripOffs[i]));
      return new Blob([buf], { type: "image/tiff" });
    },
  };

  global.CropLayer = CropLayer;
})(typeof window !== "undefined" ? window : globalThis);
