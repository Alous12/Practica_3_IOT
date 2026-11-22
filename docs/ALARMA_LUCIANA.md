# Buzzer: aporte de Luciana y cambio AWS 2.3

## Archivos de Luciana

- `src/rules/AlarmRule.h/.cpp`: usa la interfaz existente `ControlRule`.
  En `bloqueo`, un flanco nuevo del PIR enciende el buzzer si estaba apagado.
  En cualquier modo, una alarma encendida por voz, nube o Edge se apaga al
  cumplir `ALARM_MAX_MS`. El vencimiento tiene prioridad sobre otro flanco.
- `src/main.cpp`: registro de `AlarmRule` despues de `AutoLockRule`.
- `lambda-almacenamiento/lambda_function.py`: `alarma` opcional con valores
  `encendida`/`apagada`, y eventos `alarma#...` con estado anterior y origen.
- Pruebas C++ y Python, sin dispositivos ni servicios AWS reales.

Se reutiliza la evaluacion sin conexion y la limpieza pendiente de `SmartObject`.
La regla agrega `alarma: null` y `origen: null` sin borrar la limpieza de puerta.
La proteccion ante un delta antiguo dura mientras la limpieza este pendiente;
un publish exitoso del cliente MQTT no demuestra recepcion `update/accepted`.

## Dependencia de Alejandro

Base revisada: `2366284` de `main`, 22 de noviembre de 2026.
Esa version todavia NO tiene `src/actuators/Buzzer.h/.cpp` ni sus constantes.
Por eso la compilacion de la implementacion y su registro son condicionales a
la presencia de esa cabecera. Sin ella, el firmware previo sigue funcionando
y la nueva regla de alarma NO queda activa.

Al integrar el aporte de Alejandro debe existir:

1. `Buzzer`, con `turnOn()`, `turnOff()`, `isOn()` y `onSinceMs()`.
   `turnOn()` registra la hora de inicio; `loop()` controla el pitido sin bloquear.
   El apagado de 30 s corresponde a `AlarmRule`, que tambien informa origen Edge.
2. Constantes `KEY_ALARM`, `ALARM_ON`, `ALARM_OFF`, `BUZZER_PIN` y `ALARM_MAX_MS`,
   segun la guia. No se definen sustitutos en el firmware de Luciana.
3. En `main.cpp`, antes de construir `AlarmRule`, la instancia de Alejandro:

   ```cpp
   Buzzer buzzer(BUZZER_PIN);
   ```

   Y en `setup()`, antes de `smartObject.begin()`:

   ```cpp
   smartObject.addActuator(&buzzer);
   ```

La guia asigna la implementacion de `Buzzer`, las constantes, su instancia y su
registro a Alejandro. Luciana solo registra la regla que utiliza esa instancia.
No agregar una segunda instancia al resolver la integracion de `main.cpp`.

El doble de `test/luciana/alarm_stubs/` es exclusivamente para pruebas: no se
copia a `src/`, no genera sonido y no valida el circuito ni la frecuencia PWM.

## Pruebas locales

```powershell
pio run -e esp32dev
powershell -ExecutionPolicy Bypass -File test/luciana/run.ps1
python -m unittest discover -s lambda-almacenamiento/tests -v
```

Para usar una copia ya instalada de ArduinoJson, el script permite
`-ArduinoJsonPath <ruta-a-ArduinoJson/src>`.
Las pruebas Python requieren boto3; el cliente DynamoDB se sustituye por un doble.

`test_alarm.cpp` prueba calentamiento/filtro, flancos, modos manual/automatico/
bloqueo, limite exacto de 30 s, activacion por voz/nube, desborde de millis(),
encendido y apagado sin transporte, limpieza combinada con puerta y reintento
ante un delta antiguo. Usa el `OperatingMode` y `SmartObject` reales, con buzzer
y transporte simulados. Falta validar sonido, latencia y operacion en ESP32 real.

## Seccion 2.3: consola AWS

En Ohio, abrir Lambda **vigilante-logica** (la regla de bloqueo de la nube),
pestana Codigo, archivo `lambda_function.py`. Cambiar la constante a:

```python
LOCKDOWN = {
    "modo": "bloqueo",
    "puerta": "cerrada",
    "alarma": "encendida",
    "origen": "nube",
}
```

Pulsar **Deploy**. Los permisos existentes no cambian: se sigue escribiendo
en `state.desired` del Shadow. No modificar `vigilante-skill` por este paso.

Importante: en esta base, `lambda-logica/lambda_function.py` y su README describen
una copia del backend de Alexa. La prueba de contratos exige que esa copia sea
identica a `lambda/lambda_function.py`. Alli NO existe `LOCKDOWN` ni el conteo
historico de la guia. No se ha reemplazado esa carpeta por otra Lambda. Para
versionar el cambio 2.3, primero se necesita exportar el codigo correcto de la
funcion `vigilante-logica` de AWS y acordar su ubicacion con Ruben. El cambio
en la consola no se ha ejecutado desde esta entrega local.

## Actualizacion de almacenamiento y comprobacion

Copiar la Lambda actualizada de `lambda-almacenamiento/lambda_function.py` a
AWS **vigilante-almacenamiento** y pulsar Deploy. No necesita permisos nuevos.
El evento de la guia debe producir `alarma#2026-11-20T10:15:42Z` y
`deteccion#2026-11-20T10:15:42Z`; `alarma: rota` se descarta sin escrituras.
El SQL que dispara por cambios de alarma corresponde a Alejandro (parte 2.2).

En el ESP32 real, despues de integrar y desplegar todo, verificar:

- En manual y automatico, movimiento nuevo no enciende alarma.
- En bloqueo, un movimiento nuevo la enciende y el nivel alto no reinicia tiempo.
- Tras 30 s, se apaga con origen Edge, incluso si la encendio voz o nube.
- Con hotspot apagado, encendido/apagado funcionan. Al reconectar, el Shadow
  muestra el estado actual y no reactiva una orden pendiente antigua.
- Si tambien actua AutoLockRule, se limpian puerta, alarma y origen, sin borrar
  modo, max_detecciones ni ventana_min.

Guardar video, monitor serie, Shadow y filas `alarma#...` como evidencias reales;
las pruebas locales no sustituyen esas mediciones.
