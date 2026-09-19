# Dataset derivado

O script `scripts/preparar_dados.py` lê todos os `VRA_*.csv` em `data/raw/` e gera `data/voos_vra_derivados.csv` em UTF-8.

Cada linha continua representando uma etapa de voo. O arquivo contém os campos de identificação, origem, destino, horários previstos e realizados, situações operacionais e os indicadores intermediários:

- `cancelado`: voo com situação `CANCELADO`;
- `realizado`: voo com situação `REALIZADO`;
- `atraso_partida_min` e `atraso_chegada_min`: diferença entre horário real e previsto, em minutos;

Para voos não realizados, os atrasos em minutos ficam ausentes. Horários reais e os atrasos calculados são rótulos de avaliação, não variáveis de entrada do modelo. A coluna `faixa_atraso` é criada posteriormente na base de modelagem por `scripts/preparar_modelagem.py`.
