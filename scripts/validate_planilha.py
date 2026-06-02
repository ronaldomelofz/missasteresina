"""Valida igrejas.json após exportação da planilha."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "src" / "data" / "igrejas.json"
DAYS = ["domingo", "segunda", "terca", "quarta", "quinta", "sexta", "sabado"]


def main():
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {JSON_PATH}")

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("JSON sem registros.")

    names = set()
    for item in data:
        nome = (item.get("nome") or "").strip()
        if not nome:
            raise ValueError("Registro sem nome.")
        key = nome.lower()
        if key in names:
            raise ValueError(f"Nome duplicado: {nome}")
        names.add(key)

        if item.get("id") is None:
            raise ValueError(f"Registro sem id: {nome}")

        missas = item.get("missas") or {}
        if not isinstance(missas, dict):
            raise ValueError(f"Campo missas invalido em: {nome}")
        for day in DAYS:
            if day in missas and not isinstance(missas[day], list):
                raise ValueError(f"Horarios de missa invalidos ({day}) em: {nome}")

    print(f"[OK] {len(data)} locais validados.")
    return 0


if __name__ == "__main__":
  main()
