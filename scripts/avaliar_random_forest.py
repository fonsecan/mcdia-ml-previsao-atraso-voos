"""Avalia Random Forest com divisão temporal e codificação ordinal."""
from pathlib import Path
import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "modelagem_faixas_atraso.csv"
OUTPUT = ROOT / "artifacts" / "resultado_random_forest.json"

categoricas = ["companhia_icao", "origem_icao", "destino_icao", "codigo_tipo_linha", "modelo_equipamento", "periodo_dia"]
numericas = ["numero_assentos", "ano", "mes", "dia_semana", "hora_prevista", "fim_de_semana"]
features = categoricas + numericas

def main():
    df = pd.read_csv(INPUT, low_memory=False)
    df["data_referencia"] = pd.to_datetime(df["data_referencia"])
    treino = df[df["data_referencia"] < "2025-07-01"]
    teste = df[df["data_referencia"] >= "2025-10-01"]
    x_treino, y_treino = treino[features], treino["faixa_atraso"]
    x_teste, y_teste = teste[features], teste["faixa_atraso"]

    preprocessador = Pipeline([
        ("imputacao", SimpleImputer(strategy="most_frequent")),
        ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])
    modelo = Pipeline([
        ("preprocessamento", preprocessador),
        ("classificador", RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_leaf=10,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42,
        )),
    ])
    modelo.fit(x_treino, y_treino)
    pred = modelo.predict(x_teste)
    resultado = {
        "treino_linhas": int(len(treino)),
        "teste_linhas": int(len(teste)),
        "metricas": {
            "accuracy": accuracy_score(y_teste, pred),
            "balanced_accuracy": balanced_accuracy_score(y_teste, pred),
            "macro_f1": f1_score(y_teste, pred, average="macro"),
            "por_classe": classification_report(y_teste, pred, output_dict=True, zero_division=0),
        },
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print({k: round(resultado["metricas"][k], 4) for k in ["accuracy", "balanced_accuracy", "macro_f1"]})
    print(classification_report(y_teste, pred, zero_division=0))
    print(f"Resultado salvo em {OUTPUT}")

if __name__ == "__main__":
    main()
