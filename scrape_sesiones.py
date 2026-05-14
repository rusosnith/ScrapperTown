#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

WS_URL = "https://parlamentaria.legislatura.gob.ar/webservices/Json.asmx/GetSesionesAvanzado"
DETAIL_URL_TEMPLATE = "https://www.legislatura.gob.ar/InfoSesion/{session_id}"
ARCHIVO_SESIONES = "sesiones_legislatura.csv"
FECHA_INICIO_HISTORICA = "01/01/1997"


@dataclass
class Sesion:
    id_sesion_lp: str
    nro_orden_lp: str
    ano_parlamentario: str
    fecha: str
    id_sesion_tipo: str
    abrev_sesion_tipo: str
    dsc_sesion_tipo: str
    labor_documento: str
    prelabor_documento: str
    asuntos_considerados_documento: str
    archivo_vt: str
    url_detalle: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrapea sesiones de la Legislatura de CABA por rango de fechas."
    )
    parser.add_argument(
        "--desde",
        help="Fecha inicial. Acepta dd/mm/yyyy o yyyy-mm-dd.",
    )
    parser.add_argument(
        "--hasta",
        help="Fecha final. Acepta dd/mm/yyyy o yyyy-mm-dd.",
    )
    parser.add_argument(
        "--formato",
        choices=("json", "csv"),
        default="csv",
        help="Formato de salida. Default: csv.",
    )
    parser.add_argument(
        "--salida",
        help="Ruta del archivo de salida. Si se omite, imprime en stdout.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout HTTP en segundos. Default: 30.",
    )
    return parser.parse_args()


def normalize_date(value: str) -> tuple[str, datetime]:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%d/%m/%Y"), parsed
        except ValueError:
            pass
    raise ValueError(f"Fecha invalida: {value!r}. Usa dd/mm/yyyy o yyyy-mm-dd.")


def parse_session_date(value: str) -> datetime | None:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def load_existing_sessions(output_path: str) -> list[dict[str, str]]:
    if not os.path.exists(output_path):
        return []

    try:
        with open(output_path, "r", encoding="utf-8") as archivo:
            reader = csv.DictReader(archivo)
            return [fila for fila in reader]
    except Exception as exc:
        print(f"No se pudo cargar el archivo existente {output_path}: {exc}", file=sys.stderr)
        return []


def infer_date_range(existing_sessions: list[dict[str, str]]) -> tuple[str, str]:
    if not existing_sessions:
        desde = FECHA_INICIO_HISTORICA
    else:
        fechas_validas = [
            fecha
            for fecha in (parse_session_date(fila.get("fecha", "")) for fila in existing_sessions)
            if fecha is not None
        ]
        if fechas_validas:
            ultima_fecha = max(fechas_validas)
            desde = ultima_fecha.strftime("%d/%m/%Y")
        else:
            desde = FECHA_INICIO_HISTORICA

    hasta = datetime.now().strftime("%d/%m/%Y")
    return desde, hasta


def iter_date_ranges(desde_dt: datetime, hasta_dt: datetime) -> list[tuple[str, str]]:
    ranges: list[tuple[str, str]] = []
    current_start = desde_dt

    while current_start <= hasta_dt:
        current_end = datetime(current_start.year, 12, 31)
        if current_end > hasta_dt:
            current_end = hasta_dt

        ranges.append(
            (
                current_start.strftime("%d/%m/%Y"),
                current_end.strftime("%d/%m/%Y"),
            )
        )
        current_start = current_end + timedelta(days=1)

    return ranges


def fetch_sessions_in_ranges(desde_dt: datetime, hasta_dt: datetime, timeout: int) -> list[Sesion]:
    sessions: list[Sesion] = []
    for rango_desde, rango_hasta in iter_date_ranges(desde_dt, hasta_dt):
        sessions.extend(fetch_sessions(rango_desde, rango_hasta, timeout=timeout))
    return sessions


def merge_sessions(
    existing_sessions: list[dict[str, str]],
    new_sessions: list[Sesion],
) -> list[dict[str, str]]:
    sesiones_por_id = {
        fila.get("id_sesion_lp", ""): fila
        for fila in existing_sessions
        if fila.get("id_sesion_lp")
    }

    for session in new_sessions:
        sesiones_por_id[session.id_sesion_lp] = asdict(session)

    merged_sessions = list(sesiones_por_id.values())
    merged_sessions.sort(
        key=lambda fila: (
            parse_session_date(fila.get("fecha", "")) or datetime.min,
            fila.get("id_sesion_lp", ""),
        )
    )
    return merged_sessions


