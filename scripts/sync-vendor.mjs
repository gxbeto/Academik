import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";

const archivos = [
  ["node_modules/htmx.org/dist/htmx.min.js", "static/vendor/htmx.min.js"],
  ["node_modules/alpinejs/dist/cdn.min.js", "static/vendor/alpine.min.js"],
];

for (const [origenRelativo, destinoRelativo] of archivos) {
  const origen = resolve(origenRelativo);
  const destino = resolve(destinoRelativo);
  mkdirSync(dirname(destino), { recursive: true });
  copyFileSync(origen, destino);
  console.log(`Sincronizado: ${destinoRelativo}`);
}
