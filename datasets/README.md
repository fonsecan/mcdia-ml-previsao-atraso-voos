# Datasets versionados

Cada diretório `dataset-NNNNNN` define uma versão imutável dos dados usados pela modelagem. A definição (`dataset.yaml`) e a receita (`receita.sh`) são versionadas. Os CSVs, os arquivos brutos e o `manifest.json` são gerados localmente; depois de conferidos, o manifesto deve ser versionado junto com a run que o utiliza.

O manifesto registra URLs, SHA-256 e tamanho dos arquivos VRA, os hashes dos artefatos derivados, o commit do código e as versões de Python e pandas. Portanto, repetir uma receita só é considerado a reprodução do mesmo dataset quando todos os hashes de entrada coincidem. Caso a ANAC tenha republicado algum CSV, crie um novo diretório numerado: nunca substitua o conteúdo de um dataset já registrado.

Para materializar a primeira versão:

```bash
python scripts/gerenciar_datasets.py materializar dataset-000001
```

O comando baixa os CSVs em `datasets/dataset-000001/raw/`, gera a auditoria, o dataset derivado e a base de modelagem. Para criar a divisão temporal correspondente, use o diretório em [`splits/`](../splits/README.md).
