# Mockups de los reportes (RF15)

Fuente de las tres pantallas de [INFORME_P4 §2.11](../../docs/INFORME_P4.md#211-diseño-de-reportes-mockups--rf15). El resultado son imágenes estáticas en [`docs/anexos/p4/`](../../docs/anexos/p4/):

| Pantalla | Pregunta que responde | Archivos |
|---|---|---|
| Actividad del día | ¿Hay más movimiento de lo normal y a qué hora? | `mockup-actividad.png` / `.svg` |
| Puerta y alarma | ¿Quién abrió o cerró y por qué sonó la alarma? | `mockup-puerta-alarma.png` / `.svg` |
| Bloqueos y configuración | ¿El umbral de la Nube está bien elegido? | `mockup-bloqueos.png` / `.svg` |

Los números salen de [`generar-datos.js`](generar-datos.js): 7 días simulados (18 al 24 nov 2026) con semilla fija, que respetan las reglas de §2.6. **Son datos ilustrativos, no mediciones**, y cada pantalla lo indica.

## Regenerar

```bash
cd tools/mockups-rf15
npm i playwright && npx playwright install chromium   # una sola vez
node exportar.js                                     # escribe los PNG y SVG en docs/anexos/p4/
```

`mockups.html` dibuja una pantalla fija de 1440 × 1024 (`mockups.html?p=actividad`, `puerta` o `bloqueos`); `exportar.js` la captura en PNG y la convierte en SVG.
