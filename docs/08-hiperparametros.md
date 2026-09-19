# Busca de hiperparâmetros

Este documento descreve como testar configurações diferentes dos modelos e escolher uma configuração com menor risco de overfitting. A busca deve usar as divisões temporais de validação; o teste final permanece reservado para a avaliação da configuração escolhida.

## Onde os parâmetros ficam

Nas runs reproduzíveis, a configuração fica em `run.yaml`, no bloco `modelo.parametros`:

```yaml
modelo:
  algoritmo: random_forest
  preprocessamento: ordinal_todas_colunas_moda
  parametros:
    n_estimators: 300
    max_depth: 15
    min_samples_leaf: 5
    class_weight: balanced_subsample
    n_jobs: -1
    random_state: 42
```

Os valores iniciais usados pelo gerenciador estão em `scripts/gerenciar_runs.py`, na constante `PARAMETROS`. Cada run copia seus parâmetros para `run.effective.yaml`, preservando a configuração efetivamente executada.

Os notebooks e scripts históricos contêm configurações próprias e servem para exploração ou comparação anterior. Para resultados oficiais, use uma nova run com os parâmetros registrados no YAML.

## Fluxo recomendado

1. Definir uma grade de hiperparâmetros.
2. Treinar cada combinação nos folds temporais de validação.
3. Calcular `balanced_accuracy` e `macro_f1` em cada fold.
4. Comparar a média das métricas entre os folds.
5. Escolher a configuração sem consultar repetidamente o teste final.
6. Treinar a configuração escolhida no período completo de treino.
7. Avaliar uma única vez no teste final.
8. Registrar a configuração vencedora como uma nova run numerada.

Escolher parâmetros olhando repetidamente o resultado do teste transforma o teste em parte do treinamento e produz uma estimativa otimista do desempenho.

## Métrica de seleção

A acurácia não deve ser usada sozinha, pois a classe “pontual ou antecipado” é majoritária. A recomendação é priorizar `macro_f1`, que dá o mesmo peso a todas as faixas, e reportar também `balanced_accuracy`, que calcula a média do recall das classes.

Confira também o recall por faixa e a matriz de confusão. Um modelo com média melhor pode ainda ser ruim para a faixa de atraso de maior interesse operacional.

## Random Forest

Uma grade inicial pequena:

```python
from sklearn.model_selection import ParameterGrid
from sklearn.ensemble import RandomForestClassifier

grade_random_forest = {
    "n_estimators": [200, 400],
    "max_depth": [10, 20, None],
    "min_samples_leaf": [2, 5, 10],
    "max_features": ["sqrt", "log2"],
}

combinacoes = list(ParameterGrid(grade_random_forest))
print(len(combinacoes))  # 36
```

Os parâmetros mais importantes são `n_estimators`, `max_depth`, `min_samples_leaf` e `max_features`. Os parâmetros de desbalanceamento e reprodutibilidade podem permanecer fixos:

```python
modelo = RandomForestClassifier(
    **parametros_da_grade,
    class_weight="balanced_subsample",
    n_jobs=-1,
    random_state=42,
)
```

## HistGradientBoosting

Uma grade inicial:

```python
grade_hgb = {
    "max_iter": [200, 400],
    "learning_rate": [0.03, 0.08],
    "max_leaf_nodes": [15, 31, 63],
    "min_samples_leaf": [20, 50, 100],
    "l2_regularization": [0.1, 1.0, 10.0],
}
```

Essa grade gera 108 combinações. Como cada combinação passa pelos folds temporais, comece com uma grade menor ou use busca aleatória.

Os parâmetros controlam principalmente `max_iter`, `learning_rate`, `max_leaf_nodes`, `min_samples_leaf` e `l2_regularization`.

O modelo usa Target Encoding. Também podem ser avaliados os parâmetros do codificador:

```text
preprocessamento__categoricas__target_encoding__smooth
preprocessamento__categoricas__target_encoding__cv
```

Atualmente `smooth=20.0` e `cv=5` estão fixos no construtor. Se forem incluídos na busca, o Target Encoding deve ser ajustado somente com dados disponíveis no treino de cada fold.

## Busca com `ParameterGrid`

Uma busca explícita é simples de auditar e permite reutilizar exatamente as atribuições versionadas em `splits/`:

