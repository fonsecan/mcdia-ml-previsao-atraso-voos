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

## Desafios já identificados

- Os CSVs da ANAC são UTF-8 válido. A primeira aparência de `latin1` foi causada pela exibição de acentos pelo terminal Windows, não pela codificação do arquivo.
- O VRA é uma base mensal consolidada e pode ser revisado depois da publicação; cada coleta registra URL, data e tamanho do arquivo.
- Em janeiro de 2025 houve 89.616 registros: 86.376 realizados e 3.240 cancelados. Em fevereiro foram 78.930: 76.177 realizados e 2.753 cancelados.
- Cancelamentos devem ser tratados separadamente de atraso de chegada. Horários reais e situação do voo constroem o alvo, mas não podem entrar nas variáveis preditoras.
- A auditoria encontrou registros sem horários previstos e realizados; o recorte válido do alvo precisa ser documentado antes do treinamento.

Detalhes: [`docs/01-desafios-auditoria.md`](docs/01-desafios-auditoria.md) e [`docs/02-correcao-codificacao.md`](docs/02-correcao-codificacao.md).

## Dataset derivado inicial

Com janeiro e fevereiro de 2025, `scripts/preparar_dados_v2.py` gerou `data/voos_vra_derivados.csv` com 168.546 linhas, 162.553 voos realizados e 5.993 cancelados. O indicador `atraso_chegada_15m` é verdadeiro em 28.147 linhas.

Atrasos em minutos possuem outliers importantes: 51 registros excedem 24 horas. Por isso, o primeiro modelo deve usar o alvo binário de atraso de chegada, deixando a regressão em minutos para uma etapa posterior com regras de outlier documentadas. Os detalhes estão em [`docs/04-qualidade-dataset-derivado.md`](docs/04-qualidade-dataset-derivado.md).

### Achado: outliers extremos de atraso

Na amostra derivada de janeiro e fevereiro de 2025, 51 voos têm `atraso_chegada_min` superior a 24 horas. Há pelo menos um registro acima de 30 dias: a chegada prevista em 03/01/2025 aparece como realizada em 03/02/2025. A situação operacional também está classificada como `Atraso > 240`.

Esse achado pode representar uma alteração operacional real, uma remarcação registrada na mesma etapa ou um problema de qualidade/integração dos dados. Não devemos removê-lo automaticamente. O alvo inicial será `atraso_chegada_15m`, que é robusto a esse valor extremo; uma futura regressão em minutos deverá comparar métricas com e sem esses casos, depois de definir uma regra de tratamento antes do teste.

## Abrir o notebook no Windows com Anaconda e JupyterLab

### Opção recomendada: Anaconda Prompt

1. Abra o **Anaconda Prompt** pelo menu Iniciar.
2. Clone o projeto, caso ele ainda não esteja no computador:

```powershell
git clone https://github.com/fonsecan/mcdia-ml-previsao-atraso-voos.git C:\mcdia\mcdia-ml-previsao-atraso-voos
```

3. Entre na pasta do projeto:

```powershell
cd C:\mcdia\mcdia-ml-previsao-atraso-voos
```

4. Crie e ative o ambiente, apenas na primeira vez:

```powershell
conda create --name mcdia-ml python=3.11
conda activate mcdia-ml
python -m pip install -r requirements.txt
```

5. Baixe a amostra e gere o CSV derivado:

```powershell
python scripts\baixar_amostra.py --ano 2025 --meses 2
python scripts\auditar_amostra_v2.py
python scripts\preparar_dados_v2.py
```

6. Abra o JupyterLab a partir da raiz do projeto:

```powershell
jupyter lab
```

7. No navegador, abra `notebooks\00_entendimento_do_dataset.ipynb`.
8. No canto superior direito, selecione o kernel do ambiente `mcdia-ml`. Se ele não aparecer, execute no Anaconda Prompt:

```powershell
python -m ipykernel install --user --name mcdia-ml --display-name "Python (mcdia-ml)"
```

9. Execute as células na ordem com `Shift + Enter` ou use **Run → Run All Cells**.

### Opção gráfica: Anaconda Navigator

1. Abra o **Anaconda Navigator**.
2. Na aba **Environments**, crie ou selecione o ambiente `mcdia-ml` com Python 3.11.
3. Instale as dependências listadas em `requirements.txt` no terminal do ambiente ou pelo botão de instalação.
4. Na aba **Home**, selecione o ambiente `mcdia-ml` e clique em **Launch** no JupyterLab.
5. No JupyterLab, navegue até `C:\mcdia\mcdia-ml-previsao-atraso-voos\notebooks`.
6. Abra `00_entendimento_do_dataset.ipynb` e confirme o kernel `Python (mcdia-ml)`.

É importante abrir o JupyterLab na raiz `C:\mcdia\mcdia-ml-previsao-atraso-voos` ou gerar a base antes de abrir o notebook. O notebook procura o diretório `data` subindo a partir da pasta de trabalho.

### Problemas comuns

- **`conda` não é reconhecido:** use o Anaconda Prompt, não o PowerShell comum.
- **`python` abre a Microsoft Store:** use o Anaconda Prompt e confirme `conda activate mcdia-ml`.
- **CSV não encontrado:** execute `python scripts\\preparar_dados_v2.py` na raiz do projeto antes de abrir o notebook.
- **Kernel não aparece:** execute o comando `ipykernel install` acima e reinicie o JupyterLab.
- **Acentos aparecem quebrados no terminal:** o CSV é UTF-8; o problema é apenas a codificação de exibição do terminal.
