const CACHE_NAME = 'pocket-aces-cache-v1';
// Lista de arquivos essenciais para o funcionamento offline.
const urlsToCache = [
  '/',
  '/caixa',
  // Adicione aqui os URLs de outros arquivos estáticos se precisar,
  // como o CSS do Bootstrap, mas o cache dinâmico abaixo já ajuda.
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js'
];

// Evento de Instalação: Salva os arquivos essenciais em cache.
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Evento de Fetch: Intercepta os pedidos.
// Se estiver online, pega da rede. Se estiver offline, tenta pegar do cache.
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
      .catch(() => {
        return caches.match(event.request);
      })
  );
});
