#!/usr/bin/env node
/*
 * Generador de DATOS ILUSTRATIVOS para los mockups de los reportes (RF15).
 *
 * Simula 7 días (18 al 24 nov 2026, hora de Bolivia, UTC-4) del Thing
 * vigilante-123456 y produce las filas que guardaría vigilante-almacenamiento
 * en la tabla vigilante_historico (lectura, deteccion, puerta, modo, alarma).
 * Es determinista: con la misma semilla produce siempre las mismas filas.
 *
 * NO son mediciones. No copiar estos números a las tablas de resultados.
 *
 * Reglas que respeta (INFORME_P4 §2.6, §2.7, §2.8):
 *  - ≥ 6,5 s entre detecciones del PIR; 60 s de calentamiento tras arrancar.
 *  - Automático o bloqueo: un movimiento cierra la puerta (edge).
 *  - Bloqueo: un movimiento enciende la alarma (edge); se apaga sola a los 30 s.
 *  - Nube: con max_detecciones detecciones en automático dentro de ventana_min
 *    pasa a bloqueo y enciende la alarma (origen nube).
 *  - Voz: abrir solo en manual; pasar a bloqueo solo con la puerta cerrada;
 *    pasar a manual apaga la alarma.
 *  - Latido cada 60 s; ≥ 500 ms entre publicaciones; arranque con origen inicio.
 *
 * Lo usa mockups.html (se carga con <script src>). Con Node muestra un resumen:
 *   node generar-datos.js
 */
