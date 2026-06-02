"""Gera PLANILHA/MISSAS_TERESINA.xlsx a partir do igrejas.json atual."""
import json
from pathlib import Path

import openpyxl
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
OUT = WORKSPACE / "PLANILHA" / "MISSAS_TERESINA.xlsx"
SRC = ROOT / "src" / "data" / "igrejas.json"
DAYS = ["domingo", "segunda", "terca", "quarta", "quinta", "sexta", "sabado"]


def join_times(values):
    if not values:
        return ""
    return "; ".join(values)


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    wb = Workbook()
    ws = wb.active
    ws.title = "IGREJAS"

    headers = [
        "id",
        "nome",
        "endereco",
        "bairro",
        "telefone",
        "instagram",
        "lat",
        "lng",
    ]
    for day in DAYS:
        headers.append(f"missa_{day}")
    for day in DAYS:
        headers.append(f"confissao_{day}")
    for day in DAYS:
        headers.append(f"adoracao_{day}")

    ws.append(headers)

    for item in data:
        row = [
            item.get("id"),
            item.get("nome", ""),
            item.get("endereco", ""),
            item.get("bairro", ""),
            item.get("telefone", ""),
            item.get("instagram", ""),
            item.get("lat"),
            item.get("lng"),
        ]
        missas = item.get("missas") or {}
        conf = item.get("confissoes") or {}
        ador = item.get("adoracao") or {}
        for day in DAYS:
            row.append(join_times(missas.get(day, [])))
        for day in DAYS:
            row.append(join_times(conf.get(day, [])))
        for day in DAYS:
            row.append(join_times(ador.get(day, [])))
        ws.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"Modelo gerado: {OUT}")


if __name__ == "__main__":
    main()