```python
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import ParameterGrid
from sklearn.ensemble import RandomForestClassifier

resultados = []

for parametros in ParameterGrid(grade_random_forest):
    metricas_folds = []

    for treino, validacao in folds_temporais:
        modelo = RandomForestClassifier(
            **parametros,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42,
        )
        modelo.fit(treino[features], treino["faixa_atraso"])
        predicoes = modelo.predict(validacao[features])
        metricas_folds.append({
            "balanced_accuracy": balanced_accuracy_score(
                validacao["faixa_atraso"], predicoes
            ),
            "macro_f1": f1_score(
                validacao["faixa_atraso"], predicoes, average="macro"
            ),
        })

    resultados.append({
        "parametros": parametros,
        "balanced_accuracy_media": sum(
            item["balanced_accuracy"] for item in metricas_folds
        ) / len(metricas_folds),
        "macro_f1_media": sum(
            item["macro_f1"] for item in metricas_folds
        ) / len(metricas_folds),
    })

melhor = max(resultados, key=lambda item: item["macro_f1_media"])
print(melhor)
```

Neste exemplo, `folds_temporais` deve conter os folds de validação progressiva, não o teste final. Salve todos os resultados em JSON para que a escolha seja auditável.

## Uso de `GridSearchCV`

O `GridSearchCV` pode ser usado se receber um objeto de divisão temporal explícito. Não use o `cv=5` padrão sem conferir a ordem temporal, pois uma validação que misture passado e futuro pode causar vazamento.

Para os parâmetros do classificador dentro do pipeline, use:

```python
grade = {
    "classificador__n_estimators": [200, 400],
    "classificador__max_depth": [10, 20, None],
    "classificador__min_samples_leaf": [2, 5, 10],
}
```

Para o Target Encoding dentro do pipeline:

```python
grade = {
    "classificador__max_iter": [200, 400],
    "classificador__learning_rate": [0.03, 0.08],
    "preprocessamento__categoricas__target_encoding__smooth": [10.0, 20.0, 50.0],
}
```

Mesmo usando `GridSearchCV`, a divisão precisa representar o fluxo passado → futuro. A implementação explícita com `ParameterGrid` é preferível quando as atribuições versionadas precisam ser reutilizadas exatamente.

## Custo computacional

Uma grade com 36 combinações e três folds produz 108 treinamentos. A grade de 108 combinações do HistGradientBoosting produz 324 treinamentos com os mesmos três folds. Para reduzir o custo:

- comece com uma grade pequena;
- use `n_jobs=-1` quando o algoritmo permitir;
- use busca aleatória para grades grandes;
- faça uma segunda busca mais estreita ao redor dos melhores valores;
- mantenha `random_state` fixo;
- registre duração e versão das bibliotecas.

## Transformar o vencedor em uma run

Depois de escolher os parâmetros com os folds de validação, copie-os para um novo `run.yaml`. A run deve continuar referenciando o mesmo dataset e a divisão adequada:

```yaml
modelo:
  algoritmo: hist_gradient_boosting
  preprocessamento: target_encoding_multiclasse_cv5_smooth20_mediana_numericas
  parametros:
    max_iter: 400
    learning_rate: 0.05
    max_leaf_nodes: 31
    min_samples_leaf: 50
    l2_regularization: 1.0
    class_weight: balanced
    random_state: 42
```

Depois, crie e execute uma nova run:

```bash
python scripts/gerenciar_runs.py criar runs/exemplos/run.yaml
python scripts/gerenciar_runs.py executar runs/000001
```

O número real da run deve ser o informado pelo comando de criação. Uma configuração diferente deve receber uma nova run; não sobrescreva uma run já criada ou executada.

## Próximo aprimoramento

O projeto ainda não possui um script dedicado de otimização. Uma implementação futura pode criar `scripts/otimizar_hiperparametros.py` para carregar os folds `split-000001` a `split-000003`, executar a grade ou busca aleatória, salvar `artifacts/hiperparametros_<modelo>.json`, manter o `split-000004` reservado e preparar uma run oficial com os parâmetros escolhidos.

Até esse script existir, a busca pode ser realizada em um notebook separado ou em um script experimental, salvando resultados em `artifacts/`, sem misturá-los com as runs oficiais.
