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

SECONDARY_PATTERNS = [
    r"adoracao\s*$",
    r"expos\.?\s+santissimo",
    r"capela do santissimo",
    r"apos a missa",
    r"antes da missa",
    r"antes ou apos",
    r"\d+\s*min\.?\s+ant",
    r"whats\s*-",
    r"\(manha\)",
    r"\(tarde\)",
    r"no convento\s*$",
    r"secretaria:",
]

PHONE_RE = re.compile(
    r"(?<!\d)(\d{4,5}[-\s]?\d{4}|\(\d{2}\)\s*\d{4,5}[-\s]?\d{4})(?!\d)"
)


def norm_text(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = text.replace("ã", "a").replace("á", "a").replace("é", "e").replace("í", "i")
    text = text.replace("ó", "o").replace("ú", "u").replace("ç", "c")
    return text


def normalize_time_entry(value):
    text = re.sub(r"\s+", " ", str(value or "").strip())
    text = re.sub(r"^\d+\)\s*", "", text)
    return text.strip()


def time_dedupe_key(value):
    return re.sub(r"\s+", "", normalize_time_entry(value).lower())


def split_times(value):
    if value is None or str(value).strip() == "":
        return []
    if isinstance(value, (int, float)):
        return [f"{int(value)}h"]

    text = normalize_time_entry(value)
    if not text:
        return []

    parts = re.split(r"\s+e\s+|\s*;\s*|\s*,\s*(?=\d)", text, flags=re.IGNORECASE)
    out = []
    for part in parts:
        chunk = normalize_time_entry(part)
        if not chunk:
            continue
        if re.search(r"\d", chunk):
            out.append(chunk)
    return out


def expand_times(times):
    expanded = []
    for item in times or []:
        expanded.extend(split_times(item))
    return expanded


def merge_time_lists(existing, new_times):
    seen = set()
    merged = []
    for item in expand_times(list(existing or []) + list(new_times or [])):
        entry = normalize_time_entry(item)
        if not entry:
            continue
        key = time_dedupe_key(entry)
        if key in seen:
            continue
        seen.add(key)
        merged.append(entry)
    return merged


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


def normalize_nome_key(nome):
    key = norm_text(nome)
    key = re.sub(r"\s+", " ", key)
    key = key.replace("ig. de ", "igr. de ")
    key = re.sub(r"\bns\b", "n. s.", key)
    key = re.sub(r"\bparoquia\b", "paroquia", key)
    return key.strip()


def is_secondary_row(nome):
    key = normalize_nome_key(nome)
    return any(re.search(pat, key) for pat in SECONDARY_PATTERNS)


def parent_key(nome):
    key = normalize_nome_key(nome)

    if "gracas" in key and ("hgv" in key or "capela nossa senhora" in key or "capela de nossa senhora" in key):
        if "buenos aires" not in key and "palha" not in key and "santa gemma" not in key:
            return "capela nossa senhora das gracas hgv"

    if "santa clara" in key and (
        "sotero" in key or "copagre" in key or "primavera" in key or "igr." in key or "ig." in key
    ):
        return "igr. de santa clara sotero copagre"

    if "cristo rei" in key and "comunidade aparecida" in key:
        return "paroquia de cristo rei comunidade aparecida"
    if "cristo rei" in key:
        return "paroquia de cristo rei matriz"

    if "sao benedito" in key:
        return "paroquia sao benedito"

    if "sao jose operario" in key:
        return "paroquia sao jose operario"

    if "n. s. das gracas" in key and "capela de palha" in key:
        return "paroquia n. s. das gracas capela palha"

    if "n. s. das gracas" in key and "santa gemma" in key:
        return "paroquia n. s. das gracas santa gemma"

    if "n. s. das gracas" in key and "buenos aires" in key:
        return "paroquia n. s. das gracas buenos aires"

    if "n. s. das dores" in key and "catedral" in key:
        return "paroquia n. s. das dores catedral"

    for pat in SECONDARY_PATTERNS:
        key = re.sub(pat, "", key, flags=re.IGNORECASE)

    key = re.sub(r"\s*\([^)]*\)\s*$", "", key).strip()
    key = re.sub(r"\s+\d{4,}[-/ ].*$", "", key)
    key = re.sub(r"\s+/\s+.*$", "", key)
    key = re.sub(r"\s+matriz\s*$", "", key)
    key = re.sub(r"\s+", " ", key).strip()
    return key


def match_key(nome):
    return parent_key(nome)


def nome_quality_score(nome, row_data):
    score = len(nome or "")
    if any(row_data.get("missas", {}).get(d) for d in DAYS):
        score += 200
    if row_data.get("endereco"):
        score += 30
    if is_secondary_row(nome):
        score -= 100
    if PHONE_RE.search(nome or ""):
        score -= 20
    return score


def load_existing():
    if not OUTPUT_JSON.exists():
        return []
    return json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))


def index_existing(items):
    by_id = {}
    by_parent = {}
    for item in items:
        if item.get("id") is not None:
            by_id[int(item["id"])] = item
        pk = parent_key(item.get("nome") or "")
        if pk and pk not in by_parent:
            by_parent[pk] = item
    return by_id, by_parent


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

    candidate_nome = row_data.get("nome") or ""
    if nome_quality_score(candidate_nome, row_data) > nome_quality_score(
        merged.get("nome") or "", merged
    ):
        merged["nome"] = candidate_nome

    for key in ("endereco", "bairro", "telefone", "instagram"):
        if row_data.get(key) not in (None, ""):
            if key == "telefone" and merged.get("telefone"):
                if row_data[key] not in merged["telefone"]:
                    merged["telefone"] = f"{merged['telefone']} / {row_data[key]}"
            else:
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
            if not times:
                continue
            if bucket == "missas":
                merged[bucket][day] = merge_time_lists(merged[bucket].get(day), times)
            else:
                if day not in merged[bucket]:
                    merged[bucket][day] = []
                merged[bucket][day] = merge_time_lists(merged[bucket].get(day), times)

    if merged.get("missas") == {}:
        merged["missas"] = empty_schedules()

    return merged


def dedupe_church(church):
    for bucket in ("missas", "confissoes", "adoracao"):
        data = church.get(bucket) or {}
        for day in list(data.keys()):
            data[day] = merge_time_lists([], data.get(day))
        church[bucket] = data
    return church


def build_output(parsed_rows):
    existing = load_existing()
    by_id, by_parent = index_existing(existing)
    batch = {}
    used_ids = set()

    for row in parsed_rows:
        pk = parent_key(row["nome"])
        base = batch.get(pk)
        if not base:
            base = by_parent.get(pk)
        merged = merge_church(base, row)

        if merged.get("id") is None:
            next_id = max(used_ids.union({i.get("id", 0) for i in existing}), default=0) + 1
            while next_id in used_ids or next_id in by_id:
                next_id += 1
            merged["id"] = next_id

        used_ids.add(int(merged["id"]))
        batch[pk] = dedupe_church(merged)

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
