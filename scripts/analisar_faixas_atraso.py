"""Calcula a distribuição das faixas de atraso de chegada."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "voos_vra_derivados.csv"
OUTPUT_CSV = ROOT / "data" / "distribuicao_faixas_atraso.csv"
OUTPUT_JSON = ROOT / "data" / "distribuicao_faixas_atraso.json"

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
    df = pd.read_csv(INPUT, usecols=["realizado", "atraso_chegada_min", "partida_prevista"])
    realizados = df[df["realizado"].fillna(False)].copy()
    realizados["partida_prevista"] = pd.to_datetime(realizados["partida_prevista"], errors="coerce")
    janela = realizados["partida_prevista"].between("2024-01-01", "2025-12-31 23:59:59")
    realizados = realizados[janela].copy()
    calculaveis = realizados["atraso_chegada_min"].notna()
    ausentes = int((~calculaveis).sum())
    atrasos = realizados.loc[calculaveis, "atraso_chegada_min"]
    classes = atrasos.map(classificar)
    nomes = {
        0: "Pontual ou antecipado",
        1: "Atraso inferior a 15 min",
        2: "Atraso de 15 a 30 min",
        3: "Atraso superior a 30 até 45 min",
        4: "Atraso superior a 45 até 60 min",
        5: "Atraso superior a 60 min",
    }
    contagem = classes.value_counts().sort_index()
    relatorio = pd.DataFrame({
        "codigo_faixa": contagem.index,
        "faixa": [nomes[c] for c in contagem.index],
        "quantidade": contagem.values,
    })
    relatorio["percentual"] = 100 * relatorio["quantidade"] / relatorio["quantidade"].sum()
    relatorio.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    resumo = {
        "linhas_totais": int(len(df)),
        "voos_realizados": int(len(realizados)),
        "voos_realizados_com_atraso_calculavel": int(len(atrasos)),
        "voos_realizados_sem_atraso_calculavel": ausentes,
        "faixas": relatorio.to_dict(orient="records"),
    }
    OUTPUT_JSON.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(relatorio.to_string(index=False))
    print(f"Realizados sem atraso calculável: {ausentes}")

if __name__ == "__main__":
    main()
