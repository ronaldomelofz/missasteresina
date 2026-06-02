"""
Lê PLANILHA/MISSAS_TERESINA.xlsx e gera src/data/igrejas.json.
Preserva lat/lng e campos não informados na planilha (merge por id ou nome).
"""
import json
import re
from datetime import datetime
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SPREADSHEET = WORKSPACE / "PLANILHA" / "MISSAS_TERESINA.xlsx"
OUTPUT_JSON = ROOT / "src" / "data" / "igrejas.json"

DAYS = ["domingo", "segunda", "terca", "quarta", "quinta", "sexta", "sabado"]
DAY_ALIASES = {
    "domingo": "domingo",
    "dom": "domingo",
    "segunda": "segunda",
    "seg": "segunda",
    "terca": "terca",
    "terça": "terca",
    "ter": "terca",
    "quarta": "quarta",
    "qua": "quarta",
    "quinta": "quinta",
    "qui": "quinta",
    "sexta": "sexta",
    "sex": "sexta",
    "sabado": "sabado",
    "sábado": "sabado",
    "sab": "sabado",
}

FIELD_MAP = {
    "id": "id",
    "nome": "nome",
    "endereco": "endereco",
    "endereço": "endereco",
    "bairro": "bairro",
    "telefone": "telefone",
    "instagram": "instagram",
    "lat": "lat",
    "lng": "lng",
    "longitude": "lng",
    "latitude": "lat",
}


def norm_header(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = text.replace("ã", "a").replace("á", "a").replace("é", "e").replace("í", "i")
    text = text.replace("ó", "o").replace("ú", "u").replace("ç", "c")
    return re.sub(r"\s+", "_", text)


def split_times(value):
    if value is None or str(value).strip() == "":
        return []
    if isinstance(value, (int, float)):
        h = int(value)
        return [f"{h}h"]
    parts = re.split(r"[;|,/\n]+", str(value))
    out = []
    for p in parts:
        t = p.strip()
        if t:
            out.append(t)
    return out


def parse_float(value):
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def classify_column(header):
    h = norm_header(header)
    if h in FIELD_MAP:
        return ("field", FIELD_MAP[h])

    for prefix, bucket in (
        ("missa_", "missas"),
        ("missas_", "missas"),
        ("confissao_", "confissoes"),
        ("confissoes_", "confissoes"),
        ("conf_", "confissoes"),
        ("adoracao_", "adoracao"),
        ("adoracao_", "adoracao"),
        ("ador_", "adoracao"),
    ):
        if h.startswith(prefix):
            day_key = h[len(prefix) :]
            day = DAY_ALIASES.get(day_key, day_key)
            if day in DAYS:
                return (bucket, day)

    return None


def empty_schedules():
    return {d: [] for d in DAYS}


def load_existing():
    if not OUTPUT_JSON.exists():
        return []
    return json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))


def index_existing(items):
    by_id = {}
    by_name = {}
    for item in items:
        if item.get("id") is not None:
            by_id[int(item["id"])] = item
        name = (item.get("nome") or "").strip().lower()
        if name:
            by_name[name] = item
    return by_id, by_name


def merge_church(base, row_data):
    merged = json.loads(json.dumps(base)) if base else {
        "id": row_data.get("id"),
        "nome": row_data.get("nome", ""),
        "endereco": row_data.get("endereco", ""),
        "bairro": row_data.get("bairro", ""),
        "telefone": row_data.get("telefone", ""),
        "instagram": row_data.get("instagram", ""),
        "lat": None,
        "lng": None,
        "missas": empty_schedules(),
        "confissoes": {},
        "adoracao": {},
    }

    for key in ("nome", "endereco", "bairro", "telefone", "instagram"):
        if row_data.get(key) not in (None, ""):
            merged[key] = row_data[key]

    if row_data.get("id") is not None:
        merged["id"] = row_data["id"]

    lat = row_data.get("lat")
    lng = row_data.get("lng")
    if lat is not None:
        merged["lat"] = lat
    if lng is not None:
        merged["lng"] = lng

    for bucket in ("missas", "confissoes", "adoracao"):
        if bucket not in merged or not isinstance(merged[bucket], dict):
            merged[bucket] = {} if bucket != "missas" else empty_schedules()
        for day, times in (row_data.get(bucket) or {}).items():
            if times:
                merged[bucket][day] = times

    if "missas" in merged and merged["missas"] == {}:
        merged["missas"] = empty_schedules()

    return merged


def read_workbook():
    if not SPREADSHEET.exists():
        raise FileNotFoundError(f"Planilha nao encontrada: {SPREADSHEET}")

    wb = openpyxl.load_workbook(SPREADSHEET, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Planilha vazia.")

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    col_map = []
    for h in headers:
        col_map.append(classify_column(h))

    parsed_rows = []
    for row in rows[1:]:
        if not any(cell is not None and str(cell).strip() != "" for cell in row):
            continue

        data = {
            "id": None,
            "nome": "",
            "endereco": "",
            "bairro": "",
            "telefone": "",
            "instagram": "",
            "lat": None,
            "lng": None,
            "missas": empty_schedules(),
            "confissoes": {},
            "adoracao": {},
        }

        for idx, cell in enumerate(row):
            if idx >= len(col_map):
                break
            kind = col_map[idx]
            if not kind:
                continue
            bucket, field = kind
            if bucket == "field":
                if field == "id" and cell is not None and str(cell).strip() != "":
                    data["id"] = int(float(cell)) if isinstance(cell, (int, float)) else int(str(cell).strip())
                elif field in ("lat", "lng"):
                    data[field] = parse_float(cell)
                else:
                    data[field] = "" if cell is None else str(cell).strip()
            else:
                times = split_times(cell)
                if times:
                    data[bucket][field] = times

        if not data["nome"]:
            continue
        parsed_rows.append(data)

    if not parsed_rows:
        raise ValueError("Nenhuma igreja encontrada na planilha.")

    return parsed_rows


def build_output(parsed_rows):
    existing = load_existing()
    by_id, by_name = index_existing(existing)
    output = []
    used_ids = set()

    for row in parsed_rows:
        base = None
        if row.get("id") is not None and int(row["id"]) in by_id:
            base = by_id[int(row["id"])]
        else:
            name_key = row["nome"].strip().lower()
            base = by_name.get(name_key)

        merged = merge_church(base, row)
        if merged.get("id") is None:
            next_id = max(used_ids.union({i.get("id", 0) for i in existing}), default=0) + 1
            while next_id in used_ids or next_id in by_id:
                next_id += 1
            merged["id"] = next_id

        used_ids.add(int(merged["id"]))
        output.append(merged)

    output.sort(key=lambda x: (x.get("nome") or "").lower())
    return output


def main():
    parsed_rows = read_workbook()
    churches = build_output(parsed_rows)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(churches, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Arquivo gerado: {OUTPUT_JSON}")
    print(f"Origem: {SPREADSHEET}")
    print(f"Total de locais: {len(churches)}")
    print(f"Gerado em: {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
