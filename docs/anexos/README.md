# Anexos

Evidencias referenciadas por el [informe](../INFORME.md). Antes de guardar una captura, tapen el ID de cuenta (12 dígitos), el endpoint de IoT y el Skill ID. Nunca capturen el contenido de los certificados ni de `secrets.h`.

| Archivo | Responsable | Contenido | Sección |
|---|---|---|---|
| [`circuito.png`](circuito.png) | Ruben | Diagrama de conexiones (PIR en GPIO 27, servo en GPIO 25, condensador) | §2.2 |
| `circuito-wokwi.png`, [`wokwi/diagram.json`](wokwi/diagram.json) | Ruben | El mismo circuito en Wokwi | §2.2 |
| `montaje-general.jpg`, `montaje-cerrada.jpg`, `montaje-abierta.jpg`, `montaje-protoboard.jpg` | Ruben | Fotos de la maqueta | §2.2 |
| [`pruebas-hardware.md`](pruebas-hardware.md), `deteccion.csv`, `rnf1-*.png`, `rnf2-*` | Ruben | Procedimiento y datos de RNF1 y RNF2 | §4.5 |
| [`pruebas-comunicacion.md`](pruebas-comunicacion.md), `latencias.csv`, `rnf4-*.png`, `rnf5-*.png` | Luciana | Procedimiento y datos de RNF3, RNF4 y RNF5 (incluida `rnf5-monitor.png`, el arranque del §4.3) | §4.3, §4.6 |
| `aws-01` … `aws-13-*.png` | Alejandro | Configuración de AWS | §3.2 |
| `alexa-01` … `alexa-05-*.png` | Alejandro | Configuración de la skill | §3.3 |
| `alexa-sim-01` … `alexa-sim-16-*.png` | Alejandro | Guion del simulador con *Skill I/O* (JSON Input/Output) | §4.4 |
| [`pytest-lambda.txt`](pytest-lambda.txt), `pytest-final.png` | Alejandro | Salida de `python -m pytest -v` en `lambda/` | §4.2 |
| `ci-verde.png` | Alejandro | Workflow de GitHub Actions en verde en `main` | §4.2 |

Videos (RNF3, RNF5 y la demo): súbanlos a YouTube o Drive para no inflar el repositorio y pongan aquí el enlace.
