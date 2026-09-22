/* Контур Дома — фоновый помощник (service worker).
   Что делает:
   — сайт открывается мгновенно и работает без интернета: страница и картинки лежат в памяти телефона;
   — обновления подхватываются сами: страница берётся из сети, а кэш остаётся запасным вариантом;
   — кабинет (api.php) никогда не кэшируется: заявки и переписка всегда свежие.
   Версию меняем, когда нужно принудительно обновить кэш у всех. */
const V = 'kontur-v2';   /* белые иконки — чтобы у всех обновился кэш */
const SHELL = ['/', '/index.html', '/hero.jpg', '/icon-192.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()).catch(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== V).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const isHTML = req => req.mode === 'navigate' ||
  (req.headers.get('accept') || '').includes('text/html');

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  /* кабинет и всё динамическое — только из сети */
  if (url.pathname.endsWith('/api.php') || url.searchParams.has('a')) return;

  if (isHTML(req)) {
    /* страница: сначала сеть (чтобы правки были видны сразу), кэш — если сети нет */
    e.respondWith(
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(V).then(c => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(req).then(r => r || caches.match('/index.html')))
    );
    return;
  }

  /* картинки, шрифты и прочая статика: сначала кэш — открывается мгновенно */
  e.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res && res.status === 200 && res.type === 'basic') {
        const copy = res.clone();
        caches.open(V).then(c => c.put(req, copy)).catch(() => {});
      }
      return res;
    }))
  );
});

/* страница просит обновиться — применяем новую версию без перезагрузки вкладки */
self.addEventListener('message', e => {
  if (e.data === 'skip-waiting') self.skipWaiting();
});
