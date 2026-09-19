# Classificação por faixas de atraso

## Pergunta de previsão

> No momento da partida prevista, em qual faixa estará o atraso da chegada?

O objetivo é prever a severidade do atraso de chegada de um voo realizado, usando somente informações disponíveis antes do resultado do voo.

## Variável-alvo

A variável é calculada por:

`atraso_chegada_min = chegada_real - chegada_prevista`

As seis categorias são mutuamente exclusivas:

| Código | Regra | Interpretação |
|---:|---|---|
| 0 | `atraso <= 0` | pontual ou chegada antecipada |
| 1 | `0 < atraso < 15` | atraso inferior a 15 minutos |
| 2 | `15 <= atraso <= 30` | atraso de 15 a 30 minutos |
| 3 | `30 < atraso <= 45` | atraso superior a 30 até 45 minutos |
| 4 | `45 < atraso <= 60` | atraso superior a 45 até 60 minutos |
| 5 | `atraso > 60` | atraso superior a 60 minutos |

Como os atrasos são armazenados com uma casa decimal, as regras matemáticas evitam ambiguidades nos limites. Por exemplo, 14,9 minutos pertence à segunda faixa e 15,0 minutos pertence à terceira.

## Registros utilizados

- Somente voos com `realizado = True`.
- Voos cancelados ficam fora deste alvo.
- Voos sem horário previsto ou real de chegada não entram na distribuição.
- Chegadas antecipadas são consideradas pontuais.

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

A distribuição das classes deve ser examinada antes do treinamento. A base de 24 meses contém exemplos suficientes para todas as faixas, mas a classe de 46 a 60 minutos é a menor.

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

Os limites são convenções operacionais. Um voo com 30,0 minutos e outro com 30,1 minutos ficam em classes diferentes, embora sejam casos próximos. Por isso também será útil comparar a classificação com um modelo de regressão que preveja diretamente os minutos de atraso.

A classificação mostra associação e capacidade preditiva. Ela não demonstra que uma variável causou o atraso.
