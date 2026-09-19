"""Gera o dataset VRA derivado usando booleanos anuláveis."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from preparar_dados import RAW_TO_DERIVED, read_vra


def transform_v2(frame: pd.DataFrame, source: str) -> pd.DataFrame:
    result = frame[list(RAW_TO_DERIVED)].rename(columns=RAW_TO_DERIVED).copy()
    for column in ["partida_prevista", "partida_real", "chegada_prevista", "chegada_real"]:
        result[column] = pd.to_datetime(result[column], dayfirst=True, errors="coerce")
    result["cancelado"] = result["situacao_voo"].eq("CANCELADO").astype("boolean")
    result["realizado"] = result["situacao_voo"].eq("REALIZADO").astype("boolean")
    result["atraso_partida_min"] = ((result["partida_real"] - result["partida_prevista"]).dt.total_seconds() / 60).round(1)
    result["atraso_chegada_min"] = ((result["chegada_real"] - result["chegada_prevista"]).dt.total_seconds() / 60).round(1)
    result["atraso_partida_15m"] = result["atraso_partida_min"].ge(15).astype("boolean")
    result["atraso_chegada_15m"] = result["atraso_chegada_min"].ge(15).astype("boolean")
    result.loc[~result["realizado"], ["atraso_partida_15m", "atraso_chegada_15m"]] = pd.NA
    result["arquivo_origem"] = source
    result["linha_origem"] = range(1, len(result) + 1)
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "data" / "raw").glob("VRA_*.csv"))
    if not paths:
        raise SystemExit("Nenhum VRA_*.csv em data/raw/.")
    result = pd.concat([transform_v2(read_vra(path), path.name) for path in paths], ignore_index=True)
    output = root / "data" / "voos_vra_derivados.csv"
    result.to_csv(output, index=False, encoding="utf-8")
    print(f"Arquivo: {output}")
    print(f"Linhas: {len(result)}")
    print(f"Realizados: {int(result['realizado'].sum())}")
    print(f"Cancelados: {int(result['cancelado'].sum())}")
    print(f"Atrasos de chegada >= 15 min: {int(result['atraso_chegada_15m'].fillna(False).sum())}")


if __name__ == "__main__":
    main()
