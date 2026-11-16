// Service worker da T9.4: guarda o app, os modelos e o runtime para abrir sem rede.
// O build (vite.config.ts) troca as duas constantes abaixo pela lista real de arquivos.
const VERSION = "310b50a9e5bce723";
const FILES = ["./","assets/index-DctKqicf.js","assets/index-DsjAQYRZ.css","assets/poppins-latin-400-normal-BOb3E3N0.woff","assets/poppins-latin-400-normal-cpxAROuN.woff2","assets/poppins-latin-500-normal-C8OXljZJ.woff2","assets/poppins-latin-500-normal-DGXqpDMm.woff","assets/poppins-latin-600-normal-BJdTmd5m.woff","assets/poppins-latin-600-normal-zEkxB9Mr.woff2","assets/poppins-latin-700-normal-BVuQR_eA.woff","assets/poppins-latin-700-normal-Qrb0O0WB.woff2","brand/agroapp.png","brand/leaves.png","models/manifest.json","models/modelo_float16_web.tflite","models/modelo_int8_web.tflite","runtime/inference.js","runtime/litert_wasm_compat_internal.js","runtime/litert_wasm_compat_internal.wasm","runtime/litert_wasm_internal.js","runtime/litert_wasm_internal.wasm","runtime/litert_wasm_jspi_internal.js","runtime/litert_wasm_jspi_internal.wasm","runtime/litert_wasm_threaded_internal.js","runtime/litert_wasm_threaded_internal.wasm"];
const CACHE = `agroapp-${VERSION}`;

self.addEventListener("install", (event) => {
  // addAll é atômico: se um arquivo falhar, nada é considerado pronto para offline.
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(FILES))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith("agroapp-") && key !== CACHE)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  // Navegações abrem sempre o index.html guardado, com qualquer query string.
  const request =
    event.request.mode === "navigate" ? new URL("./", self.registration.scope).href : event.request;
  event.respondWith(
    // ignoreVary: servidores mandam "Vary: Origin" e o script de módulo leva Origin, o addAll não.
    caches.match(request, { cacheName: CACHE, ignoreVary: true }).then((hit) => hit ?? fetch(event.request)),
  );
});
