// Service worker da T9.4: guarda o app, os modelos e o runtime para abrir sem rede.
// O build (vite.config.ts) troca as duas constantes abaixo pela lista real de arquivos.
const VERSION = "__VERSION__";
const FILES = __FILES__;
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
