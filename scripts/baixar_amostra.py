"""Baixa um pequeno recorte mensal do VRA da ANAC."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.request import urlopen


BASE = "https://siros.anac.gov.br/siros/registros/diversos/vra"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano", type=int, default=2025)
    parser.add_argument("--meses", type=int, default=1)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    raw = root / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    files = []
    for month in range(1, args.meses + 1):
        name = f"VRA_{args.ano}_{month:02d}.csv"
        url = f"{BASE}/{args.ano}/{name}"
        target = raw / name
        with urlopen(url) as response, target.open("wb") as output:
            output.write(response.read())
        files.append({"arquivo": name, "url": url, "bytes": target.stat().st_size})
    metadata = {"fonte": BASE, "coletado_em": date.today().isoformat(), "arquivos": files}
    (root / "data" / "amostra_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
