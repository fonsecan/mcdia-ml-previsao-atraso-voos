"""Baixa um pequeno recorte mensal do VRA da ANAC."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.request import urlopen


BASE = "https://siros.anac.gov.br/siros/registros/diversos/vra"


def parse_month(value: str) -> tuple[int, int]:
    try:
        year_text, month_text = value.split("-", 1)
        year, month = int(year_text), int(month_text)
    except (ValueError, AttributeError):
        raise argparse.ArgumentTypeError("o mês deve estar no formato YYYY-MM")
    if year < 1 or not 1 <= month <= 12:
        raise argparse.ArgumentTypeError("o mês deve estar no formato YYYY-MM")
    return year, month


def month_sequence(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    if start > end:
        raise SystemExit("--inicio-mes não pode ser posterior a --fim-mes.")
    year, month = start
    months = []
    while (year, month) <= end:
        months.append((year, month))
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return months


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano", type=int)
    parser.add_argument("--meses", type=int)
    parser.add_argument("--inicio-mes", type=parse_month, help="primeiro mês, no formato YYYY-MM")
    parser.add_argument("--fim-mes", type=parse_month, help="último mês inclusivo, no formato YYYY-MM")
    parser.add_argument("--output-dir", default="data/raw")
    parser.add_argument("--metadata-output", default="data/amostra_metadata.json")
    parser.add_argument("--sobrescrever", action="store_true")
    args = parser.parse_args()
    range_mode = args.inicio_mes is not None or args.fim_mes is not None
    legacy_mode = args.ano is not None or args.meses is not None
    if range_mode and legacy_mode:
        raise SystemExit("Use --inicio-mes/--fim-mes ou --ano/--meses, não os dois formatos.")
    if range_mode:
        if args.inicio_mes is None or args.fim_mes is None:
            raise SystemExit("Informe --inicio-mes e --fim-mes juntos.")
        months = month_sequence(args.inicio_mes, args.fim_mes)
        period = {
            "inicio_mes": f"{args.inicio_mes[0]:04d}-{args.inicio_mes[1]:02d}",
            "fim_mes": f"{args.fim_mes[0]:04d}-{args.fim_mes[1]:02d}",
        }
    else:
        year = args.ano if args.ano is not None else 2025
        count = args.meses if args.meses is not None else 1
        if year < 1 or not 1 <= count <= 12:
            raise SystemExit("--ano deve ser positivo e --meses deve estar entre 1 e 12.")
        months = [(year, month) for month in range(1, count + 1)]
        period = {"inicio_mes": f"{year:04d}-01", "fim_mes": f"{year:04d}-{count:02d}"}
    root = Path(__file__).resolve().parents[1]
    raw = root / args.output_dir
    raw.mkdir(parents=True, exist_ok=True)
    files = []
    for year, month in months:
        name = f"VRA_{year}_{month:02d}.csv"
        url = f"{BASE}/{year}/{name}"
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
            "arquivo": name, "ano": year, "mes": month, "url": url,
            "bytes": target.stat().st_size, "sha256": digest,
        })
    metadata = {"fonte": BASE, "coletado_em": date.today().isoformat(), "periodo": period, "arquivos": files}
    metadata_output = root / args.metadata_output
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