/* <generador> */
function generarDatos(opciones) {
  opciones = opciones || {};
  var SEMILLA = opciones.semilla != null ? opciones.semilla : 234;
  var THING = "vigilante-123456";
  var TZ = -4 * 3600;                       // Bolivia, sin horario de verano
  var TTL = 30 * 86400;
  var MAX = 3, VENTANA = 10;                // configuración por defecto

  var s = SEMILLA >>> 0;                    // mulberry32
  function rnd() {
    s = (s + 0x6D2B79F5) >>> 0;
    var t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  function entre(a, b) { return a + (b - a) * rnd(); }
  function local(dia, h, m, seg) {          // dia: 18..24 de nov 2026, hora local
    return Date.UTC(2026, 10, dia, h, m || 0, seg || 0) / 1000 - TZ;
  }

  var INICIO = local(18, 0, 0), AHORA = local(24, 16, 42, 30);

  // ---------- cola de acciones ----------
  var cola = [];
  var desordenada = false;
  function prog(t, tipo, datos) { cola.push({ t: t, tipo: tipo, d: datos || {} }); desordenada = true; }
  function poisson(t0, t1, medio) {         // detecciones candidatas
    var t = t0 + entre(0, medio);
    while (t < t1) { prog(t, "det"); t += 7 + -Math.log(1 - rnd()) * medio; }
  }
  function rafaga(t0, n, gapMin, gapMax) {  // gato, cortina, etc.
    var t = t0;
    for (var i = 0; i < n; i++) { prog(t, "det"); t += entre(gapMin, gapMax); }
  }
  function voz(t, cmd, valor) { prog(t, "voz", { cmd: cmd, valor: valor }); }
  function esporadicas(t0, t1, porHora) {
    for (var h = t0; h < t1; h += 3600) if (rnd() < porHora) prog(h + entre(0, 3500), "det");
  }

  // ---------- plan de la semana ----------
  // 18 (mié), 19 (jue), 20 (vie), 23 (lun), 24 (mar): laborables. 21 (sáb), 22 (dom): en casa.
  [18, 19, 20, 21, 22, 23, 24].forEach(function (dia) {
    var finde = dia === 21 || dia === 22;
    // Madrugada en bloqueo: alguna detección suelta enciende la alarma (edge).
    if (rnd() < 0.3) prog(local(dia, 1 + Math.floor(entre(0, 4)), 0) + entre(0, 3000), "det");
    if (!finde) {
      var desp = local(dia, 6, 35) + entre(0, 600);
      voz(desp, "modo", "manual");
      poisson(desp + 60, local(dia, 8, 5), 380);
      var sale = local(dia, 8, 8) + entre(0, 420);
      voz(sale, "puerta", "abierta");
      voz(sale + entre(40, 90), "modo", "automatico");
      prog(sale + entre(100, 140), "det");                     // al salir: el Edge cierra
      if (dia !== 24) {
        var vuelve = local(dia, 18, 20) + entre(0, 2400);
        esporadicas(sale + 600, vuelve - 900, 0.3);
        voz(vuelve, "modo", "manual");
        voz(vuelve + entre(30, 80), "puerta", "abierta");
        voz(vuelve + entre(150, 260), "puerta", "cerrada");
        poisson(vuelve + 300, local(dia, 22, 30), 560);
      } else {
        esporadicas(sale + 600, AHORA - 1800, 0.3);
      }
    } else {
      var lev = local(dia, 8, 40) + entre(0, 900);
      voz(lev, "modo", "manual");
      poisson(lev + 60, local(dia, 22, 30), 640);
      voz(local(dia, 10, 30) + entre(0, 600), "puerta", "abierta");
      voz(local(dia, 11, 10) + entre(0, 600), "puerta", "cerrada");
      // Por la tarde ponen automático estando en casa: la Nube los bloquea
      // (falsos positivos) y vuelven a manual por voz al cabo de unos minutos.
      voz(local(dia, 13, 5) + entre(0, 900), "modo", "automatico");
    }
    if (dia !== 24) {
      var noche = local(dia, 22, 35) + entre(0, 900);
      voz(noche, "puerta", "cerrada");
      voz(noche + entre(20, 60), "modo", "bloqueo");
    }
  });
  // Ráfagas en automático con la casa vacía (mascota): algunas bloquean, otras no llegan.
  rafaga(local(18, 11, 12, 5), 3, 70, 160);     // bloquea
  rafaga(local(19, 15, 40, 12), 2, 120, 200);   // 2 en 10 min: no llega a 3
  rafaga(local(23, 10, 50, 40), 2, 150, 260);   // 2 en 10 min: no llega a 3
  rafaga(local(24, 15, 18, 30), 4, 60, 140);    // bloquea; la 4.ª suena por el Edge
  voz(local(18, 12, 40, 11), "modo", "automatico");   // desde la app de Alexa, fuera de casa
  voz(local(24, 15, 47, 2), "modo", "automatico");
  // Apertura fuera de horario: madrugada del domingo 22.
  voz(local(22, 2, 9, 14), "modo", "manual");
  voz(local(22, 2, 9, 51), "puerta", "abierta");
  voz(local(22, 2, 14, 3), "puerta", "cerrada");
  voz(local(22, 2, 15, 20), "modo", "bloqueo");
  // Corte de energía el viernes 20 y caída del WiFi el lunes 23.
  prog(local(20, 14, 5, 0), "apagar", { hasta: local(20, 14, 6, 10) });
  prog(local(23, 10, 12, 0), "sin_red", { hasta: local(23, 10, 31, 0) });

  // ---------- estado del objeto ----------
  var arranque = local(15, 9, 0, 0);
  var st = {
    movimiento: false, detecciones: 1287, ultima_deteccion: local(17, 23, 48, 7), sensor_listo: true,
    puerta: "cerrada", alarma: "apagada", modo: "bloqueo",
    max_detecciones: MAX, ventana_min: VENTANA, origen: "voz"
  };
  var filas = [], antes = null, ultimaPub = 0, ultimaDet = 0, alarmaDesde = 0;
  var encendido = true, conRed = true, latido = 0, rssiBase = -51;
  var detAuto = [], bloqueosEnCasa = 0;
  function enCasa(t) {
    var h = new Date((t + TZ) * 1000);
    return (h.getUTCDate() === 21 || h.getUTCDate() === 22) && h.getUTCHours() >= 9 && h.getUTCHours() < 22;
  }                          // epochs de detecciones en automático (lo que consulta PA2)

  function iso(epoch, ms) {
    var d = new Date(Math.round(epoch * 1000));
    var txt = d.toISOString();              // 2026-11-20T10:15:42.318Z
    return ms ? txt : txt.slice(0, 19) + "Z";
  }
  function base(tipo, epoch, ms) {
    var fecha = iso(epoch, ms);
    return { thingName: THING, tipo_ts: tipo + "#" + fecha, tipo: tipo, fecha: fecha,
             epoch: Math.floor(epoch), expira: Math.floor(epoch) + TTL };
  }
  function publicar(t) {
    if (!encendido || !conRed) return;
    if (t - ultimaPub < 0.5) t = ultimaPub + 0.5;
    ultimaPub = t;
    var lec = base("lectura", t, true), k;
    var rep = {
      movimiento: st.movimiento, detecciones: st.detecciones, ultima_deteccion: st.ultima_deteccion,
      sensor_listo: st.sensor_listo, puerta: st.puerta, alarma: st.alarma, modo: st.modo,
      max_detecciones: st.max_detecciones, ventana_min: st.ventana_min, origen: st.origen,
      uptime_s: Math.floor(t - arranque),
      rssi: Math.round(rssiBase + entre(-3.4, 3.4) + (rnd() < 0.03 ? -5 : 0))
    };
    for (k in rep) lec[k] = rep[k];
    filas.push(lec);
    if (antes) {                            // lo que hace la regla vigilante_eventos
      var seg = Math.floor(t);
      ["puerta", "modo", "alarma"].forEach(function (c) {
        if (rep[c] !== antes[c]) {
          var f = base(c, seg, false);
          f[c] = rep[c]; f.anterior = antes[c]; f.origen = rep.origen;
          filas.push(f);
        }
      });
      if (rep.detecciones > antes.detecciones) {
        var d = base("deteccion", seg, false);
        d.detecciones = rep.detecciones; d.puerta = rep.puerta; d.modo = rep.modo;
        filas.push(d);
      }
    }
    antes = rep;
  }
  function encenderAlarma(t, origen) {
    if (st.alarma === "encendida") return false;
    st.alarma = "encendida"; st.origen = origen; alarmaDesde = t;
    prog(t + 30, "alarma_off", { desde: t });
    return true;
  }

  function procesar(a) {
    var t = a.t, d = a.d;
    switch (a.tipo) {
      case "latido":
        publicar(t); break;
      case "det":
        if (!encendido || !conRed || !st.sensor_listo || t - ultimaDet < 6.5) return;
        ultimaDet = t;
        st.detecciones += 1; st.movimiento = true; st.ultima_deteccion = Math.floor(t);
        if ((st.modo === "automatico" || st.modo === "bloqueo") && st.puerta === "abierta") {
          st.puerta = "cerrada"; st.origen = "edge";
        }
        if (st.modo === "bloqueo") encenderAlarma(t, "edge");
        publicar(t);
        prog(t + 2.5, "mov_off");
        if (st.modo === "automatico") {    // regla vigilante_deteccion → vigilante-logica
          var previas = detAuto.filter(function (x) {
            return x >= Math.floor(t) - st.ventana_min * 60 && x <= Math.floor(t) - 1;
          }).length;
          detAuto.push(Math.floor(t));
          if (previas + 1 >= st.max_detecciones) prog(t + entre(1.3, 2.4), "nube");
        }
        break;
      case "mov_off":
        st.movimiento = false; publicar(t); break;
      case "nube":                         // el ESP32 aplica el delta de desired
        if (!encendido) return;
        st.modo = "bloqueo"; st.puerta = "cerrada"; st.origen = "nube";
        st.alarma = "encendida"; alarmaDesde = t;
        prog(t + 30, "alarma_off", { desde: t });
        publicar(t);
        if (enCasa(t)) {                   // fin de semana: alguien en casa lo revierte
          bloqueosEnCasa += 1;
          var vuelta = t + entre(90, 420);
          voz(vuelta, "modo", "manual");
          if (bloqueosEnCasa % 2 === 1) voz(vuelta + entre(1500, 2400), "modo", "automatico");
        }
        break;
      case "alarma_off":
        if (st.alarma !== "encendida" || alarmaDesde !== d.desde) return;
        st.alarma = "apagada"; st.origen = "edge"; publicar(t); break;
      case "voz":
        if (!encendido || !conRed) return;
        if (d.cmd === "modo") {
          if (st.modo === d.valor) return;
          if (d.valor === "bloqueo" && st.puerta !== "cerrada") return;
          st.modo = d.valor; st.origen = "voz";
          if (d.valor === "manual" && st.alarma === "encendida") st.alarma = "apagada";
        } else if (d.cmd === "puerta") {
          if (st.puerta === d.valor) return;
          if (d.valor === "abierta" && st.modo !== "manual") return;   // la skill lo rechaza
          st.puerta = d.valor; st.origen = "voz";
        }
        publicar(t); break;
      case "apagar":
        encendido = false;
        prog(d.hasta, "arrancar"); break;
      case "arrancar":
        encendido = true; arranque = t; latido = t;
        st.modo = "manual"; st.alarma = "apagada"; st.puerta = "cerrada"; st.origen = "inicio";
        st.detecciones = 0; st.movimiento = false; st.sensor_listo = false;
        publicar(t);
        prog(t + 60, "listo"); break;
      case "listo":
        st.sensor_listo = true; publicar(t); break;
      case "sin_red":
        conRed = false; prog(d.hasta, "con_red"); break;
      case "con_red":
        conRed = true; rssiBase = -53; publicar(t); break;
    }
  }

  // Latidos cada 60 s (se programan sobre la marcha) y bucle de simulación.
  var proxLatido = INICIO + 23.4;
  cola.sort(function (a, b) { return a.t - b.t; });
  publicar(INICIO);
  while (true) {
    if (desordenada) { cola.sort(function (a, b) { return a.t - b.t; }); desordenada = false; }
    var sig = cola.length ? cola[0].t : Infinity;
    if (proxLatido <= sig) {
      if (proxLatido > AHORA) break;
      procesar({ t: proxLatido, tipo: "latido", d: {} });
      proxLatido += 60;
      continue;
    }
    var acc = cola.shift();
    if (acc.t > AHORA) break;
    if (acc.t < INICIO) continue;
    procesar(acc);
  }
  // La primera fila es solo el estado inicial (00:00 del día 18): se conserva.
  return { filas: filas, ahora: AHORA, thing: THING, zona: "UTC-4", semilla: SEMILLA };
}
/* </generador> */

// ---------- CLI (Node) ----------
if (typeof module !== "undefined" && require.main === module) {
  var datos = generarDatos();
  var cuenta = {};
  datos.filas.forEach(function (f) {
    var k = f.tipo + (f.origen && f.tipo !== "lectura" && f.tipo !== "deteccion" ? ":" + f.origen : "");
    cuenta[k] = (cuenta[k] || 0) + 1;
  });
  console.log("Filas:", datos.filas.length, "(semilla " + datos.semilla + ")");
  console.log(cuenta);
}
if (typeof module !== "undefined") module.exports = { generarDatos: generarDatos };
