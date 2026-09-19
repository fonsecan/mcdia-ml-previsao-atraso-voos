"""Materializa e verifica divisões temporais versionadas.

Uso: python scripts/gerenciar_divisoes.py {materializar,verificar} split-000001
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "splits"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def split_folder(split_id: str) -> Path:
    if not split_id.startswith("split-") or not split_id.removeprefix("split-").isdigit():
        raise ValueError("A divisão deve ter o formato split-NNNNNN.")
    folder = SPLITS / split_id
    if not (folder / "split.yaml").exists():
        raise FileNotFoundError(f"Definição não encontrada: {folder / 'split.yaml'}")
    return folder


def load_definition(folder: Path) -> dict:
    definition = yaml.safe_load((folder / "split.yaml").read_text(encoding="utf-8"))
    if definition.get("schema_version") != 1 or definition.get("id") != folder.name:
        raise ValueError("split.yaml inválido ou incompatível com o nome da pasta.")
    train, evaluation = definition.get("treino", {}), definition.get("avaliacao", {})
    if not (train.get("inicio") < train.get("fim_exclusivo") <= evaluation.get("inicio") < evaluation.get("fim_exclusivo")):
        raise ValueError("Intervalos temporais inválidos ou sobrepostos.")
    return definition


def dataset_manifest(definition: dict) -> tuple[Path, dict]:
    folder = ROOT / "datasets" / definition["dataset_id"]
    manifest_path = folder / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Dataset ainda não materializado: {manifest_path}")
    return manifest_path, json.loads(manifest_path.read_text(encoding="utf-8"))


def materialize(split_id: str) -> None:
    folder = split_folder(split_id)
    definition = load_definition(folder)
    manifest_path = folder / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"{manifest_path} já existe. Divisões materializadas são imutáveis; crie uma nova versão.")
    dataset_manifest_path, dataset = dataset_manifest(definition)
    dataset_path = ROOT / definition["dataset_modelagem"]
    artifact = dataset["artefatos"].get("modelagem")
    if artifact is None or artifact["path"] != definition["dataset_modelagem"]:
        raise ValueError("O split não aponta para o artefato de modelagem registrado no dataset.")
    if not dataset_path.exists() or sha256(dataset_path) != artifact["sha256"]:
        raise ValueError("O arquivo de modelagem não coincide com o manifesto do dataset.")
    frame = pd.read_csv(dataset_path, usecols=["id_registro", "data_referencia"], low_memory=False)
    if frame["id_registro"].isna().any() or frame["id_registro"].duplicated().any():
        raise ValueError("id_registro ausente ou duplicado; não é possível congelar a divisão.")
    dates = pd.to_datetime(frame["data_referencia"], errors="raise")
    train = definition["treino"]
    evaluation = definition["avaliacao"]
    assignment = pd.Series("excluido", index=frame.index, dtype="string")
    assignment.loc[dates.between(train["inicio"], train["fim_exclusivo"], inclusive="left")] = "treino"
    assignment.loc[dates.between(evaluation["inicio"], evaluation["fim_exclusivo"], inclusive="left")] = "avaliacao"
    output = folder / "atribuicao_particoes.csv"
    result = pd.DataFrame({"id_registro": frame["id_registro"], "particao": assignment})
    result.to_csv(output, index=False, encoding="utf-8")
    counts = {key: int(value) for key, value in assignment.value_counts().sort_index().items()}
    if not counts.get("treino") or not counts.get("avaliacao"):
        raise ValueError("Treino ou avaliação sem registros.")
    if counts.get("excluido", 0):
        raise ValueError("Há registros fora das janelas do split; defina explicitamente outra versão.")
    distribution = (
        pd.read_csv(dataset_path, usecols=["id_registro", "mes_referencia", "faixa_atraso"])
        .merge(result, on="id_registro", validate="one_to_one")
        .groupby(["particao", "mes_referencia", "faixa_atraso"], observed=False)
        .size().rename("quantidade").reset_index()
    )
    distribution.to_csv(folder / "distribuicao_particoes.csv", index=False, encoding="utf-8")
    write_json(manifest_path, {
        "schema_version": 1,
        "split_id": split_id,
        "status": "materializado",
        "materializado_em_utc": utc_now(),
        "definition": "split.yaml",
        "definition_sha256": sha256(folder / "split.yaml"),
        "receita": "receita.sh",
        "receita_sha256": sha256(folder / "receita.sh"),
        "dataset_id": definition["dataset_id"],
        "dataset_manifest": str(dataset_manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "dataset_manifest_sha256": sha256(dataset_manifest_path),
        "dataset_modelagem": definition["dataset_modelagem"],
        "dataset_modelagem_sha256": artifact["sha256"],
        "atribuicao": {"path": str(output.relative_to(ROOT)), "sha256": sha256(output), "rows": int(len(result))},
        "particoes": counts,
    })
    print(f"Divisão {split_id} materializada em {folder.relative_to(ROOT)}.")


def verify(split_id: str) -> None:
    folder = split_folder(split_id)
    manifest_path = folder / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Divisão não materializada: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assignment = ROOT / manifest["atribuicao"]["path"]
    if not assignment.exists() or sha256(assignment) != manifest["atribuicao"]["sha256"]:
        raise ValueError("A atribuição de partições não coincide com o manifesto.")
    dataset_manifest_path = ROOT / manifest["dataset_manifest"]
    if not dataset_manifest_path.exists() or sha256(dataset_manifest_path) != manifest["dataset_manifest_sha256"]:
        raise ValueError("O manifesto do dataset foi alterado desde a materialização do split.")
    print(f"Divisão {split_id} verificada com sucesso.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comando", choices=["materializar", "verificar"])
    parser.add_argument("split_id")
    args = parser.parse_args()
    if args.comando == "materializar":
        materialize(args.split_id)
    else:
        verify(args.split_id)


if __name__ == "__main__":
    main()
