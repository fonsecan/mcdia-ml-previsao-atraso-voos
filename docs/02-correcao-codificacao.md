# Correção do diagnóstico de codificação

A primeira execução exibiu nomes como `Empresa A�rea`, o que parecia indicar uma codificação legada. A inspeção dos bytes mostrou que o arquivo começa com sequências UTF-8 válidas, por exemplo `A\xc3\xa9rea`; portanto, o CSV da ANAC é UTF-8.

O problema estava na exibição do resultado pelo terminal Windows, que substituiu caracteres acentuados ao imprimir a saída. O auditor v2 mantém `utf-8-sig` como codificação selecionada e identifica a coluna `Situação Voo` corretamente.

Conclusão: não devemos recodificar o CSV para latin1. Ao trabalhar no Windows, preferir arquivos JSON/CSV gravados em UTF-8 e, quando necessário, configurar o terminal para UTF-8.
