# Evidencias de Luciana para la Práctica 4

Base examinada: `1dfe514afc22e32ccab8a249dff23034ca7ba779`. Fecha de ejecución local: 24 de noviembre de 2026.

## Archivos existentes

- `lu-almacenamiento-guardado.png`: log real compartido durante configuración; guarda lectura de prueba para vigilante-123456.
- `lu-tabla-lectura-prueba.png`: tabla con esa fila de prueba. No demuestra integridad porcentual ni lectura física.
- `lu-almacenamiento-descartado.png`: rechazo real de puerta `rota`. No confundirlo con una captura de alarma `rota`.
- `lu-pruebas-almacenamiento.txt`: 12 pruebas y 18 subcasos correctos, con DynamoDB sustituido por un doble.
- `lu-regresion-logica.txt`: 15 pruebas correctas, sin AWS real.
- `lu-regresion-skill.txt`: 144 pruebas correctas, sin simulador Alexa real.
- `lu-pruebas-firmware.txt`: cuatro ejecutables C++ correctos, sin controlar el ESP32.

Las capturas son las aportadas en la conversación durante la preparación de AWS. Los timestamps del dato de ejemplo no son el tiempo de una medición física. Los registros de prueba se eliminaron después de comprobarlos.

## Comandos de reproducción

Desde la raíz, con Python, boto3, pytest, g++ y ArduinoJson disponibles:

```powershell
python -m pytest lambda-almacenamiento/tests -q
python -m pytest lambda-logica/tests -q
python -m pytest lambda/tests -q
powershell -ExecutionPolicy Bypass -File test/luciana/run.ps1
```

El script C++ utiliza `.pio/libdeps/esp32dev/ArduinoJson/src` de forma predeterminada; puede indicarse otra instalación con `-ArduinoJsonPath`. Los binarios generados están excluidos de Git. La ejecución conservada usó las dependencias ya instaladas, sin desplegar ni invocar servicios AWS.

## Lo que todavía hay que medir o adjuntar

- [x] Revisar los aportes independientes `informeRuben` (`f36d67a`) y `Rama_Ale` (`8162bc3`) sin fusionar sus ramas.
- [x] La persona designada integra los tres aportes en `docs/INFORME_P4.md` después de los commits de cada integrante. Hecho el 24/11/2026; los archivos parciales se retiraron y quedan en el historial de git.
- [ ] Exportación CSV real de `vigilante_historico`, con Thing y ventana UTC de prueba.
- [ ] Conteos de integridad de una ventana de 30 min.
- [ ] Diez muestras de latencia de almacenamiento con relojes comparables.
- [ ] Diez muestras físicas de cierre Edge y diez de primer pitido.
- [ ] Video de reglas con hotspot apagado, apagado de alarma a los 30 s y reconexión.
- [ ] Captura de `alarma#` con valor anterior/origen y de la alarma inválida rechazada.
- [x] Incorporar en la sección 5 la estimación de costo de Alejandro, identificada como estimación y condicionada a sus supuestos.
- [x] Actualizar RF15 con los tres diseños textuales y consultas de Rubén, sin tratarlos como un tablero implementado ni como datos medidos.
- [ ] Resultado físico P4 de estabilidad, voz y nube: las tablas respectivas de Alejandro/Rubén todavía están incompletas en las versiones revisadas.

Los CSV `lu-mediciones-*.csv` son plantillas vacías, no resultados. No completar valores por estimación ni reutilizar las mediciones de P3 como nuevas de P4.

## Entrega independiente e integración posterior

1. Cada integrante conserva y entrega su archivo en su rama. Este aporte y sus anexos quedan únicamente en `lu`; revisar otras ramas no significa fusionarlas.
2. Copiar de `docs/APORTE_LU_INFORME_P4.md` solo los contenidos de 1.2, 1.3, 2.2, 2.4c, 2.5b, 2.6, 2.9c, 3.1b y 5 en los títulos correspondientes.
3. Agregar filas LU-01 a LU-09 a la única tabla del plan de pruebas; conservar las filas de Alejandro y Rubén.
4. Incorporar el párrafo de conclusión, las tres recomendaciones y las filas del índice de anexos. No duplicar secciones completas de otros autores.
5. Los enlaces del aporte están calculados desde `docs/`; al pegarlos en `docs/INFORME_P4.md` siguen funcionando.
6. Sustituir estados pendientes solo cuando existan evidencias verificables. Abrir el Markdown en GitHub y comprobar los diagramas Mermaid y los enlaces antes de hacer la entrega.
