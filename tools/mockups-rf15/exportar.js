#!/usr/bin/env node
/*
 * Exporta los mockups de los tres reportes (RF15) a PNG y SVG, 1440 × 1024, tema claro:
 *   docs/anexos/p4/mockup-actividad.{png,svg}
 *   docs/anexos/p4/mockup-puerta-alarma.{png,svg}
 *   docs/anexos/p4/mockup-bloqueos.{png,svg}
 * mockups.html dibuja cada pantalla con los datos ilustrativos de generar-datos.js;
 * el PNG es una captura y el SVG se arma recorriendo la página (cajas, texto y gráficos).
 *
 * Requiere Node 18+ y Playwright con Chromium:  npm i playwright && npx playwright install chromium
 * Uso (desde tools/mockups-rf15):  node exportar.js [carpeta-destino]
 */
const path = require("path");
const fs = require("fs");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const destino = path.resolve(process.argv[2] || path.join(__dirname, "..", "..", "docs", "anexos", "p4"));
const VISTAS = [["actividad", "mockup-actividad"], ["puerta", "mockup-puerta-alarma"], ["bloqueos", "mockup-bloqueos"]];

/* Se ejecuta dentro de la página: convierte lo visible en un SVG autónomo. */
function aSVG() {
  const NS = "http://www.w3.org/2000/svg";
  const W = document.documentElement.scrollWidth, H = document.documentElement.scrollHeight;
  const out = [];
  const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  const visible = (cs) => cs.display !== "none" && cs.visibility !== "hidden" && Number(cs.opacity) > 0;
  const transparente = (c) => !c || c === "transparent" || /rgba\(.*,\s*0\)$/.test(c);
  const canvas = document.createElement("canvas").getContext("2d");
  const bodyBg = getComputedStyle(document.body).backgroundColor;
  out.push(`<rect x="0" y="0" width="${W}" height="${H}" fill="${bodyBg}"/>`);
  const sx = window.scrollX, sy = window.scrollY;

  function caja(el, cs, r) {
    const rad = Math.min(parseFloat(cs.borderTopLeftRadius) || 0, r.width / 2, r.height / 2);
    const x = r.left + sx, y = r.top + sy;
    if (!transparente(cs.backgroundColor)) {
      out.push(`<rect x="${x}" y="${y}" width="${r.width}" height="${r.height}" rx="${rad}" fill="${cs.backgroundColor}"/>`);
    }
    const lados = ["Top", "Right", "Bottom", "Left"].map((l) => [parseFloat(cs["border" + l + "Width"]) || 0, cs["border" + l + "Color"], cs["border" + l + "Style"]]);
    const uniforme = lados.every((l) => l[0] === lados[0][0] && l[1] === lados[0][1] && l[2] !== "none");
    if (uniforme && lados[0][0] > 0) {
      const b = lados[0][0];
      out.push(`<rect x="${x + b / 2}" y="${y + b / 2}" width="${r.width - b}" height="${r.height - b}" rx="${Math.max(0, rad - b / 2)}" fill="none" stroke="${lados[0][1]}" stroke-width="${b}"/>`);
    } else {
      const [t, d, a, i] = lados;
      if (t[0] && t[2] !== "none") out.push(`<rect x="${x}" y="${y}" width="${r.width}" height="${t[0]}" fill="${t[1]}"/>`);
      if (a[0] && a[2] !== "none") out.push(`<rect x="${x}" y="${y + r.height - a[0]}" width="${r.width}" height="${a[0]}" fill="${a[1]}"/>`);
      if (i[0] && i[2] !== "none") out.push(`<rect x="${x}" y="${y}" width="${i[0]}" height="${r.height}" fill="${i[1]}"/>`);
      if (d[0] && d[2] !== "none") out.push(`<rect x="${x + r.width - d[0]}" y="${y}" width="${d[0]}" height="${r.height}" fill="${d[1]}"/>`);
    }
  }
  function texto(nodo, cs) {
    const txt = nodo.textContent;
    if (!txt.trim()) return;
    const font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    canvas.font = font;
    const asc = canvas.measureText("Hg").fontBoundingBoxAscent;
    // palabras con su rectángulo → líneas
    const rango = document.createRange();
    const lineas = [];
    const re = /\S+/g;
    let m;
    while ((m = re.exec(txt))) {
      rango.setStart(nodo, m.index);
      rango.setEnd(nodo, m.index + m[0].length);
      const rects = rango.getClientRects();
      if (!rects.length) continue;
      // Palabra partida entre líneas (overflow-wrap): se reparte carácter por carácter.
      const trozos = rects.length === 1 ? [[m[0], rects[0]]] : [];
      if (rects.length > 1) {
        let actual = null;
        for (let k = 0; k < m[0].length; k++) {
          rango.setStart(nodo, m.index + k); rango.setEnd(nodo, m.index + k + 1);
          const rc = rango.getClientRects()[0];
          if (!rc) continue;
          if (actual && Math.abs(actual[1].top - rc.top) < 2) { actual[0] += m[0][k]; actual[1] = { top: actual[1].top, left: actual[1].left, right: rc.right, height: actual[1].height, width: 1 }; }
          else { actual = [m[0][k], { top: rc.top, left: rc.left, right: rc.right, height: rc.height, width: 1 }]; trozos.push(actual); }
        }
      }
      trozos.forEach(([palabra, r], k) => {
        if (!r.width) return;
        const l = lineas.find((x) => Math.abs(x.top - r.top) < 2);
        if (l) { if (k > 0) l.palabras[l.palabras.length - 1] += palabra; else l.palabras.push(palabra); l.fin = r.right; }
        else lineas.push({ top: r.top, ini: r.left, fin: r.right, alto: r.height, palabras: [palabra] });
      });
    }
    lineas.forEach((l) => {
      const contenido = l.palabras.join(" ");
      const y = l.top + sy + (l.alto - (canvas.measureText("Hg").fontBoundingBoxAscent + canvas.measureText("Hg").fontBoundingBoxDescent)) / 2 + asc;
      out.push(`<text x="${(l.ini + sx).toFixed(1)}" y="${y.toFixed(1)}" font-family="${esc(cs.fontFamily)}" font-size="${cs.fontSize}" font-weight="${cs.fontWeight}"` +
        `${cs.fontStyle !== "normal" ? ` font-style="${cs.fontStyle}"` : ""} fill="${cs.color}" textLength="${(l.fin - l.ini).toFixed(1)}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">${esc(contenido)}</text>`);
    });
  }
  function valorControl(el, cs, r) {
    let v = "";
    if (el.tagName === "SELECT") v = el.options[el.selectedIndex] ? el.options[el.selectedIndex].text : "";
    else if (el.type === "date" && el.value) { const [a, mm, d] = el.value.split("-"); v = `${d}/${mm}/${a}`; }
    else v = el.value || "";
    if (!v) return;
    canvas.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    const y = r.top + sy + r.height / 2 + parseFloat(cs.fontSize) * 0.35;
    out.push(`<text x="${r.left + sx + (parseFloat(cs.paddingLeft) || 0) + 1}" y="${y}" font-family="${esc(cs.fontFamily)}" font-size="${cs.fontSize}" fill="${cs.color}">${esc(v)}</text>`);
    if (el.tagName === "SELECT") {   // flecha
      const ax = r.right + sx - 18, ay = r.top + sy + r.height / 2 - 2;
      out.push(`<path d="M${ax} ${ay}l4 4 4-4" fill="none" stroke="${cs.color}" stroke-width="1.6" stroke-linecap="round"/>`);
    }
  }
  function svgEmbebido(el, r) {
    const copia = el.cloneNode(true);
    const orig = el.querySelectorAll("*"), cop = copia.querySelectorAll("*");
    orig.forEach((o, i) => {
      const cs = getComputedStyle(o);
      const c = cop[i];
      c.removeAttribute("style"); c.removeAttribute("tabindex"); c.removeAttribute("class");
      if (o.getAttribute("fill") === "transparent") { c.remove(); return; }
      c.setAttribute("fill", cs.fill);
      c.setAttribute("stroke", cs.stroke);
      if (cs.stroke !== "none") c.setAttribute("stroke-width", cs.strokeWidth);
      if (o.tagName === "text") { c.setAttribute("font-family", cs.fontFamily); c.setAttribute("font-size", cs.fontSize); c.setAttribute("font-weight", cs.fontWeight); }
      if (cs.opacity !== "1") c.setAttribute("opacity", cs.opacity);
    });
    copia.removeAttribute("class"); copia.removeAttribute("style"); copia.removeAttribute("aria-hidden");
    copia.setAttribute("x", r.left + sx); copia.setAttribute("y", r.top + sy);
    copia.setAttribute("width", r.width); copia.setAttribute("height", r.height);
    if (!copia.getAttribute("viewBox")) copia.setAttribute("viewBox", `0 0 ${r.width} ${r.height}`);
    if (copia.getAttribute("viewBox") === "0 0 24 24") {   // íconos: trazo heredado
      const cs = getComputedStyle(el);
      copia.setAttribute("fill", "none"); copia.setAttribute("stroke", cs.color);
      copia.querySelectorAll("*").forEach((n) => { n.setAttribute("fill", "none"); n.setAttribute("stroke", cs.stroke === "none" ? cs.color : cs.stroke); n.setAttribute("stroke-width", "2"); n.setAttribute("stroke-linecap", "round"); n.setAttribute("stroke-linejoin", "round"); });
    }
    out.push(new XMLSerializer().serializeToString(copia).replace(/ xmlns="http:\/\/www.w3.org\/2000\/svg"/, ""));
  }
  function recorrer(el) {
    const cs = getComputedStyle(el);
    if (!visible(cs)) return;
    const r = el.getBoundingClientRect();
    if (el instanceof SVGElement) { if (r.width && r.height) svgEmbebido(el, r); return; }
    if (r.width && r.height && el !== document.body) caja(el, cs, r);
    if (el.tagName === "INPUT" || el.tagName === "SELECT") { valorControl(el, cs, r); return; }
    if (el.tagName === "DETAILS") { const s = el.querySelector("summary"); if (s) recorrer(s); return; }
    el.childNodes.forEach((n) => {
      if (n.nodeType === 3) texto(n, cs);
      else if (n.nodeType === 1) recorrer(n);
    });
  }
  recorrer(document.body);
  // Coordenadas a 2 decimales (solo en atributos; el texto visible no se toca).
  const cuerpo = out.join("\n").replace(/="([^"]*)"/g, (m, v) => '="' + v.replace(/(\d+\.\d{2})\d+/g, "$1") + '"');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="${NS}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">\n` +
    `<title>${esc(document.title)}</title>\n` + cuerpo + "\n</svg>\n";
}

(async () => {
  fs.mkdirSync(destino, { recursive: true });
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage({ viewport: { width: 1440, height: 1024 }, deviceScaleFactor: 1, locale: "es-BO" });
  const errores = [];
  pagina.on("pageerror", (e) => errores.push(String(e)));
  for (const [vista, nombre] of VISTAS) {
    await pagina.goto(pathToFileURL(path.join(__dirname, "mockups.html")).href + "?p=" + vista);
    await pagina.waitForTimeout(400);
    await pagina.screenshot({ path: path.join(destino, nombre + ".png") });
    fs.writeFileSync(path.join(destino, nombre + ".svg"), await pagina.evaluate(aSVG));
    console.log("✓", nombre);
  }
  await navegador.close();
  if (errores.length) { console.error(errores); process.exit(1); }
})();
