"""Utilitários compartilhados entre export_planilha e export_pdf."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PLANILHA_DIR = WORKSPACE / "PLANILHA"
OUTPUT_JSON = ROOT / "src" / "data" / "igrejas.json"

DAYS = ["domingo", "segunda", "terca", "quarta", "quinta", "sexta", "sabado"]
DAY_HEADERS = {
    "domingo": "domingo",
    "dom": "domingo",
    "seg": "segunda",
    "segunda": "segunda",
    "ter": "terca",
    "terca": "terca",
    "terça": "terca",
    "qua": "quarta",
    "quarta": "quarta",
    "qui": "quinta",
    "quinta": "quinta",
    "sex": "sexta",
    "sexta": "sexta",
    "sab": "sabado",
    "sáb": "sabado",
    "sabado": "sabado",
    "sábado": "sabado",
}


def norm_text(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = text.replace("ã", "a").replace("á", "a").replace("é", "e").replace("í", "i")
    text = text.replace("ó", "o").replace("ú", "u").replace("ç", "c")
    return text


def split_times(value):
    if value is None or str(value).strip() == "":
        return []
    if isinstance(value, (int, float)):
        return [f"{int(value)}h"]
    parts = re.split(r"[;|,/\n]+", str(value))
    out = []
    for p in parts:
        t = p.strip()
        if t:
            out.append(t)
    return out


def empty_schedules():
    return {d: [] for d in DAYS}


def empty_row():
    return {
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
        name = match_key(item.get("nome") or "")
        if name:
            by_name[name] = item
    return by_id, by_name


def match_key(nome):
    key = norm_text(nome)
    key = re.sub(r"\s*\([^)]*\)\s*$", "", key).strip()
    key = re.sub(
        r"\s+(adoracao|expos\.?|confissao|apos a missa|matriz|capela).*$",
        "",
        key,
    )
    key = re.sub(r"\s+\d{4,}.*$", "", key)
    return key.strip()


def merge_church(base, row_data):
    merged = json.loads(json.dumps(base)) if base else empty_row().copy()
    if not base:
        merged.update(
            {
                "id": row_data.get("id"),
                "nome": row_data.get("nome", ""),
                "endereco": row_data.get("endereco", ""),
                "bairro": row_data.get("bairro", ""),
                "telefone": row_data.get("telefone", ""),
                "instagram": row_data.get("instagram", ""),
            }
        )

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

    if merged.get("missas") == {}:
        merged["missas"] = empty_schedules()

    return merged


def build_output(parsed_rows):
    existing = load_existing()
    by_id, by_name = index_existing(existing)
    batch = {}
    used_ids = set()

    for row in parsed_rows:
        base = None
        key = match_key(row["nome"])
        if key in batch:
            base = batch[key]
        elif row.get("id") is not None and int(row["id"]) in by_id:
            base = by_id[int(row["id"])]
        elif key in by_name:
            base = by_name[key]

        merged = merge_church(base, row)
        if merged.get("id") is None:
            next_id = max(used_ids.union({i.get("id", 0) for i in existing}), default=0) + 1
            while next_id in used_ids or next_id in by_id:
                next_id += 1
            merged["id"] = next_id

        used_ids.add(int(merged["id"]))
        batch[match_key(merged["nome"])] = merged

    output = list(batch.values())
    output.sort(key=lambda x: (x.get("nome") or "").lower())
    return output


def find_newest_pdf():
    pdfs = list(PLANILHA_DIR.glob("*.pdf"))
    if not pdfs:
        return None
    return max(pdfs, key=lambda p: p.stat().st_mtime)


def write_output(churches, source):
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(churches, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Arquivo gerado: {OUTPUT_JSON}")
    print(f"Origem: {source}")
    print(f"Total de locais: {len(churches)}")