def fetch_sessions(fecha_desde: str, fecha_hasta: str, timeout: int) -> list[Sesion]:
    payload = urllib.parse.urlencode(
        {"FechaDesde": fecha_desde, "FechaHasta": fecha_hasta}
    ).encode("utf-8")
    request = urllib.request.Request(
        WS_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            xml_bytes = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"No se pudo consultar el webservice: {exc}") from exc

    root = ET.fromstring(xml_bytes)
    sessions: list[Sesion] = []

    # El XML viene con namespace por defecto, por eso se recorren tags por sufijo.
    for node in root.iter():
        if not node.tag.endswith("sesiones"):
            continue
        get = lambda name: text_by_suffix(node, name)
        session_id = get("id_sesion_lp")
        sessions.append(
            Sesion(
                id_sesion_lp=session_id,
                nro_orden_lp=get("nro_orden_lp"),
                ano_parlamentario=get("ano_parlamentario"),
                fecha=get("fch_sesion_lp"),
                id_sesion_tipo=get("id_sesion_tipo"),
                abrev_sesion_tipo=get("abrev_sesion_tipo"),
                dsc_sesion_tipo=get("dsc_sesion_tipo"),
                labor_documento=get("labor_documento"),
                prelabor_documento=get("prelabor_documento"),
                asuntos_considerados_documento=get("asuntos_considerados_documento"),
                archivo_vt=get("archivo_vt"),
                url_detalle=DETAIL_URL_TEMPLATE.format(session_id=session_id),
            )
        )

    return sessions


def text_by_suffix(node: ET.Element, suffix: str) -> str:
    for child in node:
        if child.tag.endswith(suffix):
            return (child.text or "").strip()
    return ""


def serialize_json(sessions: list[Sesion]) -> str:
    return json.dumps([asdict(session) for session in sessions], ensure_ascii=False, indent=2)


def serialize_csv(sessions: list[Sesion]) -> str:
    if not sessions:
        headers = [field.name for field in Sesion.__dataclass_fields__.values()]
        rows: list[dict[str, str]] = []
    else:
        headers = list(asdict(sessions[0]).keys())
        rows = [asdict(session) for session in sessions]

    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def write_output(content: str, output_path: str | None) -> None:
    if output_path:
        path = Path(output_path)
        path.write_text(content, encoding="utf-8")
        print(f"Se guardaron los resultados en: {path.resolve()}", file=sys.stderr)
        return
    sys.stdout.write(content)
    if not content.endswith("\n"):
        sys.stdout.write("\n")


def write_csv_file(sessions: list[dict[str, str]], output_path: str) -> None:
    headers = [field.name for field in Sesion.__dataclass_fields__.values()]
    with open(output_path, "w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sessions)
    print(f"Se guardaron los resultados en: {Path(output_path).resolve()}", file=sys.stderr)


def main() -> int:
    args = parse_args()

    if bool(args.desde) != bool(args.hasta):
        print(
            "Debes informar --desde y --hasta juntos, o no informar ninguno para modo automático.",
            file=sys.stderr,
        )
        return 2

    usar_rango_automatico = not args.desde and not args.hasta
    dataset_output_path = args.salida or ARCHIVO_SESIONES
    existing_sessions = load_existing_sessions(dataset_output_path)

    try:
        if usar_rango_automatico:
            desde_text, hasta_text = infer_date_range(existing_sessions)
            desde_dt = datetime.strptime(desde_text, "%d/%m/%Y")
            hasta_dt = datetime.strptime(hasta_text, "%d/%m/%Y")
        else:
            desde_text, desde_dt = normalize_date(args.desde)
            hasta_text, hasta_dt = normalize_date(args.hasta)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if desde_dt > hasta_dt:
        print("La fecha --desde no puede ser mayor que --hasta.", file=sys.stderr)
        return 2

    try:
        sessions = fetch_sessions_in_ranges(desde_dt, hasta_dt, timeout=args.timeout)
    except (RuntimeError, ET.ParseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if usar_rango_automatico and args.formato == "csv":
        merged_sessions = merge_sessions(existing_sessions, sessions)
        write_csv_file(merged_sessions, dataset_output_path)
    else:
        content = serialize_json(sessions) if args.formato == "json" else serialize_csv(sessions)
        write_output(content, args.salida)

    print(f"Sesiones encontradas: {len(sessions)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
