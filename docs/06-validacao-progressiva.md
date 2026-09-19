# Validação temporal progressiva

## Desenho

A avaliação progressiva usa três janelas de validação e um teste final:

| Janela | Treino | Validação |
|---|---|---|
| Fold 1 | jan–set/2024 | out–dez/2024 |
| Fold 2 | jan–dez/2024 | jan–mar/2025 |
| Fold 3 | jan/2024–mar/2025 | abr–jun/2025 |

Depois dos folds, os modelos são treinados em janeiro de 2024 a junho de 2025 e avaliados no teste final de julho a dezembro de 2025.

## Médias das validações progressivas

| Modelo | Acurácia média | Balanced accuracy média | Macro-F1 médio |
|---|---:|---:|---:|
| Classe majoritária | 0,6117 | 0,1667 | 0,1263 |
| Regressão logística balanceada | 0,3427 | 0,2137 | 0,1768 |
| Random Forest balanceado | 0,3895 | 0,2415 | 0,2095 |
| HistGradientBoosting + Target Encoding | 0,4109 | 0,2485 | 0,2185 |

O HistGradientBoosting teve a melhor média de balanced accuracy e macro-F1 nas validações progressivas.

## Resultado do teste final: julho–dezembro de 2025

| Modelo | Acurácia | Balanced accuracy | Macro-F1 |
|---|---:|---:|---:|
| Classe majoritária | 0,6218 | 0,1667 | 0,1278 |
| Regressão logística balanceada | 0,2367 | 0,2173 | 0,1516 |
| Random Forest balanceado | 0,3838 | 0,2510 | 0,2160 |
| HistGradientBoosting + Target Encoding | 0,3301 | 0,2532 | 0,2009 |

No teste final ampliado, o HistGradientBoosting teve a maior balanced accuracy, enquanto o Random Forest teve o maior macro-F1.

## Comparação com a divisão anterior

A divisão anterior usava teste de outubro–dezembro de 2025, enquanto o novo teste usa julho–dezembro de 2025. Portanto, os resultados não são perfeitamente comparáveis: o novo teste tem seis meses, inclui outros períodos sazonais e contém 481.628 voos, contra 239.075 na avaliação anterior.

| Modelo | Macro-F1 anterior | Macro-F1 teste progressivo | Balanced accuracy anterior | Balanced accuracy teste progressivo |
|---|---:|---:|---:|---:|
| Classe majoritária | 0,1227 | 0,1278 | 0,1667 | 0,1667 |
| Regressão logística | 0,1503 | 0,1516 | 0,2150 | 0,2173 |
| Random Forest | 0,1969 | 0,2160 | 0,2367 | 0,2510 |
| HistGradientBoosting | 0,1783 | 0,2009 | 0,2391 | 0,2532 |

O desempenho dos modelos de árvores melhorou no teste ampliado, mas isso não deve ser interpretado como ganho causado exclusivamente pela nova divisão. A composição temporal do teste também mudou.

## Interpretação

- A validação progressiva mostra que os resultados variam entre períodos.
- O baseline tem balanced accuracy igual a 1/6 porque sempre escolhe uma classe.
- Os modelos de árvores são mais promissores que a regressão logística.
- HistGradientBoosting é o melhor candidato quando priorizamos balanced accuracy.
- Random Forest é o melhor candidato quando priorizamos macro-F1.
- A regressão logística apresentou avisos de não convergência em todos os folds.
- A validação progressiva deve ser mantida como avaliação principal para simular previsão futura.

Os resultados foram gerados por scripts/avaliar_validacao_progressiva.py e salvos localmente em artifacts/resultados_validacao_progressiva.json.
