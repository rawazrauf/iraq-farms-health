# Field-check scripts (IFH debug mode, built-in browser)

Saved 2026-10-31 from the built-in browser's localStorage on https://iraqfarmshealth.com, where they still live. If localStorage was cleared, set them again with `localStorage.pk = \`…\`` and so on, using the code below.

They depend on globals in IFH `index.html` (build 2026.10.30-k): `map`, `fieldsInView`, `onFieldTap`, `lastField`, `geomBbox`, `pointInGeom`, `geomAreaMeters`, `ndviForWindow`, `mapIdle`, `__fieldBusyUntil`, and the `#dbg` log panel.

## How one field is read
1. Mark the old page: `window.__oldPage=1; 'm'` (javascript_exec). Without this, a script can run on the previous page before the navigation lands.
2. Navigate to `https://iraqfarmshealth.com/?lat=<lat>&lon=<lon>&z=16&debug=1`. The link opens the field under the point if it can.
3. Wait about 1 s, then run `await eval(localStorage.pk)` (random sample) or `await eval(localStorage.ps)` (late-field screen).
4. In a **separate** call run `await eval(localStorage.pw)`. It returns `{n, ha, c, conf, log, months}`: 24 monthly NDVI values, the 2021 ESA line, the 2026 line, the confident-cereal percentage and the verdict. If the 2021 line hasn't arrived yet, poll again with `pl`.
5. Score the field as Yes / Partly / No / Not scored and add a row to claude/field-checks.md.

Random points are drawn in Python from `crops/2026/iraq_crops.vrt` (rasterio). Only tiles listed as `processed` in `index.json` are used, and codes 0 and 255 are skipped. Larger fields are therefore more likely to be picked, and pixels mapped as 0 are never sampled. A research-grade sample must fix both.

## pk: pick a field
If the link opened a field, it returns that one. Otherwise, or if the link's polygon was refused (over 500 ha), it taps a random 1–500 ha field in view.

```js
(async()=>{ if(window.__oldPage) return {error:'old page'}; const sleep=ms=>new Promise(r=>setTimeout(r,ms)); const until=async(fn,max,st=200)=>{const e=Date.now()+max;while(Date.now()<e){try{const v=fn();if(v)return v;}catch{}await sleep(st);}return null;}; const dbg=()=>(document.querySelector('#dbg')||{}).innerText||''; const t0=Date.now();
await until(()=>typeof map!=='undefined'&&fieldsInView().length>0,15000); await sleep(300);
const started = await until(()=>/tap FTW|whole field/.test(dbg()) || (typeof __fieldBusyUntil!=='undefined' && __fieldBusyUntil>Date.now()),6000);
let refusedLink=false; if(started){ await until(()=>/tap FTW|refused/.test(dbg()),24000); if(/tap FTW/.test(dbg())) return {how:'link opened the field under the point', secs:(Date.now()-t0)/1000}; refusedLink=true; }
const R=6371008.8,rad=Math.PI/180; const ringA=r=>{let a=0;for(let i=0;i<r.length-1;i++)a+=(r[i+1][0]-r[i][0])*rad*(2+Math.sin(r[i][1]*rad)+Math.sin(r[i+1][1]*rad));return Math.abs(a*R*R/2);}; const ha=g=>(g.type==='Polygon'?[g.coordinates]:g.coordinates).reduce((s,p)=>s+ringA(p[0]),0)/1e4;
const inv=fieldsInView(); const ok=inv.filter(f=>ha(f.geometry)>=1&&ha(f.geometry)<=500); if(!ok.length) return {how:'none', n:inv.length, secs:(Date.now()-t0)/1000};
const f=ok[Math.floor(Math.random()*ok.length)], b=geomBbox(f.geometry); let pt=null; for(let i=0;i<3000&&!pt;i++){const x=b[0]+Math.random()*(b[2]-b[0]),y=b[1]+Math.random()*(b[3]-b[1]); if(pointInGeom(x,y,f.geometry)){const p=map.project([x,y]); if(p.x>5&&p.y>5&&p.x<innerWidth-5&&p.y<innerHeight-5) pt={lng:x,lat:y};}}
if(!pt) return {how:'none (no point on screen)', secs:(Date.now()-t0)/1000};
const p=map.project([pt.lng,pt.lat]); const nr=(dbg().match(/refused/g)||[]).length; onFieldTap({features:[map.queryRenderedFeatures([p.x,p.y],{layers:['fields-fill']})[0]],lngLat:pt}); await until(()=>/tap FTW/.test(dbg())||(dbg().match(/refused/g)||[]).length>nr,24000);
return {refusedLink, how:`random field 1-500 ha in view (${ok.length} of ${inv.length})`, secs:(Date.now()-t0)/1000}; })()
```

