# MCDIA ML — Previsão de atraso de voos

POC de exploração de dados públicos da Agência Nacional de Aviação Civil (ANAC) para investigar se é possível prever, com antecedência definida, atrasos e cancelamentos de etapas de voos regulares.

## Pergunta inicial

Um voo programado chegará com 15 minutos ou mais de atraso, ou será cancelado?

O primeiro recorte é retrospectivo: a base histórica da ANAC combina informações planejadas e realizadas. Antes de chamar o resultado de previsão operacional, devemos confirmar quais horários previstos estavam disponíveis antes da execução do voo.

## Fonte

- [Metadados do Voo Regular Ativo (VRA)](https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/voo-regular-ativo-vra/62-voo-regular-ativo-vra)
- [Arquivos CSV mensais da ANAC](https://siros.anac.gov.br/siros/registros/diversos/vra/)

O VRA contém companhia, voo, origem, destino, horários previstos e realizados e situação (realizado, cancelado ou não informado). A ANAC informa atualização mensal e arquivos organizados por ano. O mês se refere às etapas cuja decolagem estava prevista ou ocorreu naquele mês.

## Organização

- `data/raw/`: CSVs originais baixados pelo script; não versionados.
- `data/`: amostras derivadas, metadados e dicionários pequenos.
- `docs/`: hipótese, decisões e limitações.
- `notebooks/`: exploração, qualidade e primeiro modelo.
- `scripts/`: download e auditoria reproduzíveis.
- `artifacts/`: gráficos, métricas e modelos locais; não versionados.

## Primeiro passo executável

No Anaconda Prompt:

```powershell
cd C:\mcdia\mcdia-ml-previsao-atraso-voos
conda create --name mcdia-ml python=3.11
conda activate mcdia-ml
python -m pip install -r requirements.txt
python scripts/baixar_amostra.py --ano 2025 --meses 1
python scripts/auditar_amostra.py
jupyter lab
```

Os scripts registram a URL, a data de coleta e as estatísticas básicas. Eles não alteram os CSVs originais.
