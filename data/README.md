# Dados

Os CSVs originais da ANAC ficam em `data/raw/` e não são versionados. O script `scripts/baixar_amostra.py` baixa arquivos mensais do diretório oficial e cria `data/amostra_metadata.json`. O script `scripts/auditar_amostra.py` lê os CSVs locais, detecta separador e encoding, lista colunas, valores ausentes, duplicidades e distribuições da situação do voo.

Antes de versionar qualquer CSV derivado, documentar os campos mantidos, as exclusões e a data da coleta.
