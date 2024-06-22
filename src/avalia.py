import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nltk.stem import PorterStemmer
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score, average_precision_score

import os

current_directory = os.getcwd()
output_directory = os.path.join(current_directory, 'AVALIA')

# Criar diretório AVALIA se não existir
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Carregar dados
resultados = pd.read_csv(os.path.join(current_directory, 'RESULT', 'RESULTADOS.csv'), delimiter=';', header=None, names=['Query', 'DocID', 'Score'])
resultados_esperados = pd.read_csv(os.path.join(current_directory, 'RESULT', 'expected_results.csv'), delimiter=';')

# Configuração do Stemmer
use_stemmer = True  # Defina como False para NOSTEMMER

# Inicializar Stemmer de Porter
stemmer = PorterStemmer() if use_stemmer else None

def preprocess(text, stemmer=None):
    # Tokenização e stemming (se aplicável)
    tokens = text.lower().split()
    if stemmer:
        tokens = [stemmer.stem(token) for token in tokens]
    return tokens

# Funções de avaliação

def calcular_11_pontos_precisao_recall(resultados, esperados):
    # Verificar e remover NaNs
    resultados = np.nan_to_num(resultados)
    esperados = np.nan_to_num(esperados)
    
    precisions, recalls, _ = precision_recall_curve(esperados, resultados)
    recall_levels = np.linspace(0, 1, 11)
    precision_at_recall = [max(precisions[recalls >= recall]) for recall in recall_levels]
    
    plt.plot(recall_levels, precision_at_recall, marker='o')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('11-Point Precision-Recall Curve')
    plt.savefig(os.path.join(output_directory, '11_pontos_precisao_recall.pdf'))
    plt.show()
    return precision_at_recall, recall_levels

def calcular_f1(resultados, esperados):
    resultados = np.nan_to_num(resultados)
    esperados = np.nan_to_num(esperados)
    f1 = f1_score(esperados, resultados, zero_division=1)
    return f1

def calcular_precision_at_k(resultados, esperados, k):
    resultados = np.nan_to_num(resultados)
    esperados = np.nan_to_num(esperados)
    precision_at_k = precision_score(esperados[:k], resultados[:k], zero_division=1)
    return precision_at_k

def calcular_r_precision(resultados, esperados):
    resultados = np.nan_to_num(resultados)
    esperados = np.nan_to_num(esperados)
    r = sum(esperados)
    r_precision = precision_score(esperados[:r], resultados[:r], zero_division=1)
    return r_precision

def calcular_map(resultados, esperados):
    resultados = np.nan_to_num(resultados)
    esperados = np.nan_to_num(esperados)
    map_score = average_precision_score(esperados, resultados)
    return map_score

def calcular_mrr(resultados, esperados):
    resultados = np.nan_to_num(resultados)
    esperados = np.nan_to_num(esperados)
    for i, result in enumerate(resultados):
        if result in esperados:
            return 1 / (i + 1)
    return 0

def calcular_dcg(resultados, esperados):
    resultados = np.nan_to_num(resultados)
    esperados = np.nan_to_num(esperados)
    dcg = 0.0
    for i, result in enumerate(resultados):
        if result in esperados:
            dcg += 1 / np.log2(i + 2)
    return dcg

def calcular_ndcg(resultados, esperados):
    dcg = calcular_dcg(resultados, esperados)
    idcg = calcular_dcg(sorted(esperados, reverse=True), esperados)
    ndcg = dcg / idcg if idcg > 0 else 0.0
    return ndcg

# Normalizar scores
resultados['Score'] = resultados['Score'] / resultados['Score'].max()

# Corrigir formato dos dados em 'DocID'
resultados['DocID'] = resultados['DocID'].apply(lambda x: int(eval(x)[1]) if isinstance(x, str) else x)

# Avaliação e geração de relatórios
resultados_esperados_bin = [1 if doc in resultados_esperados['DocNumber'].values else 0 for doc in resultados['DocID']]

# Verificar se existem classes positivas em resultados_esperados_bin
print("Unique values in resultados_esperados_bin:", np.unique(resultados_esperados_bin))

# Verificar se existem documentos em resultados que correspondem aos esperados
print("Unique DocIDs in resultados:", resultados['DocID'].unique())
print("Unique DocNumbers in resultados_esperados:", resultados_esperados['DocNumber'].unique())

precision_recall = calcular_11_pontos_precisao_recall(resultados['Score'], resultados_esperados_bin)
f1 = calcular_f1(resultados['Score'], resultados_esperados_bin)
precision5 = calcular_precision_at_k(resultados['Score'], resultados_esperados_bin, 5)
precision10 = calcular_precision_at_k(resultados['Score'], resultados_esperados_bin, 10)
r_precision = calcular_r_precision(resultados['Score'], resultados_esperados_bin)
map_score = calcular_map(resultados['Score'], resultados_esperados_bin)
mrr = calcular_mrr(resultados['DocID'].values, resultados_esperados['DocNumber'].values)
dcg = calcular_dcg(resultados['Score'], resultados_esperados_bin)
ndcg = calcular_ndcg(resultados['Score'], resultados_esperados_bin)

# Imprimir resultados
print(f"F1 Score: {f1}")
print(f"Precision@5: {precision5}")
print(f"Precision@10: {precision10}")
print(f"R-Precision: {r_precision}")
print(f"MAP: {map_score}")
print(f"MRR: {mrr}")
print(f"DCG: {dcg}")
print(f"nDCG: {ndcg}")

# Salvar gráficos em .csv e .pdf
precision_recall_df = pd.DataFrame({
    'Recall': precision_recall[1],
    'Precision': precision_recall[0]
})
precision_recall_df.to_csv(os.path.join(output_directory, '11_pontos_precisao_recall.csv'), index=False)

plt.plot(precision_recall[1], precision_recall[0], marker='o')
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('11-Point Precision-Recall Curve')
plt.savefig(os.path.join(output_directory, '11_pontos_precisao_recall.pdf'))

# Documentar resultados em RELATORIO.MD
with open(os.path.join(output_directory, 'RELATORIO.MD'), 'w') as f:
    f.write(f"# Avaliação do Sistema de Recuperação de Informação\n")
    f.write(f"## Resultados\n")
    f.write(f"- **F1 Score:** {f1}\n")
    f.write(f"- **Precision@5:** {precision5}\n")
    f.write(f"- **Precision@10:** {precision10}\n")
    f.write(f"- **R-Precision:** {r_precision}\n")
    f.write(f"- **MAP:** {map_score}\n")
    f.write(f"- **MRR:** {mrr}\n")
    f.write(f"- **DCG:** {dcg}\n")
    f.write(f"- **nDCG:** {ndcg}\n")
