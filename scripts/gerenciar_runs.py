"""Cria e executa runs reproduzíveis de modelagem.

Uso: python scripts/gerenciar_runs.py {criar,executar,gerar-catalogo} ...
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
DATASETS = ROOT / "datasets"
SPLITS = ROOT / "splits"
LEGACY = RUNS / "legacy" / "validacao_progressiva_2024_2025"
HISTORICO = LEGACY / "historico" / "validacao_progressiva_2024_2025.json"
NOTEBOOK_TEMPLATE = ROOT / "notebooks" / "templates" / "modelagem_run.ipynb"
CLASSES = list(range(6))
FAIXAS = {
    0: "Pontual ou antecipado",
    1: "Atraso inferior a 15 min",
    2: "Atraso de 15 a 30 min",
    3: "Atraso superior a 30 até 45 min",
    4: "Atraso superior a 45 até 60 min",
    5: "Atraso superior a 60 min",
}
FEATURES_CATEGORICAS = [
    "companhia_icao", "origem_icao", "destino_icao", "codigo_tipo_linha",
    "modelo_equipamento", "periodo_dia",
]
FEATURES_NUMERICAS = [
    "numero_assentos", "ano", "mes", "dia_semana", "hora_prevista", "fim_de_semana",
]
PARAMETROS = {
    "baseline": {"strategy": "most_frequent"},
    "regressao_logistica": {"max_iter": 300, "class_weight": "balanced", "solver": "lbfgs"},
    "random_forest": {
        "n_estimators": 100, "max_depth": 20, "min_samples_leaf": 10,
        "class_weight": "balanced_subsample", "n_jobs": -1, "random_state": 42,
    },
    "hist_gradient_boosting": {
        "max_iter": 200, "learning_rate": 0.08, "max_leaf_nodes": 31,
        "min_samples_leaf": 50, "l2_regularization": 1.0,
        "class_weight": "balanced", "random_state": 42,
    },
}
PREPROCESSAMENTO = {
    "baseline": "nenhum",
    "regressao_logistica": "one_hot_categoricas_mediana_numericas",
    "random_forest": "ordinal_todas_colunas_moda",
    "hist_gradient_boosting": "target_encoding_multiclasse_cv5_smooth20_mediana_numericas",
}
FOLDS = [
    ("fold_1", "split-000001", "validacao", "2024-01-01", "2024-10-01", "2025-01-01"),
    ("fold_2", "split-000002", "validacao", "2024-01-01", "2025-01-01", "2025-04-01"),
    ("fold_3", "split-000003", "validacao", "2024-01-01", "2025-04-01", "2025-07-01"),
    ("teste_jul_dez_2025", "split-000004", "teste_final", "2024-01-01", "2025-07-01", "2026-01-01"),
]
MODELOS = list(PARAMETROS)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_yaml(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def generate_notebook(folder: Path) -> None:
    """Generate a run-specific notebook from the versioned template."""
    if not NOTEBOOK_TEMPLATE.exists():
        raise FileNotFoundError(f"Template de notebook ausente: {NOTEBOOK_TEMPLATE}")
    relative_run = folder.relative_to(ROOT).as_posix()
    text = NOTEBOOK_TEMPLATE.read_text(encoding="utf-8").replace("__RUN_DIR__", relative_run)
    (folder / "run.ipynb").write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def result_record(folder: Path) -> dict:
    """Consolida os campos necessários para comparar uma run sem ler vários arquivos."""
    spec = yaml.safe_load((folder / "run.yaml").read_text(encoding="utf-8"))
    manifest_path = folder / "manifest.json"
    metrics_path = folder / "metrics.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    metrics = read_json(metrics_path) if metrics_path.exists() else {}
    split = spec["divisao"]
    return {
        "schema_version": 1,
        "run_id": folder.name,
        "status": manifest.get("status", "criada"),
        "nome": spec["nome"],
        "dataset_id": spec["dataset"]["id"],
        "split_id": split["id"],
        "split_nome": split["nome"],
        "split_papel": split["papel"],
        "modelo": spec["modelo"]["algoritmo"],
        "preprocessamento": spec["modelo"]["preprocessamento"],
        "accuracy": metrics.get("accuracy"),
        "balanced_accuracy": metrics.get("balanced_accuracy"),
        "macro_f1": metrics.get("macro_f1"),
        "treino_linhas": manifest.get("train_rows"),
        "avaliacao_linhas": manifest.get("evaluation_rows"),
        "duracao_segundos": manifest.get("duration_seconds"),
        "concluida_em_utc": manifest.get("finished_at_utc") or manifest.get("imported_at_utc"),
        "code_commit": manifest.get("code_commit_at_execution"),
        "model_sha256": manifest.get("model_artifact", {}).get("sha256"),
    }


def write_result(folder: Path) -> dict:
    result = result_record(folder)
    write_json(folder / "result.json", result)
    return result


def write_model_artifacts(folder: Path, estimator, train, spec: dict, manifest: dict) -> dict:
    """Serializa o pipeline completo e descreve a entrada necessária para inferência."""
    import joblib

    model_path = folder / "model.joblib"
    joblib.dump(estimator, model_path)
    features = [
        {
            "nome": column,
            "papel": "categorica",
            "tipo_pandas_no_treino": str(train[column].dtype),
            "aceita_nulo": bool(train[column].isna().any()),
        }
        for column in FEATURES_CATEGORICAS
    ] + [
        {
            "nome": column,
            "papel": "numerica",
            "tipo_pandas_no_treino": str(train[column].dtype),
            "aceita_nulo": bool(train[column].isna().any()),
        }
        for column in FEATURES_NUMERICAS
    ]
    schema = {
        "schema_version": 1,
        "alvo": spec["alvo"],
        "features": features,
        "classes": [{"codigo": code, "descricao": FAIXAS[code]} for code in CLASSES],
    }
    write_json(folder / "feature_schema.json", schema)
    metadata = {
        "schema_version": 1,
        "artifact": {"path": "model.joblib", "sha256": sha256(model_path)},
        "dataset_id": spec["dataset"]["id"],
        "dataset_sha256": manifest["dataset_sha256_at_execution"],
        "split_id": spec["divisao"]["id"],
        "definition_sha256": manifest["definition_sha256"],
        "modelo": spec["modelo"],
        "python_version": manifest["python_version"],
        "pandas_version": manifest["pandas_version"],
        "sklearn_version": manifest["sklearn_version"],
        "joblib_version": joblib.__version__,
        "feature_schema": "feature_schema.json",
    }
    write_json(folder / "model_metadata.json", metadata)
    return metadata["artifact"]


def generate_results_and_catalog() -> None:
    """Atualiza result.json de todas as runs e os catálogos comparativos."""
    records = []
    for folder in sorted((path for path in RUNS.iterdir() if path.is_dir() and path.name.isdigit()),
                         key=lambda path: int(path.name)):
        if (folder / "run.yaml").exists():
            records.append(write_result(folder))
    write_json(RUNS / "catalogo.json", {"schema_version": 1, "runs": records})
    columns = [
        "schema_version", "run_id", "status", "nome", "dataset_id", "split_id", "split_nome", "split_papel",
        "modelo", "preprocessamento", "accuracy", "balanced_accuracy", "macro_f1",
        "treino_linhas", "avaliacao_linhas", "duracao_segundos", "concluida_em_utc", "code_commit",
        "model_sha256",
    ]
    with (RUNS / "catalogo.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    print(f"Atualizados {len(records)} result.json e os catálogos em runs/.")


def github_login() -> str:
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True,
        encoding="utf-8", timeout=15, check=True,
    )
    login = result.stdout.strip()
    if not login:
        raise ValueError("O gh não retornou um login GitHub.")
    return login


def definition(modelo: str, fold: tuple[str, str, str, str, str], login: str,
               executor: str) -> dict:
    nome_fold, split_id, papel, treino_inicio, treino_fim, avaliacao_fim = fold
    return {
        "schema_version": 1,
        "estudo": "faixas_atraso_chegada_v1",
        "nome": f"{nome_fold}-{modelo}",
        "executado_por": {"github_login": login, "executor": executor},
        "dataset": {
            "id": "dataset-000001",
            "arquivo": "datasets/dataset-000001/modelagem_faixas_atraso.csv",
            "manifesto": "datasets/dataset-000001/manifest.json",
            "fonte": "VRA/ANAC",
            "periodo": "2024-01 a 2025-12",
        },
        "alvo": {"coluna": "faixa_atraso", "definicao": "seis_faixas_v1"},
        "divisao": {
            "id": split_id,
            "nome": nome_fold,
            "papel": papel,
            "treino_inicio": treino_inicio,
            "treino_fim_exclusivo": treino_fim,
            "avaliacao_inicio": treino_fim,
            "avaliacao_fim_exclusivo": avaliacao_fim,
        },
        "variaveis": {
            "categoricas": FEATURES_CATEGORICAS,
            "numericas": FEATURES_NUMERICAS,
        },
        "modelo": {
            "algoritmo": modelo,
            "preprocessamento": PREPROCESSAMENTO[modelo],
            "parametros": PARAMETROS[modelo],
        },
    }


def reserve_folder() -> Path:
    RUNS.mkdir(exist_ok=True)
    reservations = RUNS / ".sequence"
    reservations.mkdir(exist_ok=True)
    used = [int(p.name) for base in (RUNS, reservations)
            for p in base.iterdir() if p.is_dir() and p.name.isdigit()]
    number = max(used, default=0) + 1
    while True:
        name = f"{number:06d}"
        try:
            (reservations / name).mkdir()
            folder = RUNS / name
            folder.mkdir()
            return folder
        except FileExistsError:
            number += 1


def import_historical(login: str) -> None:
    source = ROOT / "artifacts" / "resultados_validacao_progressiva.json"
    if not source.exists():
        raise FileNotFoundError(f"Resultado histórico ausente: {source}")
    if HISTORICO.exists() or any((RUNS / f"{i:06d}").exists() for i in range(1, 17)):
        raise FileExistsError("A importação histórica já existe; nenhuma pasta foi alterada.")
    data = json.loads(source.read_text(encoding="utf-8"))
    records = data["folds"]
    expected = [(fold[0], modelo) for fold in FOLDS for modelo in MODELOS]
    actual = [(row["periodo"], row["modelo"]) for row in records]
    if actual != expected:
        raise ValueError("As 16 combinações no JSON não coincidem com o protocolo esperado.")
    HISTORICO.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, HISTORICO)
    source_hash = sha256(HISTORICO)
    for index, (fold_name, modelo) in enumerate(expected, start=1):
        row = records[index - 1]
        fold = next(item for item in FOLDS if item[0] == fold_name)
        folder = reserve_folder()
        if folder.name != f"{index:06d}":
            raise ValueError(f"Numeração inesperada: {folder.name}")
        spec = definition(modelo, fold, login, "codex")
        write_yaml(folder / "run.yaml", spec)
        generate_notebook(folder)
        write_json(folder / "manifest.json", {
            "schema_version": 1,
            "run_number": folder.name,
            "status": "importada_historicamente",
            "imported_at_utc": utc_now(),
            "executed_at_utc": None,
            "duration_seconds": None,
            "code_commit_at_execution": None,
            "dataset_sha256_at_execution": None,
            "definition_origin": "reconstruida_do_script_historico",
            "definition_source": "scripts/avaliar_validacao_progressiva.py",
            "github_login_verification": "confirmado_no_gh_na_importacao; sem_registro_da_sessao_original",
            "metrics_source": str(HISTORICO.relative_to(ROOT)).replace("\\", "/"),
            "metrics_source_sha256": source_hash,
            "missing_artifacts": [
                "run.effective.yaml", "execution.log", "confusion_matrix.csv",
                "classification_report.json",
            ],
        })
        metrics = {
            "accuracy": row["accuracy"],
            "balanced_accuracy": row["balanced_accuracy"],
            "macro_f1": row["macro_f1"],
        }
        write_json(folder / "metrics.json", metrics)
        write_result(folder)
        (folder / "summary.md").write_text(
            f"# Run {folder.name}: {modelo} / {fold_name}\n\n"
            "Resultado importado do relatório agregado da validação progressiva. "
            "A configuração foi reconstruída do script original. "
            "Horários, duração, hash do dataset e logs desta execução não foram registrados.\n\n"
            f"- Acurácia: {metrics['accuracy']:.4f}\n"
            f"- Balanced accuracy: {metrics['balanced_accuracy']:.4f}\n"
            f"- Macro-F1: {metrics['macro_f1']:.4f}\n",
            encoding="utf-8",
        )
    print("16 runs históricas importadas em runs/legacy/validacao_progressiva_2024_2025/.")


def create_from_template(template: Path, login: str, executor: str) -> None:
    spec = yaml.safe_load(template.read_text(encoding="utf-8"))
    validate_spec(spec)
    spec["executado_por"] = {"github_login": login, "executor": executor}
    folder = reserve_folder()
    write_yaml(folder / "run.yaml", spec)
    generate_notebook(folder)
    print(f"Criada {folder.relative_to(ROOT).as_posix()}/run.yaml")


def migrate_data_references() -> None:
    """Vincula runs já versionadas ao dataset e à divisão canônicos."""
    split_ids = {fold[0]: fold[1] for fold in FOLDS}
    changed = []
    for folder in sorted(path for path in RUNS.iterdir() if path.is_dir() and path.name.isdigit()):
        path = folder / "run.yaml"
        if not path.exists():
            continue
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        split_name = spec.get("divisao", {}).get("nome")
        if split_name not in split_ids:
            raise ValueError(f"Run {folder.name} tem divisão sem mapeamento: {split_name}")
        spec["dataset"] = {
            "id": "dataset-000001",
            "arquivo": "datasets/dataset-000001/modelagem_faixas_atraso.csv",
            "manifesto": "datasets/dataset-000001/manifest.json",
            "fonte": "VRA/ANAC",
            "periodo": "2024-01 a 2025-12",
        }
        spec["divisao"]["id"] = split_ids[split_name]
        write_yaml(path, spec)
        changed.append(folder.name)
    print("Runs atualizadas: " + (", ".join(changed) if changed else "nenhuma"))


def validate_spec(spec: dict) -> None:
    if spec.get("schema_version") != 1:
        raise ValueError("schema_version deve ser 1.")
    actor = spec.get("executado_por", {})
    if not actor.get("github_login") or actor.get("executor") not in {"manual", "codex"}:
        raise ValueError("executado_por deve informar login GitHub e executor.")
    model = spec.get("modelo", {}).get("algoritmo")
    if model not in MODELOS:
        raise ValueError(f"Modelo inválido: {model}")
    if spec["modelo"].get("preprocessamento") != PREPROCESSAMENTO[model]:
        raise ValueError("Pré-processamento incompatível com o modelo.")
    if spec.get("alvo", {}).get("definicao") != "seis_faixas_v1":
        raise ValueError("Definição do alvo desconhecida.")
    if spec["alvo"].get("coluna") != "faixa_atraso":
        raise ValueError("Coluna do alvo incompatível com o executor.")
    if spec.get("variaveis") != {"categoricas": FEATURES_CATEGORICAS, "numericas": FEATURES_NUMERICAS}:
        raise ValueError("Lista de variáveis diferente da versão implementada.")
    split = spec["divisao"]
    if not (split["treino_inicio"] < split["treino_fim_exclusivo"] <=
            split["avaliacao_inicio"] < split["avaliacao_fim_exclusivo"]):
        raise ValueError("Intervalos temporais inválidos ou sobrepostos.")
    dataset = spec["dataset"]
    if dataset.get("id") != "dataset-000001":
        raise ValueError("Dataset desconhecido; crie um executor compatível para outra versão.")
    if dataset.get("arquivo") != "datasets/dataset-000001/modelagem_faixas_atraso.csv":
        raise ValueError("Arquivo de entrada diferente do dataset registrado.")
    if dataset.get("manifesto") != "datasets/dataset-000001/manifest.json":
        raise ValueError("Manifesto do dataset incompatível.")
    split_id = split.get("id", "")
    if not split_id.startswith("split-") or not split_id.removeprefix("split-").isdigit():
        raise ValueError("A run deve referenciar uma divisão no formato split-NNNNNN.")


def resolve_artifacts(spec: dict) -> tuple[Path, Path, dict, dict]:
    dataset = spec["dataset"]
    dataset_manifest_path = ROOT / dataset["manifesto"]
    if not dataset_manifest_path.exists():
        raise FileNotFoundError(f"Dataset não materializado: {dataset_manifest_path}")
    dataset_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8"))
    if dataset_manifest.get("dataset_id") != dataset["id"]:
        raise ValueError("O manifesto não pertence ao dataset informado na run.")
    dataset_path = ROOT / dataset["arquivo"]
    modelagem = dataset_manifest.get("artefatos", {}).get("modelagem", {})
    if modelagem.get("path") != dataset["arquivo"] or not dataset_path.exists():
        raise ValueError("Artefato de modelagem ausente ou incompatível com o manifesto do dataset.")
    if sha256(dataset_path) != modelagem.get("sha256"):
        raise ValueError("O hash do dataset de modelagem diverge do manifesto.")
    split_id = spec["divisao"]["id"]
    split_definition_path = SPLITS / split_id / "split.yaml"
    if not split_definition_path.exists():
        raise FileNotFoundError(f"Definição da divisão ausente: {split_definition_path}")
    split_definition = yaml.safe_load(split_definition_path.read_text(encoding="utf-8"))
    split = spec["divisao"]
    if (
        split_definition.get("dataset_id") != dataset["id"]
        or split_definition.get("nome") != split.get("nome")
        or split_definition.get("papel_avaliacao") != split.get("papel")
        or split_definition.get("treino", {}).get("inicio") != split.get("treino_inicio")
        or split_definition.get("treino", {}).get("fim_exclusivo") != split.get("treino_fim_exclusivo")
        or split_definition.get("avaliacao", {}).get("inicio") != split.get("avaliacao_inicio")
        or split_definition.get("avaliacao", {}).get("fim_exclusivo") != split.get("avaliacao_fim_exclusivo")
    ):
        raise ValueError("A janela declarada na run diverge da divisão versionada.")
    split_manifest_path = SPLITS / split_id / "manifest.json"
    if not split_manifest_path.exists():
        raise FileNotFoundError(f"Divisão não materializada: {split_manifest_path}")
    split_manifest = json.loads(split_manifest_path.read_text(encoding="utf-8"))
    if split_manifest.get("split_id") != split_id or split_manifest.get("dataset_id") != dataset["id"]:
        raise ValueError("O manifesto da divisão não corresponde à run.")
    if split_manifest.get("dataset_manifest_sha256") != sha256(dataset_manifest_path):
        raise ValueError("O dataset foi alterado desde a materialização da divisão.")
    if split_manifest.get("dataset_modelagem_sha256") != modelagem.get("sha256"):
        raise ValueError("A divisão aponta para outra versão do dataset.")
    assignment_path = ROOT / split_manifest["atribuicao"]["path"]
    if not assignment_path.exists() or sha256(assignment_path) != split_manifest["atribuicao"]["sha256"]:
        raise ValueError("A atribuição de partições está ausente ou foi alterada.")
    return dataset_path, assignment_path, dataset_manifest, split_manifest


def build_model(spec: dict):
    from sklearn.compose import ColumnTransformer
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, TargetEncoder

    model = spec["modelo"]["algoritmo"]
    params = spec["modelo"]["parametros"]
    if model == "baseline":
        return DummyClassifier(**params)
    if model == "regressao_logistica":
        pre = ColumnTransformer([
            ("categoricas", Pipeline([
                ("imputacao", SimpleImputer(strategy="most_frequent")),
                ("one_hot", OneHotEncoder(handle_unknown="ignore")),
            ]), FEATURES_CATEGORICAS),
            ("numericas", SimpleImputer(strategy="median"), FEATURES_NUMERICAS),
        ])
        estimator = LogisticRegression(**params)
    elif model == "random_forest":
        pre = Pipeline([
            ("imputacao", SimpleImputer(strategy="most_frequent")),
            ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
        ])
        estimator = RandomForestClassifier(**params)
    else:
        pre = ColumnTransformer([
            ("categoricas", Pipeline([
                ("imputacao", SimpleImputer(strategy="most_frequent")),
                ("target_encoding", TargetEncoder(
                    target_type="multiclass", smooth=20.0, cv=5, random_state=42,
                )),
            ]), FEATURES_CATEGORICAS),
            ("numericas", SimpleImputer(strategy="median"), FEATURES_NUMERICAS),
        ])
        estimator = HistGradientBoostingClassifier(**params)
    return Pipeline([("preprocessamento", pre), ("classificador", estimator)])


def execute(folder: Path) -> None:
    import pandas as pd
    import sklearn
    from sklearn.metrics import (
        accuracy_score, balanced_accuracy_score, classification_report,
        confusion_matrix, f1_score,
    )

    folder = folder.resolve()
    if folder.parent != RUNS.resolve() or not folder.name.isdigit():
        raise ValueError("Informe uma pasta numerada diretamente dentro de runs/.")
    if (folder / "manifest.json").exists() or (folder / "run.lock").exists():
        raise ValueError("Esta pasta já foi executada ou importada. Crie uma nova run.")
    spec_path = folder / "run.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    validate_spec(spec)
    if spec["executado_por"]["github_login"] != github_login():
        raise ValueError("O login GitHub autenticado difere de executado_por.github_login.")
    dataset, assignment_path, dataset_manifest, split_manifest = resolve_artifacts(spec)
    dataset_hash = sha256(dataset)
    with (folder / "run.lock").open("x", encoding="utf-8") as stream:
        stream.write(utc_now() + "\n")
    effective = folder / "run.effective.yaml"
    shutil.copyfile(spec_path, effective)
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    manifest = {
        "schema_version": 1, "run_number": folder.name,
        "status": "executando", "started_at_utc": utc_now(),
        "code_commit_at_execution": commit,
        "dataset_sha256_at_execution": dataset_hash,
        "dataset_id": spec["dataset"]["id"],
        "dataset_manifest_sha256_at_execution": sha256(ROOT / spec["dataset"]["manifesto"]),
        "split_id": spec["divisao"]["id"],
        "split_manifest_sha256_at_execution": sha256(SPLITS / spec["divisao"]["id"] / "manifest.json"),
        "split_assignment_sha256_at_execution": sha256(assignment_path),
        "definition_sha256": sha256(effective),
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "sklearn_version": sklearn.__version__,
        "executor_sha256": sha256(Path(__file__)),
    }
    write_json(folder / "manifest.json", manifest)
    log = folder / "execution.log"
    start = time.monotonic()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            df = pd.read_csv(dataset, low_memory=False)
            assignment = pd.read_csv(assignment_path)
            df = df.merge(assignment, on="id_registro", how="left", validate="one_to_one")
            if df["particao"].isna().any():
                raise ValueError("Há registros do dataset sem atribuição de partição.")
            train = df[df["particao"] == "treino"]
            evaluation = df[df["particao"] == "avaliacao"]
            if train.empty or evaluation.empty:
                raise ValueError("Treino ou avaliação sem registros.")
            features = FEATURES_CATEGORICAS + FEATURES_NUMERICAS
            estimator = build_model(spec)
            estimator.fit(train[features], train["faixa_atraso"])
            predicted = estimator.predict(evaluation[features])
            actual = evaluation["faixa_atraso"]
            report = classification_report(
                actual, predicted, labels=CLASSES, output_dict=True, zero_division=0,
            )
            matrix = confusion_matrix(actual, predicted, labels=CLASSES)
            metrics = {
                "accuracy": float(accuracy_score(actual, predicted)),
                "balanced_accuracy": float(balanced_accuracy_score(actual, predicted)),
                "macro_f1": float(f1_score(actual, predicted, average="macro")),
            }
            model_artifact = write_model_artifacts(folder, estimator, train, spec, manifest)
            write_json(folder / "metrics.json", metrics)
            write_json(folder / "classification_report.json", report)
            pd.DataFrame(matrix, index=CLASSES, columns=CLASSES).to_csv(
                folder / "confusion_matrix.csv", encoding="utf-8"
            )
            warning_lines = [f"{type(item.message).__name__}: {item.message}" for item in caught]
        duration = round(time.monotonic() - start, 3)
        log.write_text(
            f"Treino: {len(train)} registros\nAvaliação: {len(evaluation)} registros\n"
            + ("\n".join(warning_lines) + "\n" if warning_lines else "Sem avisos.\n"),
            encoding="utf-8",
        )
        manifest.update(
            status="concluida", finished_at_utc=utc_now(), duration_seconds=duration,
            train_rows=int(len(train)), evaluation_rows=int(len(evaluation)),
            warnings=len(warning_lines), model_artifact=model_artifact,
        )
        write_json(folder / "manifest.json", manifest)
        write_result(folder)
        (folder / "summary.md").write_text(
            f"# Run {folder.name}: {spec['nome']}\n\n"
            f"- Treino: {len(train)} voos\n- Avaliação: {len(evaluation)} voos\n"
            f"- Acurácia: {metrics['accuracy']:.4f}\n"
            f"- Balanced accuracy: {metrics['balanced_accuracy']:.4f}\n"
            f"- Macro-F1: {metrics['macro_f1']:.4f}\n"
            f"- Duração: {duration:.1f} segundos\n"
            f"- Modelo serializado: `model.joblib` ({model_artifact['sha256']})\n",
            encoding="utf-8",
        )
        print(f"Run {folder.name} concluída: {metrics}")
    except Exception as exc:
        log.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        manifest.update(status="falhou", finished_at_utc=utc_now(), error=str(exc))
        write_json(folder / "manifest.json", manifest)
        write_result(folder)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)
    importer = sub.add_parser("importar-historico")
    importer.add_argument("--github-login", help="Login GitHub; por padrão, consultar gh api user")
    creator = sub.add_parser("criar")
    creator.add_argument("template", type=Path)
    creator.add_argument("--github-login", help="Login GitHub; por padrão, consultar gh api user")
    creator.add_argument("--executor", default="manual", choices=["manual", "codex"])
    runner = sub.add_parser("executar")
    runner.add_argument("pasta", type=Path)
    migrator = sub.add_parser("migrar-referencias-dados")
    sub.add_parser("gerar-catalogo")
    args = parser.parse_args()
    if args.comando == "importar-historico":
        import_historical(args.github_login or github_login())
    elif args.comando == "criar":
        create_from_template(args.template, args.github_login or github_login(), args.executor)
    elif args.comando == "migrar-referencias-dados":
        migrate_data_references()
    elif args.comando == "gerar-catalogo":
        generate_results_and_catalog()
    else:
        execute(args.pasta)


if __name__ == "__main__":
    main()
