# Referencias de los aportes del equipo

Revisión del 24 de noviembre de 2026 para completar únicamente el aporte de Luciana.

> **Estado:** la integración ya se hizo en [`docs/INFORME_P4.md`](../../INFORME_P4.md). Los archivos parciales que se citan abajo se retiraron del repositorio y se conservan en el historial de git (commits indicados en la tabla).

| Autor | Rama consultada | Commit | Archivo |
|---|---|---|---|
| Rubén | informeRuben | f36d67a7012f06875c7ddca8b8f98c1fc6c0382a | docs/informeRuben.md |
| Alejandro | Rama_Ale | 8162bc3a0811bcc6d2a8f9b5c46c3bad9df2b306 | docs/informe_ale.md |

No se fusionó ninguna rama ni se modificaron archivos de otros integrantes. Se actualizaron referencias, RF15 y la consolidación de resultados dentro de `docs/APORTE_LU_INFORME_P4.md`.

## Qué quedó incorporado a la consolidación

- Los tres mockups textuales y sus consultas ya están diseñados por Rubén. Los PNG ru-mockup-1/2/3 se mencionan como `[COMPLETAR]` y no están en su árbol revisado.
- Rubén documenta 144 pruebas de skill y 15 de lógica; coinciden con la ejecución local previa de Lu, por lo que no se duplican en el total. Lu añade 12 de almacenamiento: total 171 pruebas Python, más los subcasos y cuatro ejecutables C++ indicados por separado.
- Alejandro documenta compilaciones de buzzer activo/pasivo y una estimación de aproximadamente USD0,19 mensuales. Se atribuyen al autor; no se confunden con una prueba física o con facturación medida.
- P-A1 de estabilidad de Alejandro está todavía por medir. El ensayo de cinco tiempos de nube de Rubén conserva `[COMPLETAR]`. No hay valores que puedan trasladarse como mediciones en esas filas.

## Pendientes para quien una los informes

1. Mantener los resultados desconocidos como pendientes hasta adjuntar mediciones. Ni las cifras de los mockups ni las de P3 completan tiempos o integridad de P4.
2. Revisar enlaces de evidencias: Rubén usa `anexos/anexosP4/`; Alejandro y Lu usan `anexos/p4/`. Unificar o conservar rutas válidas al reunir archivos. Varias capturas citadas por los otros autores todavía no están en sus ramas.
3. Conservar la distinción entre estado ordenado y estado físicamente medido: `reported.puerta` no contiene realimentación de posición y `alarma=encendida` no significa sonido continuo durante la fase intermitente.
4. Evitar afirmar que nunca se repite un tipo de evento dentro de un segundo. El PIR puede tener un período mayor, pero puerta o alarma pueden cambiar por voz; la clave tipo+fecha en segundos no garantiza unicidad universal. El aporte de Lu conserva este límite en 2.9c.
5. Validar el cálculo económico con fecha y condiciones reales de la cuenta. La estimación de Alejandro no demuestra automáticamente aplicabilidad de todos los beneficios gratuitos ni sustituye una factura.
6. El cambio a bloqueo por voz cierra puerta, mientras el bloqueo disparado por la nube también enciende alarma. La secuencia y los resultados deben conservar esa diferencia.

Estas observaciones se entregan al integrador; no son cambios de implementación ni correcciones realizadas a las secciones de otros autores.