## pl: poll the result
```js
(async()=>{const s=ms=>new Promise(r=>setTimeout(r,ms)); const t0=Date.now(); const A=()=>{const L=document.querySelector('#dbg').innerText.split('\n'); let i=L.length-1; while(i>=0&&!/tap FTW/.test(L[i])) i--; return i<0?[]:L.slice(i);}; const M=()=>{const m={}; A().forEach(l=>{const x=l.match(/month (\d{4}-\d\d) → ([\d.-]+)/); if(x) m[x[1]]=x[2];}); return m;};
if(!A().length) return {error:'no tap', wf: document.querySelector('#dbg').innerText.split('\n').filter(l=>/whole field|refused/.test(l)).join(' / ')};
while(Date.now()-t0<28000 && !(Object.keys(M()).length>=24 && A().some(l=>/verdict/.test(l)) || (Date.now()-t0>14000 && Object.keys(M()).length>=24 && A().some(l=>/2026 part/.test(l))))) await s(300);
const m=M(); let ha=null, c=null; try{ ha=(geomAreaMeters(lastField.geometry)/1e4).toFixed(2); const b=geomBbox(lastField.geometry); c=((b[1]+b[3])/2).toFixed(5)+','+((b[0]+b[2])/2).toFixed(5);}catch{}
const cl=(A().find(l=>/2026 part/.test(l))||'').match(/2026 confident cereal.*$/); return {n:Object.keys(m).length, ha, c, conf: cl?cl[0]:null, log:A().filter(l=>/tap FTW|refused|2021 ESA|2026 part|verdict|bad scene/.test(l)).map(l=>l.trim().replace(/crop check FTW-\w+ 2026 part: 2026 ours \(\d+ px ≈ ([\d.]+) ha read\)/,'2026: ').replace(/ \| 2026 confident.*$/,'').slice(0,300)).join('\n'), months:Object.keys(m).sort().map(k=>k.slice(2)+' '+m[k]).join(' | ')};})()
```

## pw: wait for a tap, then poll
```js
(async()=>{const e=Date.now()+20000; while(Date.now()<e && !/tap FTW|refused/.test(document.querySelector('#dbg').innerText)) await new Promise(r=>setTimeout(r,300)); return await eval(localStorage.pl);})()
```

## ps: late-field screen
Zooms to 15 and shuffles the 1–150 ha fields in view. It taps the first field with April NDVI ≥ 0.35, May ≥ 0.30 and July ≤ 0.20, giving up after 30 s.

```js
(async()=>{ if(window.__oldPage) return {error:'old page'}; const sleep=ms=>new Promise(r=>setTimeout(r,ms)); const until=async(fn,max,st=200)=>{const e=Date.now()+max;while(Date.now()<e){try{const v=fn();if(v)return v;}catch{}await sleep(st);}return null;}; const dbg=()=>(document.querySelector('#dbg')||{}).innerText||''; const t0=Date.now();
await until(()=>typeof map!=='undefined'&&fieldsInView().length>0,15000); await sleep(1500); map.jumpTo({zoom:15}); await mapIdle(4000); await sleep(500);
const R=6371008.8,rad=Math.PI/180; const ringA=r=>{let a=0;for(let i=0;i<r.length-1;i++)a+=(r[i+1][0]-r[i][0])*rad*(2+Math.sin(r[i][1]*rad)+Math.sin(r[i+1][1]*rad));return Math.abs(a*R*R/2);}; const ha=g=>(g.type==='Polygon'?[g.coordinates]:g.coordinates).reduce((s,p)=>s+ringA(p[0]),0)/1e4;
const inv=fieldsInView(); const c=inv.filter(f=>{const h=ha(f.geometry); return h>=1&&h<=150;}); for(let i=c.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[c[i],c[j]]=[c[j],c[i]];}
const screened=[]; let pick=null;
for(const f of c){ if(Date.now()-t0>30000) break; let a=null,m=null; try{ a=(await ndviForWindow(f.geometry,'2026-04-01','2026-04-30')).value; if(a!=null&&a>=0.35){ m=(await ndviForWindow(f.geometry,'2026-05-01','2026-05-31')).value; } }catch{}
  screened.push([+ha(f.geometry).toFixed(1), a==null?null:+a.toFixed(2), m==null?null:+m.toFixed(2)]);
  if(a!=null&&a>=0.35&&m!=null&&m>=0.30){ let j=null; try{ j=(await ndviForWindow(f.geometry,'2026-07-01','2026-07-31')).value; }catch{} screened[screened.length-1].push(j==null?null:+j.toFixed(2)); if(j!=null&&j<=0.2){ pick=f; break; } } }
if(!pick) return {picked:false, n:c.length, screened, secs:(Date.now()-t0)/1000};
const b=geomBbox(pick.geometry); let pt=null; for(let i=0;i<3000&&!pt;i++){const x=b[0]+Math.random()*(b[2]-b[0]),y=b[1]+Math.random()*(b[3]-b[1]); if(pointInGeom(x,y,pick.geometry)) pt={lng:x,lat:y};}
const L=dbg().split('\n').length; const p=map.project([pt.lng,pt.lat]); onFieldTap({features:[map.queryRenderedFeatures([p.x,p.y],{layers:['fields-fill']})[0]],lngLat:pt});
await until(()=>dbg().split('\n').slice(L-1).some(l=>/tap FTW|refused/.test(l)),12000);
return {picked:true, n:c.length, screened, secs:(Date.now()-t0)/1000}; })()
```

## Gotchas
- Run the poll in its own call. Polling inside the same batch as the navigation often hits the time limit.
- A refused polygon (over 500 ha, `FIELD_MAX_HA`) logs "field refused". These are common in the Rabia belt.
- Evergreen fields (orchards, reeds) can pass the April/May test. The July ≤ 0.20 check excludes them.
- Near the Mosul Dam lake, `ndviForWindow` can return null or throw. Skip those points.
- "2026 ours: not processed yet" means the tile hasn't been run yet. Skip the field.
