"""Materializa e verifica versões imutáveis de dataset.

Uso: python scripts/gerenciar_datasets.py {materializar,verificar} dataset-000001
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
SCRIPTS = ROOT / "scripts"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_commit() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, encoding="utf-8",
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def dataset_folder(dataset_id: str) -> Path:
    if not dataset_id.startswith("dataset-") or not dataset_id.removeprefix("dataset-").isdigit():
        raise ValueError("O dataset deve ter o formato dataset-NNNNNN.")
    folder = DATASETS / dataset_id
    if not (folder / "dataset.yaml").exists():
        raise FileNotFoundError(f"Definição não encontrada: {folder / 'dataset.yaml'}")
    return folder


def load_definition(folder: Path) -> dict:
    definition = yaml.safe_load((folder / "dataset.yaml").read_text(encoding="utf-8"))
    if definition.get("schema_version") != 1 or definition.get("id") != folder.name:
        raise ValueError("dataset.yaml inválido ou incompatível com o nome da pasta.")
    if not definition.get("coletas"):
        raise ValueError("dataset.yaml deve informar ao menos uma coleta.")
    for collection in definition["coletas"]:
        if not isinstance(collection.get("ano"), int) or not 1 <= collection.get("meses", 0) <= 12:
            raise ValueError("Cada coleta deve informar ano e meses entre 1 e 12.")
    return definition


def run(command: list[str], command_log: Path) -> None:
    rendered = shlex.join(command)
    started = utc_now()
    print("+", rendered)
    with command_log.open("a", encoding="utf-8") as stream:
        stream.write(f"[{started}] START {rendered}\n")
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as error:
        with command_log.open("a", encoding="utf-8") as stream:
            stream.write(f"[{utc_now()}] FAIL returncode={error.returncode} {rendered}\n")
        raise
    with command_log.open("a", encoding="utf-8") as stream:
        stream.write(f"[{utc_now()}] OK {rendered}\n")


def files_in_raw(raw: Path, definition: dict) -> list[dict]:
    base_url = definition["fonte"]["base_url"].rstrip("/")
    records = []
    for collection in definition["coletas"]:
        year = collection["ano"]
        for month in range(1, collection["meses"] + 1):
            name = f"VRA_{year}_{month:02d}.csv"
            path = raw / name
            if not path.exists():
                raise FileNotFoundError(f"Coleta incompleta: {path}")
            records.append({
                "arquivo": name,
                "ano": year,
                "mes": month,
                "url": f"{base_url}/{year}/{name}",
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    return records


def materialize(dataset_id: str) -> None:
    folder = dataset_folder(dataset_id)
    definition = load_definition(folder)
    manifest_path = folder / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(
            f"{manifest_path} já existe. Datasets materializados são imutáveis; crie uma nova versão."
        )
    artifacts = definition["artefatos"]
    raw = folder / artifacts["bruto"]
    command_log = folder / "commands.log"
    command_log.write_text(
        f"# Comandos executados para materializar {dataset_id}\n"
        f"[{utc_now()}] START {shlex.join([sys.executable, *sys.argv])}\n",
        encoding="utf-8",
    )
    raw.mkdir(parents=True, exist_ok=True)
    for collection in definition["coletas"]:
        run([
            sys.executable, "scripts/baixar_amostra.py", "--ano", str(collection["ano"]),
            "--meses", str(collection["meses"]), "--output-dir",
            str(raw.relative_to(ROOT)), "--metadata-output",
            str((folder / f"download_{collection['ano']}.json").relative_to(ROOT)),
        ], command_log)
    audit = folder / artifacts["auditoria"]
    derived = folder / artifacts["derivado"]
    modeling = folder / artifacts["modelagem"]
    monthly = folder / artifacts["distribuicao_mensal"]
    run([
        sys.executable, "scripts/auditar_amostra_v2.py", "--input-dir", str(raw.relative_to(ROOT)),
        "--output", str(audit.relative_to(ROOT)),
    ], command_log)
    run([
        sys.executable, "scripts/preparar_dados_v2.py", "--input-dir", str(raw.relative_to(ROOT)),
        "--output", str(derived.relative_to(ROOT)),
    ], command_log)
    run([
        sys.executable, "scripts/preparar_modelagem.py", "--input", str(derived.relative_to(ROOT)),
        "--output", str(modeling.relative_to(ROOT)), "--monthly-output", str(monthly.relative_to(ROOT)),
    ], command_log)
    with command_log.open("a", encoding="utf-8") as stream:
        stream.write(f"[{utc_now()}] OK materialização concluída\n")
    raw_files = files_in_raw(raw, definition)
    generated = {
        name: {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for name, path in {
            "auditoria": audit, "derivado": derived, "modelagem": modeling,
            "distribuicao_mensal": monthly,
        }.items()
    }
    checksums = [f"{item['sha256']}  raw/{item['arquivo']}" for item in raw_files]
    checksums.extend(f"{item['sha256']}  {Path(item['path']).name}" for item in generated.values())
    (folder / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    write_json(manifest_path, {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "status": "materializado",
        "materializado_em_utc": utc_now(),
        "definition": "dataset.yaml",
        "definition_sha256": sha256(folder / "dataset.yaml"),
        "receita": "receita.sh",
        "receita_sha256": sha256(folder / "receita.sh"),
        "comandos": {"path": "commands.log", "sha256": sha256(command_log)},
        "code_commit": git_commit(),
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "scripts": {
            name: sha256(SCRIPTS / name)
            for name in ("baixar_amostra.py", "auditar_amostra_v2.py", "preparar_dados_v2.py", "preparar_modelagem.py")
        },
        "fontes": raw_files,
        "artefatos": generated,
    })
    print(f"Dataset {dataset_id} materializado em {folder.relative_to(ROOT)}.")


def verify(dataset_id: str) -> None:
    folder = dataset_folder(dataset_id)
    definition = load_definition(folder)
    manifest_path = folder / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Dataset não materializado: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = []
    for item in manifest["fontes"]:
        path = folder / definition["artefatos"]["bruto"] / item["arquivo"]
        if not path.exists() or sha256(path) != item["sha256"]:
            failures.append(str(path.relative_to(ROOT)))
    for item in manifest["artefatos"].values():
        path = ROOT / item["path"]
        if not path.exists() or sha256(path) != item["sha256"]:
            failures.append(item["path"])
    if sha256(folder / "dataset.yaml") != manifest.get("definition_sha256"):
        failures.append("dataset.yaml")
    if sha256(folder / "receita.sh") != manifest.get("receita_sha256"):
        failures.append("receita.sh")
    command_log = folder / manifest.get("comandos", {}).get("path", "commands.log")
    if not command_log.exists() or sha256(command_log) != manifest.get("comandos", {}).get("sha256"):
        failures.append("commands.log")
    if failures:
        raise ValueError("Hash divergente ou arquivo ausente: " + ", ".join(failures))
    print(f"Dataset {dataset_id} verificado com sucesso.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comando", choices=["materializar", "verificar"])
    parser.add_argument("dataset_id")
    args = parser.parse_args()
    if args.comando == "materializar":
        materialize(args.dataset_id)
    else:
        verify(args.dataset_id)


if __name__ == "__main__":
    main()
