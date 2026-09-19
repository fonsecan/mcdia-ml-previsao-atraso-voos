"""Baixa um pequeno recorte mensal do VRA da ANAC."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.request import urlopen


BASE = "https://siros.anac.gov.br/siros/registros/diversos/vra"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano", type=int, default=2025)
    parser.add_argument("--meses", type=int, default=1)
    parser.add_argument("--output-dir", default="data/raw")
    parser.add_argument("--metadata-output", default="data/amostra_metadata.json")
    parser.add_argument("--sobrescrever", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.meses <= 12:
        raise SystemExit("--meses deve estar entre 1 e 12.")
    root = Path(__file__).resolve().parents[1]
    raw = root / args.output_dir
    raw.mkdir(parents=True, exist_ok=True)
    files = []
    for month in range(1, args.meses + 1):
        name = f"VRA_{args.ano}_{month:02d}.csv"
        url = f"{BASE}/{args.ano}/{name}"
        target = raw / name
        if target.exists() and not args.sobrescrever:
            raise FileExistsError(
                f"Arquivo já existe: {target}. Use --sobrescrever somente para uma nova coleta."
            )
        temporary = target.with_suffix(target.suffix + ".download")
        with urlopen(url) as response, temporary.open("wb") as output:
            output.write(response.read())
        temporary.replace(target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        files.append({
            "arquivo": name, "ano": args.ano, "mes": month, "url": url,
            "bytes": target.stat().st_size, "sha256": digest,
        })
    metadata = {"fonte": BASE, "coletado_em": date.today().isoformat(), "arquivos": files}
    metadata_output = root / args.metadata_output
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
