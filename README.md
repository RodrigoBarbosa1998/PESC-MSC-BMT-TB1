# IMPLEMENTAÇÃO DE UM SISTEMA DE RECUPERAÇÃO EM MEMÓRIA SEGUNDO O MODELO VETORIAL

Um sistema de recuperação da informação dividido em módulos especificados a seguir.

## 1) Processador de Consultas

- Deverá ler um arquivo de configuração chamado `PC.CFG`, que contém duas instruções obrigatórias, nesta ordem:
  - `LEIA=cfquery.xml`
  - `CONSULTAS=processed_queries.csv`
  - `ESPERADOS=expected_results.csv`

- Deverá ler um arquivo XML indicado pela instrução `LEIA` no arquivo de configuração. O formato é descrito pelo arquivo `cfc2-query.dtd`. O arquivo a ser lido é `cfquery.xml`.

- Deverá gerar dois arquivos CSV:
  - O primeiro, indicado na instrução `CONSULTAS` do arquivo de configuração, conterá consultas processadas em letras maiúsculas, sem acento.
  - O segundo, indicado na instrução `ESPERADOS` do arquivo de configuração, conterá o número de votos de cada documento para cada consulta.

## 2) Gerador Lista Invertida

- Deverá ler um arquivo de configuração chamado `GLI.CFG`, que contém duas instruções:
  - `LEIA=data\cf74.xml, data\cf75.xml, data\cf76.xml, data\cf77.xml, data\cf78.xml, data\cf79.xml`
  - `ESCREVA=RESULT\inverted_list.csv`

- Deverá ler um conjunto de arquivos XML indicados pela instrução `LEIA` no arquivo de configuração. O formato é descrito pelo arquivo `cfc2.dtd`.

- Deverá gerar um arquivo CSV, indicado na instrução `ESCREVA` do arquivo de configuração, contendo uma lista invertida simples.

## 3) Indexador

- Será configurado por um arquivo chamado `INDEX.CFG`, que contém duas instruções:
  - `LEIA=RESULT\inverted_list.csv`
  - `ESCREVA=RESULT\vector_model.csv`

- Deverá implementar um indexador segundo o Modelo Vetorial, utilizando tf/idf padrão. A base a ser indexada está na instrução `LEIA` do arquivo de configuração.

- Deverá salvar toda a estrutura do Modelo Vetorial para utilização posterior.

## 4) Buscador

- Deverá ler o arquivo de consultas e o arquivo do modelo vetorial e realizar cada consulta, escrevendo outro arquivo com a resposta encontrada para cada consulta.

- Usará o arquivo de configuração `BUSCA.CFG`, que possui duas instruções:
  - `MODELO=RESULT\vector_model.csv`
  - `CONSULTAS=RESULT\processed_queries.csv`
  - `RESULTADOS=RESULT\RESULTADOS.csv`

- A busca será feita usando modelo vetorial. Cada palavra na consulta terá peso 1.

- O arquivo de resultados será no formato CSV, separando os campos por ponto e vírgula.

Cada uma dessas seções corresponde a um módulo do sistema e descreve suas funcionalidades, entradas e saídas esperadas.

## 5) Entrega dos Resultados

- Para executar o código, basta rodar o arquivo main.py e acompanhar os resultados sendo criados no diretório RESULT
    - `No diretório...\Code> python src/main.py`

- O resultado final, a busca realizada segundo o modelo vetorial, estará no arquivo RESULTADOS.csv no diretório RESULT