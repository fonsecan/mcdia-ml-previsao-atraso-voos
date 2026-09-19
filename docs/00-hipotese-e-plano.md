# Hipótese e plano da POC

## Objetivo

Avaliar se informações conhecidas antes de uma etapa de voo permitem estimar a probabilidade de atraso ou cancelamento.

## Alvos

- `cancelado`: 1 quando a situação do voo for cancelado.
- `atraso_chegada_15m`: 1 quando o voo realizado tiver chegada pelo menos 15 minutos depois da chegada prevista.

Os alvos são mutuamente informativos, mas não devem ser confundidos: voo cancelado não tem atraso de chegada observável.

## Entradas candidatas

Companhia, aeroporto de origem, aeroporto de destino, data e hora previstas, dia da semana, mês, distância se houver fonte confiável e histórico de atraso calculado somente com observações anteriores.

Horários reais, situação do voo e qualquer agregado calculado incluindo o próprio voo ficam fora das entradas.

## Validação

Separação temporal. Começar com 2022–2023 para treino, 2024 para validação e 2025 para teste, ajustando depois da auditoria de cobertura. Comparar frequência histórica, frequência por companhia/rota e regressão logística antes de árvores ou boosting.

## Limitações

O VRA é uma base mensal consolidada e pode ser revisado. É necessário verificar a semântica e a disponibilidade histórica dos horários previstos antes de interpretar o resultado como previsão feita antes do voo. Voos sem chegada real não entram no alvo de atraso de chegada; cancelamentos são avaliados separadamente.
