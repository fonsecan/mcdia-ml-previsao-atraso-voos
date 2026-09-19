"""Compara os modelos com validação temporal progressiva."""
from pathlib import Path
import json
import time
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, TargetEncoder

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "modelagem_faixas_atraso.csv"
OUTPUT = ROOT / "artifacts" / "resultados_validacao_progressiva.json"

CATEGORICAS = ["companhia_icao", "origem_icao", "destino_icao", "codigo_tipo_linha", "modelo_equipamento", "periodo_dia"]
NUMERICAS = ["numero_assentos", "ano", "mes", "dia_semana", "hora_prevista", "fim_de_semana"]
FEATURES = CATEGORICAS + NUMERICAS

def metricas(y_true, pred):
    return {
        "accuracy": float(accuracy_score(y_true, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, pred)),
        "macro_f1": float(f1_score(y_true, pred, average="macro")),
    }

def criar_logistica():
    pre = ColumnTransformer([
        ("categoricas", Pipeline([
            ("imputacao", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]), CATEGORICAS),
        ("numericas", SimpleImputer(strategy="median"), NUMERICAS),
    ])
    return Pipeline([
        ("preprocessamento", pre),
        ("classificador", LogisticRegression(
            max_iter=300, class_weight="balanced", solver="lbfgs"
        )),
    ])

def criar_random_forest():
    pre = Pipeline([
        ("imputacao", SimpleImputer(strategy="most_frequent")),
        ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])
    return Pipeline([
        ("preprocessamento", pre),
        ("classificador", RandomForestClassifier(
            n_estimators=100, max_depth=20, min_samples_leaf=10,
            class_weight="balanced_subsample", n_jobs=-1, random_state=42,
        )),
    ])

def criar_hgb():
    pre = ColumnTransformer([
        ("categoricas", Pipeline([
            ("imputacao", SimpleImputer(strategy="most_frequent")),
            ("target_encoding", TargetEncoder(
                target_type="multiclass", smooth=20.0, cv=5, random_state=42
            )),
        ]), CATEGORICAS),
        ("numericas", SimpleImputer(strategy="median"), NUMERICAS),
    ])
    return Pipeline([
        ("preprocessamento", pre),
        ("classificador", HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.08, max_leaf_nodes=31,
            min_samples_leaf=50, l2_regularization=1.0,
            class_weight="balanced", random_state=42,
        )),
    ])

def carregar_anterior():
    anterior = {}
    caminho = ROOT / "artifacts" / "resultados_baselines.json"
    if caminho.exists():
        d = json.loads(caminho.read_text(encoding="utf-8"))
        anterior["regressao_logistica"] = d["regressao_logistica_balanceada"]
        anterior["baseline"] = d["baseline_classe_majoritaria"]
    caminho = ROOT / "artifacts" / "resultado_random_forest.json"
    if caminho.exists():
        anterior["random_forest"] = json.loads(caminho.read_text(encoding="utf-8"))["metricas"]
    caminho = ROOT / "artifacts" / "resultado_target_encoding_hgb.json"
    if caminho.exists():
        anterior["hist_gradient_boosting"] = json.loads(caminho.read_text(encoding="utf-8"))["metricas"]
    return {nome: {k: v for k, v in valores.items() if k in ["accuracy", "balanced_accuracy", "macro_f1"]} for nome, valores in anterior.items()}

def main():
    inicio = time.time()
    df = pd.read_csv(INPUT, low_memory=False)
    df["data_referencia"] = pd.to_datetime(df["data_referencia"])
    folds = [
        ("fold_1", "2024-01-01", "2024-10-01", "2025-01-01"),
        ("fold_2", "2024-01-01", "2025-01-01", "2025-04-01"),
        ("fold_3", "2024-01-01", "2025-04-01", "2025-07-01"),
    ]
    resultados = []
    for nome_fold, inicio_treino, inicio_validacao, fim_validacao in folds:
        treino = df[(df["data_referencia"] >= inicio_treino) & (df["data_referencia"] < inicio_validacao)]
        validacao = df[(df["data_referencia"] >= inicio_validacao) & (df["data_referencia"] < fim_validacao)]
        x_train, y_train = treino[FEATURES], treino["faixa_atraso"]
        x_val, y_val = validacao[FEATURES], validacao["faixa_atraso"]
        print(f"{nome_fold}: treino={len(treino)} validacao={len(validacao)}", flush=True)
        modelos = {
            "baseline": DummyClassifier(strategy="most_frequent"),
            "regressao_logistica": criar_logistica(),
            "random_forest": criar_random_forest(),
            "hist_gradient_boosting": criar_hgb(),
        }
        for nome, modelo in modelos.items():
            t = time.time()
            modelo.fit(x_train, y_train)
            pred = modelo.predict(x_val)
            m = metricas(y_val, pred)
            resultados.append({"periodo": nome_fold, "tipo": "validacao", "modelo": nome, **m})
            print(f"  {nome}: macro_f1={m['macro_f1']:.4f} ({time.time()-t:.1f}s)", flush=True)
    treino = df[df["data_referencia"] < "2025-07-01"]
    teste = df[df["data_referencia"] >= "2025-07-01"]
    x_train, y_train = treino[FEATURES], treino["faixa_atraso"]
    x_test, y_test = teste[FEATURES], teste["faixa_atraso"]
    print(f"teste_final: treino={len(treino)} teste={len(teste)}", flush=True)
    for nome, modelo in {
        "baseline": DummyClassifier(strategy="most_frequent"),
        "regressao_logistica": criar_logistica(),
        "random_forest": criar_random_forest(),
        "hist_gradient_boosting": criar_hgb(),
    }.items():
        t = time.time()
        modelo.fit(x_train, y_train)
        pred = modelo.predict(x_test)
        m = metricas(y_test, pred)
        resultados.append({"periodo": "teste_jul_dez_2025", "tipo": "teste_final", "modelo": nome, **m})
        print(f"  {nome}: macro_f1={m['macro_f1']:.4f} ({time.time()-t:.1f}s)", flush=True)
    saida = {
        "janela": "2024-01 a 2025-12",
        "folds": resultados,
        "divisao_anterior_teste_out_dez_2025": carregar_anterior(),
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultado salvo em {OUTPUT}; tempo total={time.time()-inicio:.1f}s")

if __name__ == "__main__":
    main()
