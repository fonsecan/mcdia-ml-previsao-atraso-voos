"""Avalia HistGradientBoosting com Target Encoding ajustado no treino."""
from pathlib import Path
import json
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import TargetEncoder

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "modelagem_faixas_atraso.csv"
OUTPUT = ROOT / "artifacts" / "resultado_target_encoding_hgb.json"

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

    preprocessador = ColumnTransformer([
        ("categoricas", Pipeline([
            ("imputacao", SimpleImputer(strategy="most_frequent")),
            ("target_encoding", TargetEncoder(
                target_type="multiclass",
                smooth=20.0,
                cv=5,
                random_state=42,
            )),
        ]), categoricas),
        ("numericas", SimpleImputer(strategy="median"), numericas),
    ])
    modelo = Pipeline([
        ("preprocessamento", preprocessador),
        ("classificador", HistGradientBoostingClassifier(
            max_iter=200,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=50,
            l2_regularization=1.0,
            class_weight="balanced",
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
