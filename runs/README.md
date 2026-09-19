# Runs de treinamento

Cada pasta numerada representa **um modelo treinado e avaliado em uma janela temporal**. O número é sequencial e não deve ser reutilizado. A definição fica em `run.yaml` antes da execução; métricas e outros arquivos são gerados depois.

## Identidade de quem executou

`executado_por.github_login` identifica o login autenticado no GitHub. `executado_por.executor` distingue execução manual de execução pelo Codex. Nas 16 runs históricas, o login `fonsecan` foi confirmado com `gh api user` na importação, e o executor foi o Codex. Não há registro do login da sessão original de treinamento. O login identifica a conta responsável pelo ambiente; não afirma que o usuário treinou o modelo manualmente.

## Arquivos

| Arquivo | Função |
|---|---|
| `run.yaml` | Configuração criada antes da execução: dataset, alvo, datas, variáveis, algoritmo e parâmetros. |
| `run.effective.yaml` | Cópia congelada da configuração efetivamente executada; existe apenas nas novas runs executadas pelo gerenciador. |
| `manifest.json` | Estado, horários, commit do código, hashes e contagens. |
| `metrics.json` | Acurácia, balanced accuracy e macro-F1. |
| `classification_report.json` | Precisão, recall e F1 por faixa nas novas runs. |
| `confusion_matrix.csv` | Erros entre as seis faixas nas novas runs. |
| `summary.md` | Resumo legível do resultado. |
| `execution.log` | Avisos e erros de novas runs; arquivo local, ignorado pelo Git. |

O dataset grande, modelos serializados e previsões individuais não são versionados. `run.yaml`, manifestos, métricas e resumos pequenos são versionados para permitir a leitura no GitHub. Uma pasta iniciada não é reutilizada: uma repetição recebe outro número.

## As 16 runs históricas

| Janela | Baseline | Regressão logística | Random Forest | HistGradientBoosting |
|---|---:|---:|---:|---:|
| Validação out–dez/2024 | `000001` | `000002` | `000003` | `000004` |
| Validação jan–mar/2025 | `000005` | `000006` | `000007` | `000008` |
| Validação abr–jun/2025 | `000009` | `000010` | `000011` | `000012` |
| Teste jul–dez/2025 | `000013` | `000014` | `000015` | `000016` |

Essas pastas foram **importadas** do resultado agregado preservado em `runs/historico/validacao_progressiva_2024_2025.json`. A configuração foi reconstruída do script original de avaliação. Não foram registrados individualmente na época: horário da execução, duração, hash do dataset, logs, relatórios por classe e matrizes de confusão. Os manifestos deixam esses campos vazios; não representam uma nova execução.

## Criar e executar uma nova run

Abra o **Anaconda Prompt**, ative o ambiente `mcdia-ml-voos` e gere `data/modelagem_faixas_atraso.csv` conforme o README principal. O `gh` deve estar autenticado para preencher automaticamente o login GitHub. Também é possível informar `--github-login` explicitamente.

Crie uma definição a partir do exemplo:

```powershell
python scripts\gerenciar_runs.py criar runs\exemplos\run.yaml
```

O comando informa o número criado. Revise o respectivo `run.yaml` e execute a pasta criada; substitua `000017` pelo número mostrado:

```powershell
python scripts\gerenciar_runs.py executar runs\000017
```

O executor confere se o login autenticado no `gh` corresponde ao `run.yaml`, congela a definição, calcula o SHA-256 do CSV local, registra o commit do código, treina com as datas definidas, avalia as seis classes e escreve os artefatos. A configuração de exemplo usa a primeira janela e Random Forest; edite modelo e datas antes de executar outra experiência.

As datas `*_fim_exclusivo` não entram no intervalo. A separação de treino e avaliação usa `data_referencia`, mas essa coluna não é entrada do modelo. O alvo vem de `faixa_atraso`; horários reais e atrasos observados não entram nas variáveis explicativas.
