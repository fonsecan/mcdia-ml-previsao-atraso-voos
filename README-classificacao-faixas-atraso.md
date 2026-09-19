# Classificação por faixas de atraso

## Pergunta de previsão

> No momento da partida prevista, em qual faixa estará o atraso da chegada?

O objetivo inicial será prever a severidade do atraso de chegada de um voo realizado. O modelo deve usar somente informações disponíveis antes do resultado do voo.

## Variável-alvo

A variável-alvo será construída a partir de:

`atraso_chegada_min = chegada_real - chegada_prevista`

As categorias são mutuamente exclusivas:

| Código | Categoria |
|---:|---|
| 0 | pontual ou atraso de 0 a 14 minutos |
| 1 | atraso de 15 a 30 minutos |
| 2 | atraso de 31 a 45 minutos |
| 3 | atraso de 46 a 60 minutos |
| 4 | atraso superior a 60 minutos |

A categoria 0 também inclui chegadas antecipadas, isto é, atrasos negativos.

## Registros utilizados

- Somente voos com `realizado = True`.
- Voos cancelados ficam fora deste alvo, pois não possuem atraso de chegada comparável.
- Voos sem horário previsto ou real de chegada não entram na distribuição.
- A regra de classificação deve ser aplicada sem arredondamentos adicionais.

## Natureza do problema

Este é um problema de **classificação ordinal**: as categorias têm uma ordem natural de severidade. Um erro entre faixas vizinhas é diferente de confundir um voo pontual com um atraso superior a 60 minutos.

Também será mantida uma versão binária para comparação:

> atraso de chegada igual ou superior a 15 minutos.

## Variáveis de entrada

A primeira versão poderá usar informações disponíveis até a partida prevista:

- companhia aérea;
- aeroporto de origem;
- aeroporto de destino;
- mês;
- dia da semana;
- hora prevista;
- tipo de linha;
- modelo de equipamento;
- quantidade de assentos.

Não devem ser usadas variáveis preenchidas depois do voo, como horário real de partida, horário real de chegada, situação da chegada ou atraso de partida observado.

## Avaliação

A distribuição das classes deve ser examinada antes do treinamento. Se alguma faixa for muito rara, serão consideradas a coleta de mais meses, pesos de classe ou a união de faixas.

Métricas previstas:

- acurácia balanceada;
- precisão, recall e F1 por classe;
- macro-F1;
- matriz de confusão;
- erro absoluto médio entre os códigos das categorias;
- weighted Cohen's kappa;
- calibração das probabilidades.

A divisão será temporal: meses mais antigos para treino, meses seguintes para validação e meses mais recentes para teste.

## Limitações

Os limites são convenções operacionais. Um voo com 30 minutos e outro com 31 minutos ficam em classes diferentes, embora sejam casos próximos. Por isso também será útil comparar a classificação com um modelo de regressão que preveja diretamente os minutos de atraso.

A classificação mostra associação e capacidade preditiva. Ela não demonstra que uma variável causou o atraso.

