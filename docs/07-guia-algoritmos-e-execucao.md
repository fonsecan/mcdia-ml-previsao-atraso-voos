# Guia de algoritmos e execução

Este documento descreve os modelos usados no projeto, o fluxo para executar uma nova run e a forma recomendada de interpretar os resultados.

## Variável-alvo

O alvo é `faixa_atraso`, uma classificação com seis valores ordenados:

1. pontual ou antecipado (`atraso <= 0`);
2. atraso de 1 a 14 minutos;
3. atraso de 15 a 30 minutos;
4. atraso de 31 a 45 minutos;
5. atraso de 46 a 60 minutos;
6. atraso superior a 60 minutos.

Cancelamentos não entram nessa classificação. Eles devem ser analisados separadamente ou usados em um futuro problema de classificação binária.

## Algoritmos

### Baseline majoritário

Sempre prevê a faixa mais frequente no conjunto de treinamento. É a referência mínima: um modelo só é útil se superar esse comportamento em métricas que considerem todas as classes.

### Regressão logística multinomial

É um classificador linear. As variáveis categóricas são transformadas com one-hot encoding e o treinamento usa pesos balanceados entre as classes. É simples e interpretável, mas pode sofrer com a grande quantidade de categorias e apresentou avisos de não convergência em alguns experimentos.

### Random Forest

Usa várias árvores de decisão e codificação ordinal das categorias. A configuração inicial usa 100 árvores, profundidade máxima 20, `min_samples_leaf=10` e `class_weight="balanced_subsample"`. A codificação ordinal impõe números às categorias; por isso, o resultado é uma referência inicial e não uma solução definitiva para variáveis nominais.

### HistGradientBoosting com Target Encoding

As categorias são convertidas em estatísticas calculadas somente no treino. Em seguida, o classificador usa árvores construídas sequencialmente. A configuração inicial usa 200 iterações, `learning_rate=0.08`, `max_leaf_nodes=31`, `min_samples_leaf=50` e regularização `l2_regularization=1.0`, com pesos balanceados.

O Target Encoding precisa ser ajustado separadamente em cada conjunto de treino. Usar validação ou teste para calcular médias das categorias causaria vazamento de informação.

## Variáveis usadas

As variáveis explicativas representam informações disponíveis antes da realização do voo, como companhia, aeroportos, rota, equipamento, horário previsto e características do voo. `data_referencia` serve para separar os períodos, mas não entra no modelo. Horários reais, situação realizada, atraso observado e qualquer coluna derivada do resultado são excluídos para evitar vazamento.

## Métricas

A acurácia deve ser lida junto com outras métricas porque a classe pontual representa aproximadamente 62% dos voos. As métricas principais são:

- `balanced_accuracy`: média do recall das seis classes;
- `macro_f1`: média do F1 sem favorecer a classe majoritária;
- recall por faixa;
- matriz de confusão.

Um modelo pode ter acurácia menor que o baseline e ainda ser melhor se identificar atrasos raros. Os resultados agregados estão em [`05-resultados-baseline.md`](05-resultados-baseline.md) e [`06-validacao-progressiva.md`](06-validacao-progressiva.md).

## Validação temporal

A avaliação principal não usa divisão aleatória. As janelas progressivas simulam a situação de treinar com o passado e prever um período posterior:

| Fold | Treino | Validação |
|---|---|---|
| 1 | jan–set/2024 | out–dez/2024 |
| 2 | jan–dez/2024 | jan–mar/2025 |
| 3 | jan/2024–mar/2025 | abr–jun/2025 |

Depois dos folds, o modelo é treinado de janeiro de 2024 a junho de 2025 e avaliado no teste final de julho a dezembro de 2025. A divisão aleatória pode misturar padrões temporais e produzir uma estimativa otimista, portanto deve ser apenas uma análise secundária.

## Executar uma nova run

Abra o **Anaconda Prompt**. Os blocos abaixo são independentes; execute um bloco por vez e aguarde seu término.

Ative o ambiente:

```bat
conda activate mcdia-ml-voos
```

Materialize e verifique o dataset e a divisão usados pela run:

```bat
python scripts\gerenciar_datasets.py materializar dataset-000001
python scripts\gerenciar_divisoes.py materializar split-000001
python scripts\gerenciar_datasets.py verificar dataset-000001
python scripts\gerenciar_divisoes.py verificar split-000001
```

Crie uma nova definição a partir do exemplo:

```bat
python scripts\gerenciar_runs.py criar runs\exemplos\run.yaml
```

Abra a pasta numerada informada pelo comando e revise o `run.yaml`. Nele ficam o algoritmo, o período, o alvo, as variáveis e os parâmetros. Depois execute a run, substituindo `000017` pelo número criado:

```bat
python scripts\gerenciar_runs.py executar runs\000017
```

O gerenciador registra a configuração efetiva, o commit do código, os hashes do dataset e da divisão, as métricas, o relatório por classe, a matriz de confusão e um resumo em Markdown. O `gh` autenticado é usado para registrar o login GitHub do executor.

Para abrir o notebook da run:

```bat
jupyter lab
```

No JupyterLab, abra `runs/000017/run.ipynb`. O notebook é gerado a partir do mesmo `run.yaml` e permite inspecionar as etapas, as métricas e a matriz de confusão. O comando oficial de execução é o gerenciador; o notebook é um artefato de auditoria e reprodução interativa.

## Runs históricas

As runs `000001` a `000016` reconstruídas a partir do resultado agregado da validação progressiva foram preservadas em `runs/legacy/validacao_progressiva_2024_2025/`. Elas servem para consulta e não participam da sequência de runs reproduzíveis, que recomeça em `runs/000001`.

## Arquivos gerados

Em uma nova run, os arquivos pequenos versionáveis são `run.yaml`, `run.effective.yaml`, `manifest.json`, `metrics.json`, `classification_report.json`, `confusion_matrix.csv`, `summary.md` e `run.ipynb`. Logs, modelos serializados, previsões e datasets grandes permanecem locais e são ignorados pelo Git.
