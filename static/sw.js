self.addEventListener("install", function (e) {
  console.log("Service Worker instalado");
});

self.addEventListener("fetch", function (event) {
  // No cache por enquanto — só intercepta
});
