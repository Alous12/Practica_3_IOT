# Parte de Luciana - Practica 4

## Alcance

- `core/ControlRule.h`: contrato para reglas locales.
- `rules/AutoLockRule.*`: cierra ante un flanco nuevo del PIR en `automatico` o `bloqueo`.
- `PirSensor::motionStarted()`: flanco filtrado del ultimo ciclo; se reinicia en cada `update()`.
- `DoorLock::close()`: cierre idempotente; el arranque sigue ordenando la posicion segura.
- `SmartObject::addRule()`: evalua despues de sensores y antes de comprobar la conexion.
- Publicacion atomica de `reported` y `desired: {puerta: null, origen: null}` tras un cierre Edge.
- Reintento si no hay red o falla la publicacion. Un delta anterior de puerta se ignora
  mientras la limpieza local este pendiente, para evitar una reapertura al reconectar.
- `lambda-almacenamiento/lambda_function.py`: codigo de almacenamiento de la guia,
  con validacion, lecturas, eventos y TTL de 30 dias.
- `aws/almacenamiento-role-policy.json`: plantilla del permiso minimo `PutItem`.
  Reemplazar `<ACCOUNT_ID>` por la cuenta compartida al desplegar; conservar ademas
  los permisos basicos de logs de Lambda. No contiene credenciales.

No se implementan aqui `Setting`, `OperatingMode`, `IntSetting`, los parametros,
las reglas SQL, las definiciones de tablas ni los cambios de Alexa asignados a otros integrantes.

## Integracion simultanea con Alejandro

Base: `42d1b8d` de `main`. La regla ya se registra en `main.cpp`.
La base todavia no tiene el registro de ajustes, por lo que el firmware conserva
modo manual hasta integrar ese aporte. No se inventa otra implementacion del modo.

1. Concentrar la construccion del estado completo en `SmartObject::collectState()`:
   el bucle que llama a `Setting::report()` debe ir AHI, junto al de sensores y actuadores.
   Este mismo estado alimenta las reglas y la publicacion. No basta agregar ajustes
   solamente en `publishState()`: la regla tambien necesita leer `modo` sin red.
2. Conservar `addRule()`, su registro en `main.cpp` y la evaluacion ANTES del retorno
   por desconexion. Procesar los ajustes del delta antes de los actuadores.
3. Unificar el origen en una sola variable: `inicio` al arrancar, `edge` cuando actua
   una regla, y el origen validado `voz`/`nube` cuando se aplica un ajuste o actuador
   del delta. Este aporte ya maneja el origen para actuadores y cierres Edge; Alejandro
   debe reutilizarlo cuando incorpore ajustes. No crear dos fuentes de origen.
4. Sustituir los literales compartidos `modo`, `origen`, `manual`, `automatico`,
   `bloqueo`, `inicio`, `voz`, `nube` y `edge` por las constantes de `config.h`
   al unir ambos aportes; no se edita ese archivo aqui para no duplicar su trabajo.
5. Los adaptadores `AwsShadowPort` y `LocalShadowPort` implementan `publishUpdate()`.
   Cualquier nuevo adaptador debe enviar tambien `desired`, no solo `reported`.
6. La limpieza retira SOLO `puerta` y `origen`; conserva modo y parametros.
   El envio por MQTT es QoS 0: un retorno exitoso significa publicacion aceptada
   por el cliente, no confirmacion `update/accepted` de AWS ni posicion mecanica.
   La prioridad del cierre pendiente dura hasta esa publicacion. Una orden nueva
   que llegue durante ese intervalo tambien queda subordinada al cierre local.

Los dos aportes tocan `SmartObject` y `main.cpp`: unir los cambios por bloques o
con Git; no reemplazar esos archivos completos por la version de otro integrante.

## Pruebas reproducibles (sin hardware)

Con PlatformIO y g++ instalados, desde la raiz:

```powershell
pio run -e esp32dev
powershell -ExecutionPolicy Bypass -File test/luciana/run.ps1
python -m unittest discover -s lambda-almacenamiento/tests -v
```

Las pruebas Python necesitan boto3 (`python -m pip install boto3`). No necesitan
credenciales, red ni una tabla: sustituyen el cliente DynamoDB por un doble.
Las pruebas Edge usan un doble del proveedor de modo, sin implementar los ajustes
de Alejandro. Comprueban manual, automatico, bloqueo, filtro, calentamiento,
flancos, cierre con transporte apagado, no repetir PWM, reintento y delta antiguo.

## Prueba fisica pendiente, despues de unir los ajustes

Validacion local del 21 de noviembre de 2026: compilacion `esp32dev` y
`esp32dev-aws` correctas (esta ultima con plantilla sin credenciales); 3 ejecutables
C++ correctos; 6 pruebas de almacenamiento y las 61 pruebas anteriores de Lambda
correctas. Las compilaciones no cargan el ESP32 ni despliegan la Lambda.

No se ha ejecutado sobre el ESP32 en esta entrega. No confundir las pruebas
automatizadas con una medicion real de latencia o de posicion del servo.

1. Con el PIR ya listo, en manual abrir la puerta. Activar automatico sin generar
   un flanco nuevo en el PIR. Comprobar `reported.modo`.
2. Apagar el hotspot. Esperar una bajada del PIR y provocar una subida: debe cerrar.
   La red no debe ser necesaria para ejecutar la regla.
3. Encender el hotspot. Verificar puerta cerrada y origen `edge` en `reported`,
   sin `puerta` ni `origen` pendientes en `desired`, y sin reapertura del servo.
4. Repetir en bloqueo. En manual una deteccion no debe cerrar la puerta.
5. Confirmar que un nivel alto sostenido no genera nuevas acciones. Grabar video,
   monitor serie y Shadow; medir la respuesta Edge por separado.

El cierre reportado sigue siendo la posicion ordenada, no una medicion fisica.
