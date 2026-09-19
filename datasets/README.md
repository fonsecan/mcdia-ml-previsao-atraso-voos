# Datasets versionados

Cada diretório `dataset-NNNNNN` define uma versão imutável dos dados usados pela modelagem. A definição (`dataset.yaml`) e a receita (`receita.sh`) são versionadas. Os CSVs, os arquivos brutos e o `manifest.json` são gerados localmente; depois de conferidos, o manifesto deve ser versionado junto com a run que o utiliza.

O período é definido por `inicio_mes` e `fim_mes`, no formato `YYYY-MM`, com o fim inclusivo. O materializador expande o intervalo e baixa um arquivo mensal por vez, inclusive quando o período atravessa anos:

```yaml
periodo:
  inicio_mes: "2024-01"
  fim_mes: "2026-08"
```

O manifesto registra URLs, SHA-256 e tamanho dos arquivos VRA, os hashes dos artefatos derivados, o commit do código e as versões de Python e pandas. Portanto, repetir uma receita só é considerado a reprodução do mesmo dataset quando todos os hashes de entrada coincidem. Caso a ANAC tenha republicado algum CSV, crie um novo diretório numerado: nunca substitua o conteúdo de um dataset já registrado.

## Materializar um dataset

Materializar significa executar a receita versionada e produzir os arquivos reais no disco. Antes disso, o diretório contém somente as instruções de como construir o dataset; depois, ele contém os CSVs brutos, os artefatos derivados e evidências de proveniência.

Ao materializar, o gerenciador:

1. baixa os CSVs mensais do intervalo definido em `dataset.yaml` para `raw/`;
2. registra URL, data, tamanho e SHA-256 de cada coleta;
3. audita os arquivos brutos;
4. gera o dataset derivado;
5. gera a base de modelagem, incluindo a coluna-alvo `faixa_atraso`;
6. cria `commands.log` com todos os comandos executados, horários e códigos de retorno;
7. cria `manifest.json` e `checksums.sha256` com os hashes dos dados e dos scripts usados. O manifesto também registra o hash de `commands.log`.

Para materializar a primeira versão:

```bash
python scripts/gerenciar_datasets.py materializar dataset-000001
```

O comando baixa os CSVs em `datasets/dataset-000001/raw/`, gera a auditoria, o dataset derivado e a base de modelagem. Para criar a divisão temporal correspondente, use o diretório em [`splits/`](../splits/README.md).
