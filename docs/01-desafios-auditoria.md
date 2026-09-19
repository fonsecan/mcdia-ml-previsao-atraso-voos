# Desafios identificados na auditoria

## Codificação

Os CSVs da ANAC não devem ser tratados automaticamente como UTF-8. O arquivo `VRA_2025_01.csv` foi lido corretamente com `latin1`; forçar UTF-8 produziu mojibake nos nomes de colunas e nos valores textuais. O auditor v2 testa UTF-8, CP1252 e latin1 e escolhe a codificação com menos caracteres de substituição.

## Cobertura do alvo

Em janeiro de 2025 houve 89.616 registros: 86.376 realizados e 3.240 cancelados. Havia 2.253 registros sem horário previsto e 3.240 sem horário real. Portanto, o alvo de atraso de chegada deve ser calculado somente para voos realizados com horários previstos e reais válidos; cancelamento deve ser tratado separadamente.

## Ausência e possível vazamento

Horários reais, situação do voo e justificativa são informações posteriores ao evento. Eles podem construir o alvo, mas não podem entrar nas variáveis preditoras. Ainda é necessário confirmar quando o horário previsto foi disponibilizado e se o VRA histórico preserva revisões.

## Revisões e reprodutibilidade

O VRA é publicado mensalmente e os arquivos podem ser atualizados. Cada coleta deve registrar URL, data, tamanho e hash do arquivo. Os arquivos brutos permanecem em `data/raw/` e não são versionados.
