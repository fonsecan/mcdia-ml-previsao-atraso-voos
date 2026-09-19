# Runs de treinamento

Cada pasta numerada representa **um modelo treinado e avaliado em uma janela temporal**. O notebook específico da pasta é gerado a partir do template notebooks/templates/modelagem_run.ipynb. O número é sequencial e não deve ser reutilizado. A definição fica em `run.yaml` antes da execução; métricas e outros arquivos são gerados depois.

## Identidade de quem executou

`executado_por.github_login` identifica o login autenticado no GitHub. `executado_por.executor` distingue execução manual de execução pelo Codex. O login identifica a conta responsável pelo ambiente; não afirma que o usuário treinou o modelo manualmente.

## Arquivos

| Arquivo | Função |
|---|---|
| `run.yaml` | Configuração criada antes da execução: referências a dataset e divisão, alvo, variáveis, algoritmo e parâmetros. |
| `run.effective.yaml` | Cópia congelada da configuração efetivamente executada; existe apenas nas novas runs executadas pelo gerenciador. |
| `manifest.json` | Estado, horários, commit do código, hashes e contagens. |
| `metrics.json` | Acurácia, balanced accuracy e macro-F1. |
| `result.json` | Resumo plano e autocontido para comparação: dataset, divisão, modelo, métricas, tamanhos e duração. |
| `classification_report.json` | Precisão, recall e F1 por faixa nas novas runs. |
| `confusion_matrix.csv` | Erros entre as seis faixas nas novas runs. |
| `summary.md` | Resumo legível do resultado. |
| `run.ipynb` | Notebook gerado a partir do template para reproduzir aquela configuração. |
| `execution.log` | Avisos e erros de novas runs; arquivo local, ignorado pelo Git. |

O dataset grande, a atribuição de partições, modelos serializados e previsões individuais não são versionados. `run.yaml`, manifestos, métricas e resumos pequenos são versionados para permitir a leitura no GitHub. Uma pasta iniciada não é reutilizada: uma repetição recebe outro número.

O comando abaixo recria `result.json` para as runs reproduzíveis ativas e os catálogos comparativos `runs/catalogo.json` e `runs/catalogo.csv`:

```powershell
python scripts\gerenciar_runs.py gerar-catalogo
```

Antes de criar uma run, materialize e verifique o dataset e a divisão referenciados. O executor confere o SHA-256 do CSV, do manifesto do dataset, do manifesto do split e da atribuição de partições. Veja [`datasets/README.md`](../datasets/README.md) e [`splits/README.md`](../splits/README.md).

## Histórico legado

As 16 runs importadas anteriormente foram preservadas em [`legacy/validacao_progressiva_2024_2025/`](legacy/validacao_progressiva_2024_2025/). Elas servem somente para consulta e não participam da numeração, do catálogo ou das comparações das novas execuções reproduzíveis.

## Criar e executar uma nova run

Abra o **Anaconda Prompt**, ative o ambiente `mcdia-ml-voos` e materialize o dataset e o split definidos em `run.yaml` conforme o README principal. O `gh` deve estar autenticado para preencher automaticamente o login GitHub. Também é possível informar `--github-login` explicitamente.

Crie uma definição a partir do exemplo:

```powershell
python scripts\gerenciar_runs.py criar runs\exemplos\run.yaml
```

O comando informa o número criado. Como a sequência ativa foi reiniciada, a primeira run reproduzível será `000001`. Revise o respectivo `run.yaml` e execute a pasta criada:

```powershell
python scripts\gerenciar_runs.py executar runs\000001
```

O executor confere se o login autenticado no `gh` corresponde ao `run.yaml`, congela a definição, confere o dataset e split registrados, registra o commit do código, treina com as partições congeladas, avalia as seis classes e escreve os artefatos. A configuração de exemplo usa a primeira janela e Random Forest; para usar outra janela, crie uma nova divisão versionada em `splits/`.

As datas `*_fim_exclusivo` não entram no intervalo. A separação de treino e avaliação usa `data_referencia`, mas essa coluna não é entrada do modelo. O alvo vem de `faixa_atraso`; horários reais e atrasos observados não entram nas variáveis explicativas.
