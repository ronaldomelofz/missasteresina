"""Auditoria: horarios faltando e duplicados (PDF vs JSON)."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_pdf import parse_pdf
from planilha_common import DAYS, find_newest_pdf, merge_time_lists, parent_key

JSON_PATH = Path(__file__).resolve().parents[1] / "src" / "data" / "igrejas.json"


def find_dupes_in_church(church):
    dupes = []
    for bucket in ("missas", "confissoes", "adoracao"):
        data = church.get(bucket) or {}
        for day in DAYS:
            times = data.get(day) or []
            seen = set()
            for t in times:
                key = t.strip().lower()
                if key in seen:
                    dupes.append((church["nome"], bucket, day, t))
                seen.add(key)
    return dupes


def main():
    pdf = find_newest_pdf()
    parsed = parse_pdf(pdf)
    churches = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    pdf_by_parent = defaultdict(list)
    for row in parsed:
        pdf_by_parent[parent_key(row["nome"])].append(row)

    print(f"Locais no JSON: {len(churches)}")
    print(f"Linhas PDF parseadas: {len(parsed)}")
    print(f"Chaves pai unicas PDF: {len(pdf_by_parent)}")

    print("\n=== SEM MISSAS NO JSON ===")
    sem = [c for c in churches if not any((c.get("missas") or {}).get(d) for d in DAYS)]
    print(f"Total: {len(sem)}")
    for c in sem[:25]:
        print(f"  - {c['nome']}")

    print("\n=== DUPLICATAS (mesmo dia/horario) ===")
    total_dupes = 0
    for c in churches:
        for item in find_dupes_in_church(c):
            print(f"  {item[0][:55]} | {item[1]} {item[2]}: {item[3]}")
            total_dupes += 1
    print(f"Total duplicatas: {total_dupes}")

    print("\n=== CHAVES PAI DUPLICADAS NO JSON ===")
    keys = defaultdict(list)
    for c in churches:
        keys[parent_key(c["nome"])].append(c["nome"])
    for k, names in keys.items():
        if len(names) > 1:
            print(f"  {k}:")
            for n in names:
                print(f"    - {n}")


if __name__ == "__main__":
    main()
