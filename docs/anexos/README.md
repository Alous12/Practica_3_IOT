# Anexos

Evidencias referenciadas por el [informe](../INFORME.md). Antes de guardar una captura, tapen el ID de cuenta (12 dígitos), el endpoint de IoT y el Skill ID. Nunca capturen el contenido de los certificados ni de `secrets.h`.

| Archivo | Responsable | Contenido | Sección |
|---|---|---|---|
| [`circuito.png`](circuito.png) | Ruben | Diagrama de conexiones (PIR en GPIO 27, servo en GPIO 25, porta pilas 4 × AA con tierra común) | §2.2 |
| [`circuito-3d.svg`](circuito-3d.svg), [`circuito-3d.png`](circuito-3d.png), [`circuito-3d-oscuro.png`](circuito-3d-oscuro.png) | Ruben | Montaje en la protoboard en vista isométrica (tema claro y oscuro) | §2.2 |
| [`montaje-protoboard.jpg`](montaje-protoboard.jpg) | Ruben | Foto del prototipo armado en la protoboard | §2.2 |
| [`pruebas-hardware.md`](pruebas-hardware.md), [`deteccion.csv`](deteccion.csv) | Ruben | Procedimiento y datos de RNF1 y RNF2 | §4.5 |
| [`pruebas-comunicacion.md`](pruebas-comunicacion.md), [`latencias.csv`](latencias.csv) | Luciana | Procedimiento y datos de RNF3, RNF4 y RNF5 | §4.3, §4.6 |
| `aws-01`, `aws-02`, `aws-03`, `aws-04`, `aws-05`, `aws-07`, `aws-08`, `aws-09`, `aws-10`, `aws-11` (`.png`) | Alejandro | Configuración de AWS | §3.2 |
| `alexa-01` … `alexa-05` (`.png`) | Alejandro | Configuración de la skill y simulador con *Skill I/O* (`alexa-05`) | §3.3 |
| [`pytest-lambda.txt`](pytest-lambda.txt) | Alejandro | Salida de `python -m pytest -v` en `lambda/` | §4.2 |
