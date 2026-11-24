"""Reproduce las mediciones de Lu con Python 3, sin AWS ni dependencias externas.

Desde la raiz: python tools/analizar_mediciones_lu.py
No genera mediciones fisicas ni convierte estimaciones en resultados.
"""
import collections
import csv
import hashlib
import json
import re
import statistics
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'docs/anexos/p4/lu-sesion-20261124'
FIELDS = ('movimiento', 'detecciones', 'ultima_deteccion', 'sensor_listo',
          'puerta', 'alarma', 'modo', 'max_detecciones', 'ventana_min',
          'origen', 'uptime_s', 'rssi')
NUMBERS = {'detecciones', 'ultima_deteccion', 'max_detecciones', 'ventana_min', 'uptime_s', 'rssi'}


def dt(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def load_csv(name):
    with (BASE / name).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def save_csv(name, rows, fields=None):
    with (BASE / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_json(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fingerprint(row):
    result = []
    for key in FIELDS:
        value = row[key]
        if key in NUMBERS:
            value = int(str(value).lstrip("'"))
        elif key in ('movimiento', 'sensor_listo'):
            if isinstance(value, str):
                if value.lower() not in ('true', 'false'):
                    raise ValueError(f'Booleano invalido: {key}={value}')
                value = value.lower() == 'true'
        result.append(value)
    return tuple(result)


def main():
    capture = json.loads((BASE / 'lu-resumen-serial.json').read_text(encoding='utf-8-sig'))
    serial_text = (BASE / 'lu-monitor-serie.txt').read_text(encoding='utf-8-sig')
    serial = []
    reports = []
    for line in serial_text.splitlines():
        if ' | ' not in line:
            continue
        utc, message = line.split(' | ', 1)
        if not capture['inicio_utc_pc'] <= utc < capture['fin_utc_pc_exclusivo']:
            continue
        serial.append((utc, message))
        if '[Shadow] reported -> ' in message:
            payload = json.loads(message.split('[Shadow] reported -> ', 1)[1])
            reports.append((utc, payload['state']['reported'], payload['state'].get('desired', {})))

    header, exported = load_csv('lu-historico-lecturas-exportado.csv')
    keys = [(r['thingName'], r['tipo_ts']) for r in exported]
    assert len(keys) == len(set(keys)), 'Claves DynamoDB duplicadas'
    assert all(r['thingName'] == 'vigilante-123456' and r['tipo'] == 'lectura' for r in exported)
    buckets = collections.defaultdict(list)
    for row in sorted(exported, key=lambda r: r['fecha']):
        buckets[fingerprint(row)].append(row)
    matched, missing, cross, publications = [], [], [], []
    for number, (utc, state, desired) in enumerate(reports, 1):
        publications.append(dict(n=number, recepcion_utc_pc=utc, **state))
        candidates = buckets[fingerprint(state)]
        if not candidates:
            missing.append(number)
            continue
        row = candidates.pop(0)
        difference = round((dt(row['fecha']) - dt(utc)).total_seconds() * 1000, 3)
        assert abs(difference) < 5000, 'Revisar la cohorte y los relojes'
        matched.append(row)
        cross.append(dict(n=number, recepcion_serial_utc_pc=utc,
                          tipo_ts_dynamodb=row['tipo_ts'], fecha_regla_utc=row['fecha'],
                          uptime_s=state['uptime_s'], coinciden_12_atributos=True,
                          diferencia_referencias_ms_no_latencia=difference))
    assert len(set(r['tipo_ts'] for r in matched)) == len(matched)
    assert len(reports) == capture['publicaciones_reported_con_publish_ok']
    backwards = [(a[0], b[0]) for a, b in zip(reports, reports[1:]) if b[1]['uptime_s'] < a[1]['uptime_s']]
    resets = [(t, m) for t, m in serial if re.search(r'Brownout|rst:|\[Vigilante\] Reinicio|Guru Meditation', m, re.I)]
    failed = [(t, m) for t, m in serial if '[Shadow] reported FALL' in m]
    save_csv('lu-publicaciones.csv', publications)
    save_csv('lu-historico-lecturas-sesion.csv', matched, header)
    save_csv('lu-cruce-publicaciones-historico.csv', cross)
    integrity = dict(thingName='vigilante-123456', inicio_utc_pc=capture['inicio_utc_pc'],
                     fin_utc_pc_exclusivo=capture['fin_utc_pc_exclusivo'],
                     duracion_s=(dt(capture['fin_utc_pc_exclusivo'])-dt(capture['inicio_utc_pc'])).total_seconds(),
                     filas_exportadas=len(exported), publicaciones_validas_con_publish_ok=len(reports),
                     filas_guardadas_coincidentes_uno_a_uno=len(matched), publicaciones_sin_fila=missing,
                     otras_filas_fuera_cohorte=len(exported)-len(matched),
                     integridad_observada_porcentaje=100*len(matched)/len(reports),
                     atributos_comparados=list(FIELDS),
                     reinicios_observados=resets, disminuciones_uptime=backwards,
                     fallos_publish_observados=failed,
                     uptime_primero_s=reports[0][1]['uptime_s'], uptime_ultimo_s=reports[-1][1]['uptime_s'],
                     estado_inicial=reports[0][1], estado_final=reports[-1][1],
                     alcance='Integridad de esta cohorte con red y seguimiento serie; no prueba efectos fisicos, ausencia de bloqueos breves ni funcionamiento offline.')
    save_json('lu-resultado-integridad.json', integrity)

    raw = (BASE / 'lu-cloudwatch-texto-original.txt').read_text(encoding='utf-8-sig')
    pattern = re.compile(r'\[INFO\]\s+(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+([\da-f-]{36})\s*(\{[^{}]*\})')
    events, occurrences = {}, 0
    for match in pattern.finditer(raw):
        stamp, request, payload = match.groups()
        event = json.loads(payload)
        if event.get('evento') == 'guardado':
            occurrences += 1
            events[(stamp, request, event['thing'], event['tipo_ts'])] = event
    cohort = {(r['thingName'], r['tipo_ts']) for r in matched}
    aws_rows = []
    for (stamp, request, thing, key) in sorted(events):
        if (thing, key) in cohort:
            origin = key.split('#', 1)[1]
            aws_rows.append(dict(thingName=thing, tipo_ts=key, fecha_regla_utc=origin,
                                 log_post_putitem_utc=stamp, request_id=request,
                                 tramo_regla_a_log_ms=round((dt(stamp)-dt(origin)).total_seconds()*1000, 3)))
    assert len({r['tipo_ts'] for r in aws_rows}) == len(aws_rows)
    values = [r['tramo_regla_a_log_ms'] for r in aws_rows]
    assert all(v >= 0 for v in values)
    save_csv('lu-cloudwatch-tramo-almacenamiento.csv', aws_rows)
    aws_summary = dict(muestras=len(values), media_ms=round(statistics.mean(values), 3),
                       mediana_ms=statistics.median(values), minimo_ms=min(values), maximo_ms=max(values),
                       copias_duplicadas_eliminadas=occurrences-len(events),
                       alcance='Regla IoT a log guardado posterior a PutItem. No es tiempo puro de DynamoDB ni latencia ESP32 a almacenamiento.',
                       lu05_extremo_a_extremo_completo=False)
    save_json('lu-cloudwatch-resultado.json', aws_summary)

    # Encendido/apagado logico, emparejado sin inferir sonido fisico.
    alarm_rows, opened = [], None
    for utc, message in serial:
        if message == '[Alarma] Encendida':
            opened = utc
        elif message == '[Alarma] Apagada' and opened:
            before = next((r for r in reports if r[0] >= opened), None)
            after = next((r for r in reports if r[0] >= utc), None)
            origin_on = before[1]['origen'] if before else 'sin_reporte'
            origin_off = after[1]['origen'] if after else 'sin_reporte'
            cleared = after and after[1]['alarma'] == 'apagada' and 'alarma' in after[2] and after[2]['alarma'] is None
            alarm_rows.append(dict(encendida_utc_pc=opened, apagada_utc_pc=utc,
                                   duracion_logica_s=round((dt(utc)-dt(opened)).total_seconds(), 3),
                                   origen_encendido=origin_on, origen_apagado=origin_off,
                                   limpieza_desired_alarma=bool(cleared),
                                   apagado_edge=bool(cleared and origin_off == 'edge')))
            opened = None
    save_csv('lu-alarmas-serie.csv', alarm_rows)
    durations = [r['duracion_logica_s'] for r in alarm_rows if r['origen_encendido'] == 'edge' and r['apagado_edge']]
    save_json('lu-alarmas-resultado.json', dict(ciclos_completos=len(alarm_rows),
              ciclos_edge_con_limpieza_y_apagado_edge=len(durations),
              media_logica_edge_s=round(statistics.mean(durations), 3) if durations else None,
              minimo_logico_edge_s=min(durations) if durations else None,
              maximo_logico_edge_s=max(durations) if durations else None,
              alcance='Timestamps de recepcion serie del PC; duracion del estado logico. No mide sonido, primeros pitidos ni apagado sin red.'))

    # Pares consecutivos sin cambio de estado, salvo uptime/RSSI: latidos observados.
    heartbeats = []
    stable_fields = [f for f in FIELDS if f not in ('uptime_s', 'rssi')]
    for before, after in zip(reports, reports[1:]):
        elapsed = round((dt(after[0])-dt(before[0])).total_seconds(), 3)
        intervening = [m for t, m in serial if before[0] < t < after[0]]
        if (after[1]['uptime_s'] > before[1]['uptime_s']
                and not intervening
                and all(before[1][k] == after[1][k] for k in stable_fields)):
            heartbeats.append(dict(inicio_utc_pc=before[0], fin_utc_pc=after[0], intervalo_s=elapsed))
    save_csv('lu-latidos-serie.csv', heartbeats)
    save_json('lu-latidos-resultado.json', dict(pares_observados=len(heartbeats),
              minimo_s=min(r['intervalo_s'] for r in heartbeats), maximo_s=max(r['intervalo_s'] for r in heartbeats),
              alcance='Pares consecutivos sin cambios de estado excepto uptime/RSSI, uptime creciente y sin eventos serie intermedios. No se seleccionan por el intervalo obtenido. No mide retardo evento a MQTT.'))

    samples = [matched[i] for i in (0, 1, len(matched)//2, len(matched)-1)]
    save_csv('lu-muestras-dynamodb.csv', samples, header)
    source_names = ('lu-monitor-serie.txt', 'lu-resumen-serial.json', 'lu-historico-lecturas-exportado.csv', 'lu-cloudwatch-texto-original.txt')
    save_json('lu-fuentes-sha256.json', {name: hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in source_names})
    print(json.dumps(dict(integridad=integrity['integridad_observada_porcentaje'], reportes=len(reports),
                         aws=aws_summary, alarmas_edge=durations, latidos=len(heartbeats)), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
