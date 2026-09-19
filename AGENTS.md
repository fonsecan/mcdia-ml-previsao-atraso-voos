# Instruções para agentes

- Usar somente dados públicos e os campos necessários à pergunta.
- Registrar fonte, URL, data da coleta, período, filtros, campos e transformações.
- O alvo inicial é agregado a partir de voos individuais; não criar perfil de passageiros.
- Não usar horários reais, situação do voo ou qualquer campo derivado do futuro como entrada.
- Manter arquivos brutos em `data/raw/`, ignorados pelo Git, e dados derivados pequenos em `data/`.
- Arquivos textuais devem ser UTF-8 sem BOM.
