# Qualidade do dataset derivado

O recorte de janeiro e fevereiro de 2025 gerou 168.546 linhas, das quais 162.553 são voos realizados e 5.993 cancelados. A classificação atual usa seis faixas de atraso e é criada somente depois de filtrar voos realizados com atraso de chegada calculável.

Há 10.386 linhas sem atraso calculável porque pelo menos um horário necessário está ausente. Isso inclui cancelamentos e voos realizados sem horário completo; elas não devem entrar em uma regressão de atraso contínuo sem uma regra adicional.

O atraso de chegada tem valores extremos: 51 registros excedem 24 horas, e há casos acima de 30 dias. O foco atual é a classificação ordinal em seis faixas, que preserva a ordem do atraso sem exigir previsão exata em minutos. Se testarmos regressão em minutos, devemos reportar MAE mediana, quantis, métricas com e sem truncamento pré-especificado e inspeção manual dos maiores outliers. Não aplicar um corte depois de olhar o desempenho do teste.

Os horários reais e os atrasos calculados são rótulos. Variáveis de entrada para previsão devem ser definidas em uma etapa separada, usando apenas campos disponíveis antes do voo.
