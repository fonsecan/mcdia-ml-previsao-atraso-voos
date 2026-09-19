"""Converte arquivos mensais VRA em uma tabela derivada com alvos de atraso."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


RAW_TO_DERIVED = {
    "Sigla ICAO Empresa Aérea": "companhia_icao",
    "Empresa Aérea": "empresa",
    "Número Voo": "numero_voo",
    "Código DI": "codigo_di",
    "Código Tipo Linha": "codigo_tipo_linha",
    "Modelo Equipamento": "modelo_equipamento",
    "Número de Assentos": "numero_assentos",
    "Sigla ICAO Aeroporto Origem": "origem_icao",
    "Descrição Aeroporto Origem": "origem_descricao",
    "Partida Prevista": "partida_prevista",
    "Partida Real": "partida_real",
    "Sigla ICAO Aeroporto Destino": "destino_icao",
    "Descrição Aeroporto Destino": "destino_descricao",
    "Chegada Prevista": "chegada_prevista",
    "Chegada Real": "chegada_real",
    "Situação Voo": "situacao_voo",
    "Situação Partida": "situacao_partida",
    "Situação Chegada": "situacao_chegada",
    "Codeshare": "codeshare",
}


def read_vra(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="utf-8-sig", low_memory=False)


def transform(frame: pd.DataFrame, source: str) -> pd.DataFrame:
    missing = sorted(set(RAW_TO_DERIVED) - set(frame.columns))
    if missing:
        raise ValueError(f"Colunas ausentes em {source}: {missing}")
    result = frame[list(RAW_TO_DERIVED)].rename(columns=RAW_TO_DERIVED).copy()
    for column in ["partida_prevista", "partida_real", "chegada_prevista", "chegada_real"]:
        result[column] = pd.to_datetime(result[column], dayfirst=True, errors="coerce")
    result["cancelado"] = result["situacao_voo"].eq("CANCELADO")
    result["realizado"] = result["situacao_voo"].eq("REALIZADO")
    result["atraso_partida_min"] = (
        (result["partida_real"] - result["partida_prevista"]).dt.total_seconds() / 60
    ).round(1)
    result["atraso_chegada_min"] = (
        (result["chegada_real"] - result["chegada_prevista"]).dt.total_seconds() / 60
    ).round(1)
    result["atraso_partida_15m"] = result["atraso_partida_min"].ge(15)
    result["atraso_chegada_15m"] = result["atraso_chegada_min"].ge(15)
    result.loc[~result["realizado"], ["atraso_partida_15m", "atraso_chegada_15m"]] = pd.NA
    result["arquivo_origem"] = source
    result["linha_origem"] = range(1, len(result) + 1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", default="data/voos_vra_derivados.csv")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "data" / "raw").glob("VRA_*.csv"))
    if not paths:
        raise SystemExit("Nenhum VRA_*.csv em data/raw/. Execute baixar_amostra.py primeiro.")
    frames = [transform(read_vra(path), path.name) for path in paths]
    result = pd.concat(frames, ignore_index=True)
    output = root / args.saida
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, encoding="utf-8")
    print(f"Arquivo: {output}")
    print(f"Linhas: {len(result)}")
    print(f"Realizados: {int(result['realizado'].sum())}")
    print(f"Cancelados: {int(result['cancelado'].sum())}")
    print(f"Atrasos de chegada >= 15 min: {int(result['atraso_chegada_15m'].fillna(False).sum())}")


if __name__ == "__main__":
    main()
