"""
Lê o PDF mais recente em PLANILHA/*.pdf e gera src/data/igrejas.json.
Preserva lat/lng e campos do JSON atual (merge por id ou nome).
"""
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pdfplumber

from planilha_common import (
    DAY_HEADERS,
    DAYS,
    build_output,
    empty_row,
    empty_schedules,
    find_newest_pdf,
    split_times,
    write_output,
)

PHONE_RE = re.compile(
    r"(?<!\d)(\d{4,5}[-\s]?\d{4}|\(\d{2}\)\s*\d{4,5}[-\s]?\d{4})(?!\d)"
)


def strip_accents(text):
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def norm_header(cell):
    return strip_accents((cell or "").strip()).lower()


def is_schedule_table(table):
    if not table or len(table) < 2:
        return False
    headers = [norm_header(c) for c in table[0]]
    return "paroquia / igreja" in headers[0] or "paroquia" in headers[0]


def is_contact_table(table):
    if not table or len(table) < 2:
        return False
    headers = [norm_header(c) for c in table[0]]
    return "telefone" in headers and "instagram" in headers


def map_day_columns(headers):
    mapping = {}
    for idx, h in enumerate(headers):
        key = DAY_HEADERS.get(h)
        if key:
            mapping[idx] = key
    return mapping


def classify_page_section(page_text, page_index, table_index):
    head = strip_accents((page_text or "")[:400]).lower()
    if page_index <= 2:
        return "missas"
    if "confiss" in head and "adora" not in head.split("\n")[0]:
        return "confissoes"
    if page_index == 4 and table_index >= 1:
        return "confissoes"
    if "adora" in head or "expos" in head or "santissimo" in head:
        return "adoracao"
    if page_index == 5 and table_index == 0:
        return "confissoes"
    return "missas"


def parse_church_cell(raw):
    text = (raw or "").strip()
    if not text:
        return "", "", "", ""

    nome = text
    endereco = ""
    telefone = ""
    bairro = ""

    phone_match = PHONE_RE.search(text)
    if phone_match:
        telefone = phone_match.group(1).strip()
        text_wo = text[: phone_match.start()].strip() + " " + text[phone_match.end() :].strip()
        text_wo = re.sub(r"\s+", " ", text_wo).strip(" ,")
        text = text_wo or text

    paren = text.rfind("(")
    if paren > 0 and ")" in text[paren:]:
        close = text.find(")", paren)
        inner = text[paren + 1 : close].strip()
        nome = text[:paren].strip()
        endereco = inner
        if " - " in inner:
            parts = inner.rsplit(" - ", 1)
            if len(parts) == 2 and len(parts[1]) < 40:
                endereco = parts[0].strip()
                bairro = parts[1].strip()
    else:
        nome = text

    nome = re.sub(r"\s+", " ", nome).strip()
    return nome, endereco, bairro, telefone


def row_from_schedule(cells, day_cols, bucket):
    if not cells or not (cells[0] or "").strip():
        return None

    nome, endereco, bairro, telefone = parse_church_cell(cells[0])
    if not nome:
        return None

    data = empty_row()
    data["nome"] = nome
    data["endereco"] = endereco
    data["bairro"] = bairro
    data["telefone"] = telefone

    target = data["missas"] if bucket == "missas" else data[bucket]

    for col_idx, day in day_cols.items():
        if col_idx >= len(cells):
            continue
        times = split_times(cells[col_idx])
        if times:
            if bucket == "missas":
                target[day] = times
            else:
                target[day] = times

    return data


def row_from_contact(cells):
    if not cells or not (cells[0] or "").strip():
        return None

    nome, endereco, bairro, telefone_cell = parse_church_cell(cells[0])
    telefone = telefone_cell
    instagram = ""
    facebook = ""

    if len(cells) > 1 and cells[1]:
        if not telefone:
            telefone = str(cells[1]).strip()
        else:
            extra = str(cells[1]).strip()
            if extra and extra != telefone:
                telefone = f"{telefone} / {extra}" if telefone else extra

    if len(cells) > 2 and cells[2]:
        instagram = str(cells[2]).strip().lstrip("@")
    if len(cells) > 3 and cells[3]:
        facebook = str(cells[3]).strip()

    data = empty_row()
    data["nome"] = nome
    data["endereco"] = endereco
    data["bairro"] = bairro
    data["telefone"] = telefone
    if instagram:
        data["instagram"] = instagram
    return data


def parse_pdf(pdf_path):
    parsed = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            tables = page.extract_tables() or []

            for table_index, table in enumerate(tables):
                if is_contact_table(table):
                    for row in table[1:]:
                        data = row_from_contact(row)
                        if data:
                            parsed.append(data)
                    continue

                if not is_schedule_table(table):
                    continue

                headers = [norm_header(c) for c in table[0]]
                day_cols = map_day_columns(headers)
                if not day_cols:
                    continue

                bucket = classify_page_section(page_text, page_index, table_index)
                for row in table[1:]:
                    data = row_from_schedule(row, day_cols, bucket)
                    if data:
                        parsed.append(data)

    if not parsed:
        raise ValueError("Nenhum dado extraido do PDF.")

    return parsed


def main():
    pdf_path = find_newest_pdf()
    if not pdf_path:
        raise FileNotFoundError(
            f"Nenhum PDF em {Path(__file__).resolve().parents[1].parent / 'PLANILHA'}. "
            "Coloque o arquivo atualizado na pasta PLANILHA."
        )

    print(f"PDF selecionado (mais recente): {pdf_path.name}")
    print(f"Modificado em: {datetime.fromtimestamp(pdf_path.stat().st_mtime)}")

    rows = parse_pdf(pdf_path)
    churches = build_output(rows)
    write_output(churches, pdf_path)
    print(f"Gerado em: {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
