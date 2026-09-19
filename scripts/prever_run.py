"""Gera previsões usando o modelo serializado de uma run.

Uso: python scripts/prever_run.py runs/000001 entrada.csv [--saida previsoes.csv]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Pasta ativa da run, por exemplo runs/000001")
    parser.add_argument("entrada", type=Path, help="CSV com as variáveis preditoras")
    parser.add_argument("--saida", type=Path, help="CSV de previsões; padrão: <run>/predictions.csv")
    args = parser.parse_args()
    run = (ROOT / args.run).resolve()
    if run.parent != (ROOT / "runs").resolve() or not run.name.isdigit():
        raise ValueError("Informe uma run numérica ativa diretamente dentro de runs/.")
    metadata_path = run / "model_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError("Modelo ausente: esta run não possui model_metadata.json.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    model_path = run / metadata["artifact"]["path"]
    if not model_path.exists() or sha256(model_path) != metadata["artifact"]["sha256"]:
        raise ValueError("model.joblib ausente ou divergente do hash registrado.")
    schema = json.loads((run / metadata["feature_schema"]).read_text(encoding="utf-8"))
    features = [item["nome"] for item in schema["features"]]
    entrada = pd.read_csv(ROOT / args.entrada)
    missing = sorted(set(features) - set(entrada.columns))
    if missing:
        raise ValueError(f"CSV de entrada sem variáveis obrigatórias: {missing}")
    model = joblib.load(model_path)
    resultado = entrada.copy()
    prediction = model.predict(entrada[features])
    labels = {item["codigo"]: item["descricao"] for item in schema["classes"]}
    resultado["faixa_atraso_prevista"] = prediction
    resultado["faixa_atraso_descricao"] = pd.Series(prediction).map(labels).to_numpy()
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(entrada[features])
        for index, code in enumerate(model.classes_):
            resultado[f"probabilidade_faixa_{code}"] = probabilities[:, index]
    output = ROOT / args.saida if args.saida else run / "predictions.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(output, index=False, encoding="utf-8")
    print(f"Previsões geradas: {output}")


if __name__ == "__main__":
    main()
