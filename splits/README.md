# Divisões versionadas

Cada diretório `split-NNNNNN` define uma divisão de **um** dataset. A definição e a receita são versionadas; a atribuição de cada registro e o manifesto são gerados localmente. A atribuição usa `id_registro`, composto por `arquivo_origem:linha_origem`, e evita duplicar o dataset completo em treino, validação e teste.

Materialize uma divisão somente após o dataset correspondente estar materializado:

```bash
python scripts/gerenciar_divisoes.py materializar split-000001
```

O manifesto da divisão guarda os hashes do dataset, da atribuição e do arquivo de definição. O executor de runs exige esses hashes antes de treinar, para impedir que uma run use silenciosamente uma divisão diferente.
