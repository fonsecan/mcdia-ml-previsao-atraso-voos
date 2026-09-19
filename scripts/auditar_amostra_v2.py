"""Audita CSVs VRA com detecção de codificação e da coluna de situação."""
from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from pathlib import Path

import pandas as pd


def normalizado(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(char for char in text if not unicodedata.combining(char)).lower().replace(" ", "")


def ler(path: Path) -> tuple[pd.DataFrame, str]:
    sample = path.read_bytes()[:100_000]
    encodings = ["utf-8-sig", "cp1252", "latin1"]
    encoding = min(encodings, key=lambda item: sample.decode(item, errors="replace").count("�"))
    dialect = csv.Sniffer().sniff(sample.decode(encoding, errors="replace"), delimiters=";,|\t")
    return pd.read_csv(path, sep=dialect.delimiter, encoding=encoding, low_memory=False), encoding


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="data/raw")
    parser.add_argument("--output", default="data/auditoria_amostra.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / args.input_dir).glob("*.csv"))
    if not paths:
        raise SystemExit(f"Nenhum CSV em {args.input_dir}/. Execute baixar_amostra.py primeiro.")
    reports = []
    for path in paths:
        frame, encoding = ler(path)
        report = {
            "arquivo": path.name,
            "encoding": encoding,
            "linhas": int(len(frame)),
            "colunas": [str(c) for c in frame.columns],
            "duplicatas": int(frame.duplicated().sum()),
            "ausentes_por_coluna": {str(k): int(v) for k, v in frame.isna().sum().items()},
        }
        status = next((c for c in frame.columns if "situacao" in normalizado(c) and "voo" in normalizado(c)), None)
        if status is not None:
            report["coluna_situacao"] = status
            report["situacao"] = frame[status].value_counts(dropna=False).astype(int).to_dict()
        reports.append(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
