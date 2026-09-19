"""Executa os baselines iniciais com divisão temporal."""
from pathlib import Path
import json
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "modelagem_faixas_atraso.csv"
OUTPUT = ROOT / "artifacts" / "resultados_baselines.json"

categoricas = ["companhia_icao", "origem_icao", "destino_icao", "codigo_tipo_linha", "modelo_equipamento", "periodo_dia"]
numericas = ["numero_assentos", "ano", "mes", "dia_semana", "hora_prevista", "fim_de_semana"]

def metricas(y_true, pred):
    return {
        "accuracy": accuracy_score(y_true, pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, pred),
        "macro_f1": f1_score(y_true, pred, average="macro"),
        "por_classe": classification_report(y_true, pred, output_dict=True, zero_division=0),
    }

def main():
    df = pd.read_csv(INPUT, low_memory=False)
    df["data_referencia"] = pd.to_datetime(df["data_referencia"])
    treino = df[df["data_referencia"] < "2025-07-01"]
    teste = df[df["data_referencia"] >= "2025-10-01"]
    x_treino, y_treino = treino[categoricas + numericas], treino["faixa_atraso"]
    x_teste, y_teste = teste[categoricas + numericas], teste["faixa_atraso"]

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(x_treino, y_treino)
    pred_baseline = baseline.predict(x_teste)

    preprocessador = ColumnTransformer([
        ("categoricas", Pipeline([
            ("imputacao", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]), categoricas),
        ("numericas", SimpleImputer(strategy="median"), numericas),
    ])
    modelo = Pipeline([
        ("preprocessamento", preprocessador),
        ("classificador", LogisticRegression(
            max_iter=300, class_weight="balanced", solver="lbfgs"
        )),
    ])
    modelo.fit(x_treino, y_treino)
    pred_modelo = modelo.predict(x_teste)

    resultado = {
        "treino_linhas": int(len(treino)),
        "teste_linhas": int(len(teste)),
        "baseline_classe_majoritaria": metricas(y_teste, pred_baseline),
        "regressao_logistica_balanceada": metricas(y_teste, pred_modelo),
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    for nome, valores in resultado.items():
        if isinstance(valores, dict) and "macro_f1" in valores:
            print(nome, {k: round(valores[k], 4) for k in ["accuracy", "balanced_accuracy", "macro_f1"]})
    print(f"Resultado salvo em {OUTPUT}")

if __name__ == "__main__":
    main()

