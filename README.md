# MCDIA ML — Previsão de atraso de voos

POC de exploração de dados públicos da Agência Nacional de Aviação Civil (ANAC) para investigar se é possível prever, com antecedência definida, atrasos e cancelamentos de etapas de voos regulares.

**ATENÇÃO — abra o _Anaconda Prompt_ antes de executar qualquer comando deste README.**

O fluxo documentado foi preparado para o Anaconda Prompt. Não execute estes comandos no PowerShell comum ou no Prompt de Comando.

## Pergunta inicial

Em qual faixa de atraso de chegada um voo programado será classificado?

O primeiro recorte é retrospectivo: a base histórica da ANAC combina informações planejadas e realizadas. Antes de chamar o resultado de previsão operacional, devemos confirmar quais horários previstos estavam disponíveis antes da execução do voo.

O alvo atual usa seis faixas ordinais de atraso de chegada; consulte a [definição completa das categorias](README-classificacao-faixas-atraso.md).

## Fonte

- [Metadados do Voo Regular Ativo (VRA)](https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/voo-regular-ativo-vra/62-voo-regular-ativo-vra)
- [Arquivos CSV mensais da ANAC](https://siros.anac.gov.br/siros/registros/diversos/vra/)

O VRA contém companhia, voo, origem, destino, horários previstos e realizados e situação (realizado, cancelado ou não informado). A ANAC informa atualização mensal e arquivos organizados por ano. O mês se refere às etapas cuja decolagem estava prevista ou ocorreu naquele mês.

## Organização

- `data/raw/`: CSVs originais baixados pelo script; não versionados.
- `data/`: amostras derivadas, metadados e dicionários pequenos.
- `datasets/`: receitas e manifestos de versões imutáveis dos dados.
- `splits/`: receitas e manifestos das divisões de treino, validação e teste.
- `docs/`: hipótese, decisões e limitações.
- `notebooks/`: exploração, qualidade e primeiro modelo.
- `scripts/`: download e auditoria reproduzíveis.
- `artifacts/`: gráficos, métricas e modelos locais; não versionados.

## Fluxo reprodutível de datasets, divisões e runs

O fluxo oficial usa versões numeradas para impedir que uma nova publicação da ANAC altere silenciosamente um experimento já registrado.

1. Cada `datasets/dataset-NNNNNN/` contém `dataset.yaml` e `receita.sh`, que definem os CSVs de origem e as transformações. Ao materializar o dataset, o processo registra URL, data, tamanho e SHA-256 de cada arquivo bruto; também registra o hash dos CSVs derivados, as versões de Python e pandas, o commit e os hashes dos scripts usados.
2. Cada `splits/split-NNNNNN/` define uma divisão temporal de um dataset. A materialização gera `atribuicao_particoes.csv` com a partição de cada `id_registro`, sem duplicar o dataset em três CSVs. O manifesto vincula os hashes da divisão ao dataset exato.
3. Cada run referencia um `dataset-NNNNNN` e um `split-NNNNNN`. O executor só treina quando os hashes do dataset, do manifesto e da atribuição ainda coincidem.

Para preparar o conjunto inicial de 2024–2025 e as quatro janelas temporais, execute na raiz do projeto:

```bash
python scripts/gerenciar_datasets.py materializar dataset-000001
python scripts/gerenciar_divisoes.py materializar split-000001
python scripts/gerenciar_divisoes.py materializar split-000002
python scripts/gerenciar_divisoes.py materializar split-000003
python scripts/gerenciar_divisoes.py materializar split-000004
```

Antes de uma run, confira a integridade:

```bash
python scripts/gerenciar_datasets.py verificar dataset-000001
python scripts/gerenciar_divisoes.py verificar split-000004
```

Os CSVs brutos e derivados não entram no Git por serem grandes. Versione os arquivos pequenos (`dataset.yaml`, `receita.sh`, `manifest.json`, `split.yaml` e o manifesto da divisão) e armazene os CSVs materializados em local imutável e compartilhado antes de outra pessoa reproduzir uma run. Se algum hash de origem mudar, crie um novo `dataset-NNNNNN`; não sobrescreva um diretório materializado.

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
python -m pip install -r requirements.lock
```

Materialize o dataset e as divisões versionadas. Execute cada bloco separadamente:

```powershell
python scripts\gerenciar_datasets.py materializar dataset-000001
```

```powershell
python scripts\gerenciar_divisoes.py materializar split-000001
```

```powershell
python scripts\gerenciar_divisoes.py materializar split-000002
```

```powershell
python scripts\gerenciar_divisoes.py materializar split-000003
python scripts\gerenciar_divisoes.py materializar split-000004
```

Abra o JupyterLab em um comando separado:

```powershell
jupyter lab
```

Os scripts registram URL, data, tamanho e SHA-256 de cada coleta, além dos hashes dos artefatos derivados. Um dataset ou split materializado não deve ser alterado.
## Desafios já identificados

- O VRA é uma base mensal consolidada e pode ser revisado depois da publicação; cada coleta registra URL, data e tamanho do arquivo.
- Em janeiro de 2025 houve 89.616 registros: 86.376 realizados e 3.240 cancelados. Em fevereiro foram 78.930: 76.177 realizados e 2.753 cancelados.
- Cancelamentos devem ser tratados separadamente de atraso de chegada. Horários reais e situação do voo constroem o alvo, mas não podem entrar nas variáveis preditoras.
- A auditoria encontrou registros sem horários previstos e realizados; o recorte válido do alvo precisa ser documentado antes do treinamento.

Detalhes: [`docs/01-desafios-auditoria.md`](docs/01-desafios-auditoria.md).

## Dataset derivado inicial

Com janeiro de 2024 a dezembro de 2025, `scripts/preparar_dados_v2.py` gerou localmente `data/voos_vra_derivados.csv` com 1.992.832 linhas, 1.923.336 voos realizados e 69.496 cancelados. O indicador `atraso_chegada_15m` é verdadeiro em 329.739 linhas.

Atrasos em minutos possuem outliers importantes. O projeto seguirá inicialmente com classificação ordinal em seis faixas de atraso, mantendo a classificação binária como comparação. Os detalhes estão em [`README-classificacao-faixas-atraso.md`](README-classificacao-faixas-atraso.md) e [`docs/04-qualidade-dataset-derivado.md`](docs/04-qualidade-dataset-derivado.md).

### Achado: outliers extremos de atraso

Na base derivada de 24 meses, a distribuição das faixas foi calculada somente para voos realizados com atraso de chegada calculável. O relatório local está em `data/distribuicao_faixas_atraso.csv` e pode ser recriado com `python scripts\analisar_faixas_atraso.py`.

Entre os 1.864.184 voos realizados com atraso calculável, 61,96% foram pontuais ou antecipados; 20,35% tiveram atraso inferior a 15 minutos; 8,69% entre 15 e 30 minutos; 3,40% entre 30 e 45 minutos; 1,72% entre 45 e 60 minutos; e 3,88% acima de 60 minutos. Todos os voos realizados dentro da janela temporal tiveram atraso de chegada calculável; cancelados e registros fora da janela foram excluídos da modelagem.

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
python -m pip install -r requirements.lock
```

5. Materialize o dataset e as divisões versionadas:

```powershell
python scripts\gerenciar_datasets.py materializar dataset-000001
python scripts\gerenciar_divisoes.py materializar split-000001
python scripts\gerenciar_divisoes.py materializar split-000002
python scripts\gerenciar_divisoes.py materializar split-000003
python scripts\gerenciar_divisoes.py materializar split-000004
```

6. Abra o JupyterLab a partir da raiz do projeto:

```powershell
jupyter lab
```

7. No navegador, abra `notebooks\00_entendimento_do_dataset.ipynb` ou `notebooks\01_modelagem_faixas_atraso.ipynb`.
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

É importante abrir o JupyterLab na raiz do projeto ou gerar a base antes de abrir o notebook. O notebook procura o diretório `data` subindo a partir da pasta de trabalho.

### Problemas comuns

- **`conda` não é reconhecido:** use o Anaconda Prompt, não o PowerShell comum.
- **`python` abre a Microsoft Store:** use o Anaconda Prompt e confirme `conda activate mcdia-ml-voos`.
- **CSV não encontrado:** execute `python scripts\\preparar_dados_v2.py` na raiz do projeto antes de abrir o notebook.
- **Kernel não aparece:** execute o comando `ipykernel install` acima e reinicie o JupyterLab.

## Abrir o notebook no Linux Fedora com Python e JupyterLab

No Fedora GNOME, abra o **Terminal** (`Ctrl + Alt + T`) e instale os pacotes necessários:

```bash
sudo dnf install -y git python3.14 python3.14-pip
```

Confirme a versão do Python:

```bash
python3.14 --version
```

Se o projeto ainda não estiver no computador, clone-o uma vez:

```bash
mkdir -p ~/Git
cd ~/Git
git clone https://github.com/fonsecan/mcdia-ml-previsao-atraso-voos.git
```

Entre na pasta do projeto e crie o ambiente virtual:

```bash
cd ~/Git/mcdia-ml-previsao-atraso-voos
python3.14 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install ipykernel
```

Registre o kernel do ambiente:

```bash
python -m ipykernel install --user \
  --name mcdia-ml-voos \
  --display-name "Python (mcdia-ml-voos)"
```

Materialize o dataset e as divisões versionadas:

```bash
python scripts/gerenciar_datasets.py materializar dataset-000001
python scripts/gerenciar_divisoes.py materializar split-000001
python scripts/gerenciar_divisoes.py materializar split-000002
python scripts/gerenciar_divisoes.py materializar split-000003
python scripts/gerenciar_divisoes.py materializar split-000004
```

Inicie o JupyterLab a partir da raiz do projeto:

```bash
jupyter lab
```

No navegador, abra `notebooks/00_entendimento_do_dataset.ipynb` ou `notebooks/01_modelagem_faixas_atraso.ipynb` e selecione o kernel **Python (mcdia-ml-voos)**.

Nas próximas sessões, basta executar:

```bash
cd ~/Git/mcdia-ml-previsao-atraso-voos
source .venv/bin/activate
jupyter lab
```








## Abrir o notebook no Linux com Python 3.14, sem Conda

Este fluxo usa o ambiente virtual nativo do Python (`venv`). Abra um terminal Linux. Os blocos abaixo são independentes; execute um bloco por vez.

Confirme que o Python 3.14 está instalado:

```bash
python3.14 --version
```

Se o comando não existir, instale o pacote Python 3.14 e o módulo `venv` usando o gerenciador de pacotes da sua distribuição. Os nomes dos pacotes podem variar entre distribuições.

Clone o projeto:

```bash
git clone https://github.com/fonsecan/mcdia-ml-previsao-atraso-voos.git
```

Entre na pasta do projeto:

```bash
cd mcdia-ml-previsao-atraso-voos
```

Crie o ambiente virtual com Python 3.14. Esse comando só precisa ser executado na primeira vez:

```bash
python3.14 -m venv .venv
```

Ative o ambiente:

```bash
source .venv/bin/activate
```

Com o ambiente ativo, atualize o instalador e instale as dependências:

```bash
python -m pip install --upgrade pip
```

```bash
python -m pip install -r requirements.lock
```

Materialize o dataset e as divisões versionadas:

```bash
python scripts/gerenciar_datasets.py materializar dataset-000001
python scripts/gerenciar_divisoes.py materializar split-000001
python scripts/gerenciar_divisoes.py materializar split-000002
python scripts/gerenciar_divisoes.py materializar split-000003
python scripts/gerenciar_divisoes.py materializar split-000004
```

Abra o JupyterLab a partir da raiz do projeto:

```bash
jupyter lab
```

No navegador, abra `notebooks/00_entendimento_do_dataset.ipynb` ou `notebooks/01_modelagem_faixas_atraso.ipynb`. Se o kernel não aparecer, execute com o ambiente `.venv` ativo:

```bash
python -m ipykernel install --user --name mcdia-ml-voos-py314 --display-name "Python (mcdia-ml-voos-py314)"
```

Para sair do ambiente virtual depois do uso:

```bash
deactivate
```

Se o terminal for fechado, reative o ambiente entrando novamente na pasta do projeto e executando `source .venv/bin/activate`. O diretório `.venv` é local e não deve ser versionado.
## Preparar a base de modelagem

O dataset versionado já gera a base usada pelos modelos. Para preparar uma base temporária, fora do fluxo oficial de runs, execute no Anaconda Prompt:

```powershell
python scripts\preparar_modelagem.py
```

O script cria localmente os arquivos de modelagem e a distribuição mensal das seis classes. Abra então o notebook notebooks/01_modelagem_faixas_atraso.ipynb. Ele usa treino de janeiro de 2024 a junho de 2025, validação de julho a setembro de 2025 e teste de outubro a dezembro de 2025.



Os resultados da primeira execução dos baselines estão em [docs/05-resultados-baseline.md](docs/05-resultados-baseline.md).

A validação progressiva e a comparação com a divisão anterior estão em [docs/06-validacao-progressiva.md](docs/06-validacao-progressiva.md).

O guia de algoritmos, métricas, validação temporal e execução de novas runs está em [docs/07-guia-algoritmos-e-execucao.md](docs/07-guia-algoritmos-e-execucao.md).

## Histórico das runs de treinamento

As 16 combinações de modelo e janela da validação progressiva foram importadas para pastas numeradas em `runs/`. Cada pasta contém sua definição, manifesto, métricas e resumo. Consulte [runs/README.md](runs/README.md) para entender os arquivos e criar novas runs.
