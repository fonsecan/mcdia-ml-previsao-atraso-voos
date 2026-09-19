# Resultados iniciais dos baselines

## Configuração

A avaliação usa a base de janeiro de 2024 a dezembro de 2025, com divisão temporal:

- treino: janeiro de 2024 a junho de 2025, 1.382.556 voos;
- validação: julho a setembro de 2025, prevista no notebook;
- teste: outubro a dezembro de 2025, 239.075 voos.

As variáveis usam somente informações disponíveis até a partida prevista. O alvo possui seis faixas de atraso.

## Resultado no teste

| Modelo | Acurácia | Balanced accuracy | Macro-F1 |
|---|---:|---:|---:|
| Classe majoritária | 0,5825 | 0,1667 | 0,1227 |
| Regressão logística balanceada | 0,2071 | 0,2150 | 0,1503 |

A regressão logística balanceada reduziu a acurácia geral porque deixou de prever quase sempre a classe pontual. Em compensação, aumentou balanced accuracy e macro-F1, que são métricas mais adequadas para este problema desbalanceado.

## Desempenho por faixa

Na regressão logística balanceada, os recalls observados foram:

| Faixa | Recall |
|---|---:|
| Pontual ou antecipado | 0,217 |
| Atraso inferior a 15 min | 0,129 |
| 15 a 30 min | 0,307 |
| Superior a 30 até 45 min | 0,060 |
| Superior a 45 até 60 min | 0,248 |
| Superior a 60 min | 0,328 |

O modelo identifica melhor alguns atrasos mais graves do que a classe pontual, mas ainda confunde muitas faixas. O desempenho não é suficiente para considerar o modelo pronto.

## Limitação observada

Mesmo com 300 iterações, a regressão logística apresentou aviso de não convergência. O resultado deve ser tratado como baseline preliminar, não como comparação definitiva.

A codificação one-hot de rotas, aeroportos e equipamentos produz muitas variáveis. O próximo experimento deve testar um modelo baseado em árvores e uma estratégia ordinal ou hierárquica, mantendo a mesma divisão temporal.

O resultado foi gerado por scripts/avaliar_baselines.py e salvo localmente em artifacts/resultados_baselines.json.

## Random Forest

O Random Forest foi avaliado com codificação ordinal das variáveis categóricas, 100 árvores, profundidade máxima 20 e pesos balanceados.

| Modelo | Acurácia | Balanced accuracy | Macro-F1 |
|---|---:|---:|---:|
| Classe majoritária | 0,5825 | 0,1667 | 0,1227 |
| Regressão logística balanceada | 0,2071 | 0,2150 | 0,1503 |
| Random Forest balanceado | 0,3087 | 0,2367 | 0,1969 |

O Random Forest apresentou o melhor balanced accuracy e macro-F1 entre os modelos testados até agora. A acurácia continua abaixo do baseline majoritário porque o modelo tenta identificar as classes menos frequentes.

A codificação ordinal impõe uma ordem numérica artificial às categorias de aeroportos e companhias. Portanto, este resultado é uma referência inicial. Um próximo experimento deve avaliar uma codificação mais apropriada para categorias ou um modelo especializado em dados categóricos.

## HistGradientBoosting com Target Encoding

Neste experimento, cada categoria foi codificada usando estatísticas calculadas somente no conjunto de treino. O modelo recebeu essas variáveis numéricas e utilizou HistGradientBoostingClassifier com pesos balanceados.

| Modelo | Acurácia | Balanced accuracy | Macro-F1 |
|---|---:|---:|---:|
| Classe majoritária | 0,5825 | 0,1667 | 0,1227 |
| Regressão logística balanceada | 0,2071 | 0,2150 | 0,1503 |
| Random Forest balanceado | 0,3087 | 0,2367 | 0,1969 |
| HistGradientBoosting + Target Encoding | 0,2499 | 0,2391 | 0,1783 |

O HistGradientBoosting obteve a maior balanced accuracy até agora, mas o Random Forest manteve o maior macro-F1. Isso mostra que a escolha do modelo depende da métrica prioritária: equilíbrio do recall entre classes ou qualidade média das previsões por classe.

O Target Encoding deve ser ajustado somente no treino. Calcular essas estatísticas usando validação ou teste causaria vazamento de informação.
