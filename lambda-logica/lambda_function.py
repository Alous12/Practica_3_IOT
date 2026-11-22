# -*- coding: utf-8 -*-
"""Punto de entrada de AWS Lambda (Handler: lambda_function.lambda_handler).

Variables de entorno:
    IOT_ENDPOINT        (obligatoria) p. ej. xxxxxxxx-ats.iot.us-east-2.amazonaws.com
    LINKS_TABLE         tabla de vinculaciones (por defecto vigilante_vinculaciones)
    THING_PREFIX        prefijo de los Things (por defecto vigilante-)
    CONFIRM_TIMEOUT_S   segundos que se espera la confirmación del actuador (por defecto 3)
    STALE_AFTER_S       segundos sin reporte para avisar desconexión (por defecto 150)

No se usan access keys: boto3 toma las credenciales temporales del rol de ejecución.
"""
import logging

import boto3

from vigilante.config import Settings
from vigilante.device_gateway import DeviceGateway
from vigilante.link_repository import LinkRepository
from vigilante.skill import build_skill

logging.getLogger().setLevel(logging.INFO)

_settings = Settings.from_env()
_repository = LinkRepository(boto3.client("dynamodb"), _settings.links_table)
_gateway = DeviceGateway(
    boto3.client("iot"),
    boto3.client("iot-data", endpoint_url="https://" + _settings.iot_endpoint),
    poll_interval_s=_settings.poll_interval_s,
)

lambda_handler = build_skill(_repository, _gateway, _settings).lambda_handler()
