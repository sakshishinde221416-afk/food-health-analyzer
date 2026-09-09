// Register PWA Service Worker safely without breaking the application if unsupported
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('[PWA] ServiceWorker registered successfully with scope:', registration.scope);
            })
            .catch((error) => {
                console.warn('[PWA] ServiceWorker registration notice:', error);
            });
    });
}
