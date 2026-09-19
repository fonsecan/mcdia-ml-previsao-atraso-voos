# Dataset derivado

O script `scripts/preparar_dados.py` lê todos os `VRA_*.csv` em `data/raw/` e gera `data/voos_vra_derivados.csv` em UTF-8.

Cada linha continua representando uma etapa de voo. O arquivo contém os campos de identificação, origem, destino, horários previstos e realizados, situações operacionais e os alvos derivados:

- `cancelado`: voo com situação `CANCELADO`;
- `realizado`: voo com situação `REALIZADO`;
- `atraso_partida_min` e `atraso_chegada_min`: diferença entre horário real e previsto, em minutos;
- `atraso_partida_15m` e `atraso_chegada_15m`: indicadores de atraso de pelo menos 15 minutos.

Para voos não realizados, os indicadores de atraso ficam ausentes. Horários reais e esses alvos são rótulos de avaliação, não variáveis de entrada do modelo.
