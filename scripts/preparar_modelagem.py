"""Prepara dados para prever a faixa de atraso sem usar informação futura."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "voos_vra_derivados.csv"
OUTPUT = ROOT / "data" / "modelagem_faixas_atraso.csv"
MONTHLY_OUTPUT = ROOT / "data" / "distribuicao_mensal_faixas_atraso.csv"

FAIXAS = {
    0: "Pontual ou antecipado",
    1: "Atraso inferior a 15 min",
    2: "Atraso de 15 a 30 min",
    3: "Atraso superior a 30 até 45 min",
    4: "Atraso superior a 45 até 60 min",
    5: "Atraso superior a 60 min",
}

def classificar(valor: float) -> int:
    if valor <= 0:
        return 0
    if valor < 15:
        return 1
    if valor <= 30:
        return 2
    if valor <= 45:
        return 3
    if valor <= 60:
        return 4
    return 5

def main() -> None:
    columns = [
        "companhia_icao", "origem_icao", "destino_icao",
        "codigo_tipo_linha", "modelo_equipamento", "numero_assentos",
        "partida_prevista", "realizado", "atraso_chegada_min",
    ]
    df = pd.read_csv(INPUT, usecols=columns, low_memory=False)
    df["partida_prevista"] = pd.to_datetime(df["partida_prevista"], errors="coerce")
    df["realizado"] = df["realizado"].fillna(False).astype(bool)
    janela = df["partida_prevista"].between("2024-01-01", "2025-12-31 23:59:59")
    calculavel = df["realizado"] & df["partida_prevista"].notna() & df["atraso_chegada_min"].notna() & janela
    df = df.loc[calculavel].copy()
    df["faixa_atraso"] = df["atraso_chegada_min"].map(classificar).astype("int8")
    dt = df["partida_prevista"]
    df["data_referencia"] = dt.dt.strftime("%Y-%m-%d")
    df["mes_referencia"] = dt.dt.to_period("M").astype(str)
    df["ano"] = dt.dt.year.astype("int16")
    df["mes"] = dt.dt.month.astype("int8")
    df["dia_semana"] = dt.dt.dayofweek.astype("int8")
    df["hora_prevista"] = dt.dt.hour.astype("int8")
    df["fim_de_semana"] = (df["dia_semana"] >= 5).astype("int8")
    df["periodo_dia"] = pd.cut(
        df["hora_prevista"], bins=[-1, 5, 11, 17, 23],
        labels=["madrugada", "manha", "tarde", "noite"],
    ).astype("string")
    features = [
        "data_referencia", "mes_referencia", "companhia_icao",
        "origem_icao", "destino_icao", "codigo_tipo_linha",
        "modelo_equipamento", "numero_assentos", "ano", "mes",
        "dia_semana", "hora_prevista", "fim_de_semana", "periodo_dia",
        "faixa_atraso",
    ]
    modelagem = df[features].sort_values("data_referencia").reset_index(drop=True)
    modelagem.to_csv(OUTPUT, index=False, encoding="utf-8")
    monthly = (
        modelagem.groupby(["mes_referencia", "faixa_atraso"], observed=False)
        .size().rename("quantidade").reset_index()
    )
    monthly["faixa"] = monthly["faixa_atraso"].map(FAIXAS)
    monthly["percentual_no_mes"] = (
        monthly["quantidade"] /
        monthly.groupby("mes_referencia")["quantidade"].transform("sum") * 100
    )
    monthly.to_csv(MONTHLY_OUTPUT, index=False, encoding="utf-8")
    print(f"Arquivo de modelagem: {OUTPUT}")
    print(f"Linhas elegíveis: {len(modelagem)}")
    print(f"Distribuição mensal: {MONTHLY_OUTPUT}")
    print(modelagem["faixa_atraso"].value_counts().sort_index().to_string())

if __name__ == "__main__":
    main()
