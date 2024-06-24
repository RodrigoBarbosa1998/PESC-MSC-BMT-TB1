import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nltk.stem import PorterStemmer
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score, average_precision_score
import ast  # Para lidar com a conversão de strings para lista
import os

# Configurações de diretório e arquivos
current_directory = os.getcwd()
resultados_file = os.path.join(current_directory, 'RESULT', 'RESULTADOS.csv')
resultados_esperados_file = os.path.join(current_directory, 'RESULT', 'expected_results.csv')

# Carregar dados
resultados = pd.read_csv(resultados_file, delimiter=';', header=None)
resultados_esperados = pd.read_csv(resultados_esperados_file, delimiter=';', header=None)

# Leitura da opção do stemmer do arquivo de configuração
config_file = current_directory + '\\src\\config.txt'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        stemmer_choice = f.readline().strip()  # Ler a primeira linha e remover espaços em branco
else:
    stemmer_choice = "STEMMER"  # Se o arquivo de configuração não existir, use STEMMER por padrão

# Configuração do Stemmer
use_stemmer = True if stemmer_choice == "STEMMER" else False
stemmer = PorterStemmer() if use_stemmer else None  # Garantir que stemmer seja instanciado corretamente

# Função para pré-processamento dos dados
def preprocess(text, stemmer=None):
    try:
        results_list = ast.literal_eval(text)
        if isinstance(results_list, list):
            if stemmer:
                return [(0, 0, stemmer.stem(str(score))) for score in results_list]
            else:
                return [(0, 0, str(score)) for score in results_list]
        else:
            if stemmer:
                return [(0, 0, stemmer.stem(str(text)))]
            else:
                return [(0, 0, str(text))]
    except (SyntaxError, ValueError):
        if stemmer:
            return [(0, 0, stemmer.stem(str(text)))]
        else:
            return [(0, 0, str(text))]

# Aplicar pré-processamento aos resultados
resultados['Processed'] = resultados[1].apply(preprocess, stemmer=stemmer)

# Preparar dados para avaliação
resultados_flat = resultados.explode('Processed').reset_index(drop=True)
resultados_flat[['Posicao', 'DocNumber', 'DocScore']] = pd.DataFrame(resultados_flat['Processed'].tolist(), index=resultados_flat.index)
resultados_flat = resultados_flat.drop(['Processed', 0, 1], axis=1)

# Unir resultados com esperados
# Renomear as colunas para os nomes corretos
resultados_esperados.columns = ['QueryNumber', 'Esperado', 'DocScore']

# Eliminar a primeira linha que contém cabeçalhos
resultados_esperados = resultados_esperados.iloc[1:]  # Seleciona todas as linhas a partir da segunda

# Converter 'QueryNumber' para int64
resultados_esperados['QueryNumber'] = resultados_esperados['QueryNumber'].astype('int64')

# Agrupar resultados_flat por QueryNumber
resultados_flat_grouped = resultados_flat.groupby('Posicao')  # Ajuste aqui conforme a estrutura dos seus dados

# Inicializar listas para armazenar métricas
precision_recall_stemmer_all = []
f1_stemmer_all = []
precision5_stemmer_all = []
precision10_stemmer_all = []
r_precision_stemmer_all = []
map_score_stemmer_all = []

# Iterar sobre cada grupo de resultados por QueryNumber
for query, group_flat in resultados_flat_grouped:
    # Verificar se há resultados esperados para essa query
    if query in resultados_esperados['QueryNumber'].values:
        # Filtrar resultados esperados pela QueryNumber atual
        group_esperados = resultados_esperados[resultados_esperados['QueryNumber'] == query]['DocScore']
        
        # Verificar se há dados suficientes para calcular métricas
        if len(group_flat) > 0 and len(group_esperados) > 0:
            # Calcular métricas para o grupo atual
            precision_recall_stemmer = precision_recall_curve(group_esperados, group_flat['DocScore'])
            f1_stemmer = f1_score(group_esperados, group_flat['DocScore'])
            precision5_stemmer = precision_score(group_esperados, group_flat['DocScore'], pos_label=1, average='binary', k=5)
            precision10_stemmer = precision_score(group_esperados, group_flat['DocScore'], pos_label=1, average='binary', k=10)
            r_precision_stemmer = r_precision_score(group_esperados, group_flat['DocScore'])
            map_score_stemmer = average_precision_score(group_esperados, group_flat['DocScore'])
            
            # Armazenar métricas calculadas
            precision_recall_stemmer_all.append(precision_recall_stemmer)
            f1_stemmer_all.append(f1_stemmer)
            precision5_stemmer_all.append(precision5_stemmer)
            precision10_stemmer_all.append(precision10_stemmer)
            r_precision_stemmer_all.append(r_precision_stemmer)
            map_score_stemmer_all.append(map_score_stemmer)
        else:
            print(f"Dados insuficientes para calcular métricas para a Query {query}")

# Calcular métricas médias se necessário
# Exemplo de cálculo de média de precision_recall_stemmer_all:
if len(precision_recall_stemmer_all) > 0:
    precision_recall_stemmer_avg = np.mean(precision_recall_stemmer_all, axis=0)

    # Verifique se precision_recall_stemmer_avg contém valores válidos antes de plotar
    if isinstance(precision_recall_stemmer_avg, tuple) and len(precision_recall_stemmer_avg) > 1:
        # Gerar relatório em Markdown ou utilizar os resultados conforme necessário
        # Exemplo:
        with open('RELATORIO.MD', 'w') as f:
            f.write("# Avaliação do Sistema de Recuperação de Informação\n\n")
            
            f.write("## Resultados com Stemmer\n")
            f.write(f"- **F1 Score:** {np.mean(f1_stemmer_all)}\n")
            f.write(f"- **Precision@5:** {np.mean(precision5_stemmer_all)}\n")
            f.write(f"- **Precision@10:** {np.mean(precision10_stemmer_all)}\n")
            f.write(f"- **R-Precision:** {np.mean(r_precision_stemmer_all)}\n")
            f.write(f"- **MAP:** {np.mean(map_score_stemmer_all)}\n")

        # Gráfico de Precisão-Recall
        plt.plot(precision_recall_stemmer_avg[1], precision_recall_stemmer_avg[0], marker='o')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('11-Point Precision-Recall Curve')
        plt.savefig(f'11pontos-{stemmer_choice.lower()}.pdf')
        plt.show()
    else:
        print("Não há dados suficientes para gerar a curva de precisão-recall.")
else:
    print("Não há dados suficientes para calcular métricas.")

# Salvando os dados em CSV
resultados_flat.to_csv(f'RESULTADOS-{stemmer_choice}.csv', index=False, sep=';')
