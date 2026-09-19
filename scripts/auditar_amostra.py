"""Audita os CSVs VRA baixados em data/raw/."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd


def read_csv(path: Path) -> pd.DataFrame:
    sample = path.read_bytes()[:100_000]
    encoding = "utf-8-sig"
    text = sample.decode(encoding, errors="replace")
    dialect = csv.Sniffer().sniff(text, delimiters=";,|\t")
    return pd.read_csv(path, sep=dialect.delimiter, encoding=encoding, low_memory=False)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "data" / "raw").glob("*.csv"))
    if not paths:
        raise SystemExit("Nenhum CSV em data/raw/. Execute baixar_amostra.py primeiro.")
    reports = []
    for path in paths:
        frame = read_csv(path)
        report = {
            "arquivo": path.name,
            "linhas": int(len(frame)),
            "colunas": [str(c) for c in frame.columns],
            "duplicatas": int(frame.duplicated().sum()),
            "ausentes_por_coluna": {str(k): int(v) for k, v in frame.isna().sum().items()},
        }
        for candidate in ["Situação do voo", "Situacao do voo", "SITUACAO_VOO"]:
            if candidate in frame.columns:
                report["situacao"] = frame[candidate].value_counts(dropna=False).astype(int).to_dict()
        reports.append(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    (root / "data" / "auditoria_amostra.json").write_text(
        json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
