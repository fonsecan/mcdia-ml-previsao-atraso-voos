# MCDIA ML — Previsão de atraso de voos

POC de exploração de dados públicos da Agência Nacional de Aviação Civil (ANAC) para investigar se é possível prever, com antecedência definida, atrasos e cancelamentos de etapas de voos regulares.

**ATENÇÃO — abra o _Anaconda Prompt_ antes de executar qualquer comando deste README.**

O fluxo documentado foi preparado para o Anaconda Prompt. Não execute estes comandos no PowerShell comum ou no Prompt de Comando.

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

**Abra o Anaconda Prompt pelo menu Iniciar. Não use o PowerShell comum.** Execute cada bloco somente depois que o bloco anterior terminar.

Se o projeto ainda não estiver no computador, clone-o uma vez:

```powershell
git clone https://github.com/fonsecan/mcdia-ml-previsao-atraso-voos.git
```

Entre na pasta do projeto:

```powershell
cd mcdia-ml-previsao-atraso-voos
```

Na primeira execução, crie o ambiente. Este comando é interativo: quando o Conda perguntar se deseja prosseguir, digite `y` e pressione Enter. Aguarde a conclusão antes de continuar:

```powershell
conda create --name mcdia-ml-voos python=3.11
```

Ative o ambiente:

```powershell
conda activate mcdia-ml-voos
```

Com o ambiente ativo, instale as dependências. Este bloco pode ser copiado e executado de uma vez:

```powershell
python -m pip install -r requirements.txt
```

Baixe dois meses, audite os arquivos e gere o CSV derivado. Este bloco pode ser copiado e executado de uma vez:

```powershell
python scripts\baixar_amostra.py --ano 2025 --meses 2
python scripts\auditar_amostra_v2.py
python scripts\preparar_dados_v2.py
```

Abra o JupyterLab em um comando separado:

```powershell
jupyter lab
```

Os scripts registram a URL, a data da coleta e as estatísticas básicas. Eles não alteram os CSVs originais.
## Desafios já identificados

- Os CSVs da ANAC são UTF-8 válido. A primeira aparência de `latin1` foi causada pela exibição de acentos pelo terminal Windows, não pela codificação do arquivo.
- O VRA é uma base mensal consolidada e pode ser revisado depois da publicação; cada coleta registra URL, data e tamanho do arquivo.
- Em janeiro de 2025 houve 89.616 registros: 86.376 realizados e 3.240 cancelados. Em fevereiro foram 78.930: 76.177 realizados e 2.753 cancelados.
- Cancelamentos devem ser tratados separadamente de atraso de chegada. Horários reais e situação do voo constroem o alvo, mas não podem entrar nas variáveis preditoras.
- A auditoria encontrou registros sem horários previstos e realizados; o recorte válido do alvo precisa ser documentado antes do treinamento.

Detalhes: [`docs/01-desafios-auditoria.md`](docs/01-desafios-auditoria.md).

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
git clone https://github.com/fonsecan/mcdia-ml-previsao-atraso-voos.git
```

3. Entre na pasta do projeto:

```powershell
cd mcdia-ml-previsao-atraso-voos
```

4. Crie e ative o ambiente, apenas na primeira vez:

```powershell
conda create --name mcdia-ml-voos python=3.11
conda activate mcdia-ml-voos
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
8. No canto superior direito, selecione o kernel do ambiente `mcdia-ml-voos`. Se ele não aparecer, execute no Anaconda Prompt:

```powershell
python -m ipykernel install --user --name mcdia-ml-voos --display-name "Python (mcdia-ml-voos)"
```

9. Execute as células na ordem com `Shift + Enter` ou use **Run → Run All Cells**.

### Opção gráfica: Anaconda Navigator

1. Abra o **Anaconda Navigator**.
2. Na aba **Environments**, crie ou selecione o ambiente `mcdia-ml-voos` com Python 3.11.
3. Instale as dependências listadas em `requirements.txt` no terminal do ambiente ou pelo botão de instalação.
4. Na aba **Home**, selecione o ambiente `mcdia-ml-voos` e clique em **Launch** no JupyterLab.
5. No JupyterLab, navegue até `notebooks`.
6. Abra `00_entendimento_do_dataset.ipynb` e confirme o kernel `Python (mcdia-ml-voos)`.

É importante abrir o JupyterLab na raiz a raiz do projeto ou gerar a base antes de abrir o notebook. O notebook procura o diretório `data` subindo a partir da pasta de trabalho.

### Problemas comuns

- **`conda` não é reconhecido:** use o Anaconda Prompt, não o PowerShell comum.
- **`python` abre a Microsoft Store:** use o Anaconda Prompt e confirme `conda activate mcdia-ml-voos`.
- **CSV não encontrado:** execute `python scripts\\preparar_dados_v2.py` na raiz do projeto antes de abrir o notebook.
- **Kernel não aparece:** execute o comando `ipykernel install` acima e reinicie o JupyterLab.
- **Acentos aparecem quebrados no terminal:** o CSV é UTF-8; o problema é apenas a codificação de exibição do terminal.







