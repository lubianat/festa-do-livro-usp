const V='festa-2026-v7';
const CORE=['./','index.html','data.json','words.json','words.b64.txt','docs.b64.txt','manifest.webmanifest','icon-192.png','icon-512.png',
'28flusp-site-espaco-verde.webp','28flusp-site-espaco-rosa.webp','28flusp-site-espacos-marrom.webp'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('festa-2026-')&&k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET')return;
  if(u.origin===location.origin){ // app files: cache first, refresh in background
    e.respondWith(caches.open(V).then(async c=>{const hit=await c.match(e.request,{ignoreSearch:true});
      const net=fetch(e.request).then(r=>{if(r.ok)c.put(e.request,r.clone());return r}).catch(()=>hit);
      return hit||net}));return}
  if(/covers\.openlibrary\.org|archive\.org|books\.google|googleusercontent/.test(u.hostname)){ // covers: keep what was seen
    e.respondWith(caches.open('festa-covers').then(async c=>{const hit=await c.match(e.request);if(hit)return hit;
      try{const r=await fetch(e.request);if(r.ok||r.type==='opaque')c.put(e.request,r.clone());return r}catch(err){return Response.error()}}))}
});
