# Dados

Os caminhos em `data/` existem para exploração local e compatibilidade com os primeiros notebooks. Para datasets usados por runs, use `datasets/dataset-NNNNNN/`: cada versão registra fontes, hashes, transformações e artefatos derivados. Veja [`datasets/README.md`](../datasets/README.md).

Os CSVs originais da ANAC ficam em `data/raw/` e não são versionados. O script `scripts/baixar_amostra.py` aceita `--output-dir` e calcula SHA-256 para cada download. O script `scripts/auditar_amostra.py` lê os CSVs locais, detecta separador e encoding, lista colunas, valores ausentes, duplicidades e distribuições da situação do voo.

Antes de versionar qualquer CSV derivado, documentar os campos mantidos, as exclusões e a data da coleta.
