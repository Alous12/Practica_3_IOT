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
- [x] Exportación real de 186 lecturas de `vigilante-123456`; 132 corresponden a la sesión. Archivos y procedencia en [lu-sesion-20261124/README.md](lu-sesion-20261124/README.md).
- [x] LU-04: 132/132 publicaciones emparejadas, 100 % observado en 1800 s. Se comparan 12 atributos y multiplicidad, sin reutilizar claves.
- [x] LU-05 parcial: 17 intervalos regla IoT → log posterior a PutItem, media 160,824 ms y máximo 378 ms.
- [ ] LU-05 completo: diez emisiones UTC acreditadas → log posterior a PutItem. La recepción serie del PC no es un inicio de emisión sincronizado.
- [ ] Diez muestras físicas de cierre Edge y diez de primer pitido.
- [ ] Video de reglas con hotspot apagado, apagado de alarma a los 30 s y reconexión.
- [ ] Captura de `alarma#` con valor anterior/origen y de la alarma inválida rechazada.
- [x] Incorporar en la sección 5 la estimación de costo de Alejandro, identificada como estimación y condicionada a sus supuestos.
- [x] Actualizar RF15 con los tres diseños textuales y consultas de Rubén, sin tratarlos como un tablero implementado ni como datos medidos.
- [x] Seguimiento serie de 30 min: 0 indicios de reinicio y 0 retrocesos de uptime. LU-07: 7 apagados Edge lógicos de 29,996–29,998 s. G-01: 19 latidos de 59,995–60,001 s.
- [x] Actualizar el informe de la rama lu con resultados M y escenarios E separados; conservar supuestos y capturas/verificación faltantes en [lu-estimaciones-y-verificacion.md](lu-estimaciones-y-verificacion.md).
- [ ] Video y guion físico completo de P-A1; tiempos y capturas de voz y Nube, precisión PIR y reconexión siguen sin ensayo conservado.

Los CSV `lu-mediciones-*.csv` siguen siendo plantillas para ensayos sin completar; los resultados M están en `lu-sesion-20261124/`. A petición de la usuaria, el informe incluye escenarios E explícitamente etiquetados. No se introducen como muestras experimentales, no acreditan RNF y no se reutiliza P3 como resultado medido de P4.

## Actualización de la rama lu

El informe ya fue unificado por la persona designada. Esta actualización edita `docs/INFORME_P4.md` en la rama `lu` y añade evidencias de Lu, sin fusionar otras ramas, hacer commits ni publicar cambios. El equipo puede revisar el diff y decidir cómo integrarlo.

Las capturas reales de lecturas/alarma se adjuntaron. La activación de TTL, reglas desplegadas, LOCKDOWN, ZIP de skill, modelo compilado, binario instalado y arquitectura de Lambda siguen sujetos a verificación; no se pueden acreditar con valores estimados.
