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
    PHONE_RE,
    build_output,
    empty_row,
    find_newest_pdf,
    norm_text,
    split_times,
    write_output,
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
    if not headers:
        return False
    first = headers[0]
    if "paroquia" not in first and "igreja" not in first:
        return False
    return any(h in DAY_HEADERS for h in headers)


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
    head = strip_accents((page_text or "")[:500]).lower()
    first_line = head.split("\n")[0] if head else ""

    if page_index <= 2:
        return "missas"
    if "confiss" in first_line or (page_index >= 5 and "confiss" in head):
        if table_index >= 1 and page_index == 4:
            return "confissoes"
        if page_index >= 5:
            return "confissoes"
    if page_index == 4 and table_index >= 1:
        return "confissoes"
    if "adora" in first_line or "expos" in first_line or "santissimo" in first_line:
        return "adoracao"
    if page_index in (3, 4):
        return "adoracao"
    return "missas"


def is_address_like(inner):
    low = inner.lower()
    if re.search(r"\b(r\.?|av\.?|br\.?|km\s*\d|shop\.?|bairro)\b", low):
        return True
    if re.search(r"\d{3,}", inner):
        return True
    return False


def parse_church_cell(raw):
    text = (raw or "").strip()
    if not text:
        return "", "", "", ""

    nome = text
    endereco = ""
    telefone = ""
    bairro = ""

    phone_tail = PHONE_RE.search(text)
    if phone_tail and phone_tail.end() >= len(text) - 8:
        telefone = phone_tail.group(1).strip()
        text = (text[: phone_tail.start()] + text[phone_tail.end() :]).strip(" /,-")
        nome = text

    paren = text.find("(")
    if paren > 0:
        close = text.rfind(")")
        if close > paren:
            inner = text[paren + 1 : close].strip()
            phone_in_paren = PHONE_RE.search(inner)
            if phone_in_paren:
                telefone = telefone or phone_in_paren.group(1).strip()
                inner = (
                    inner[: phone_in_paren.start()] + inner[phone_in_paren.end() :]
                ).strip(" ,")

            base = text[:paren].strip()
            if is_address_like(inner):
                nome = base
                endereco = inner
                if " - " in inner:
                    parts = inner.rsplit(" - ", 1)
                    if len(parts) == 2 and len(parts[1]) < 45:
                        endereco = parts[0].strip()
                        tail = parts[1].strip()
                        if re.match(r"^[\d\s\-]+$", tail):
                            telefone = telefone or tail
                        else:
                            bairro = tail
            else:
                nome = f"{base} ({inner})".strip()
        else:
            nome = text[:paren].strip()
            endereco = text[paren + 1 :].strip()

    nome = re.sub(r"\s+", " ", nome).strip(" /,-")
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
            target[day] = times

    for bucket_name in ("missas", "confissoes", "adoracao"):
        block = data.get(bucket_name) or {}
        for day in DAYS:
            if block.get(day):
                return data

    return None


def row_from_contact(cells):
    if not cells or not (cells[0] or "").strip():
        return None

    nome, endereco, bairro, telefone_cell = parse_church_cell(cells[0])
    telefone = telefone_cell
    instagram = ""

    if len(cells) > 1 and cells[1]:
        val = str(cells[1]).strip()
        if PHONE_RE.search(val) or re.match(r"^[\d\s\-/]+$", val):
            telefone = telefone or val
        elif not telefone:
            telefone = val

    if len(cells) > 2 and cells[2]:
        raw = str(cells[2]).strip()
        if raw and not PHONE_RE.fullmatch(raw.replace(" ", "")):
            instagram = raw.lstrip("@")

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
