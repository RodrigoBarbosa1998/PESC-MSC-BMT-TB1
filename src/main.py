import xml.etree.ElementTree as ET
import os
import csv
import math
from nltk.tokenize import word_tokenize
import xml.etree.ElementTree as ET
from ast import literal_eval
from collections import defaultdict
from math import sqrt
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')

def read_configuration_file(file_path):
    instructions = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            instructions[key.strip()] = value.strip()
    return instructions

def calculate_votes(score):
    return sum(int(digit) for digit in str(score))

def process_queries(xml_file, output_processed_queries, output_expected_results):
    queries = {}

    # Parse XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Processar cada consulta
    logging.info("\nProcessando cada Consulta")
    for raw_query in root.iter('QUERY'):
        query_number = None
        query_text = None
        query_results = {}

        for element in raw_query.iter():
            if element.tag == 'QueryNumber':
                query_number = element.text.strip()
            elif element.tag == 'QueryText':
                query_text = element.text.strip().upper()
            elif element.tag == 'Records':
                for item in element.iter('Item'):
                    doc_number = int(item.text.strip())
                    doc_score = int(item.attrib.get('score'))
                    query_results[doc_number] = calculate_votes(doc_score)

        if query_number and query_text:
            queries[int(query_number)] = {'text': query_text, 'results': query_results}

    # Gravar consultas processadas em CSV
    logging.info("\nGravando Consultas Processadas em CSV - Arquivo %s", output_processed_queries)
    with open(output_processed_queries, 'w') as processed_queries_file:
        processed_queries_file.write('QueryNumber;QueryText\n')
        for query_number, query_data in queries.items():
            query_text = query_data['text'].replace('\n', ' ').strip().replace("    ", " ")  
            processed_queries_file.write(f'{query_number};"{query_text}"\n')

    # Resultados esperados em CSV
    logging.info("\nGravando Resultados Esperados em CSV - Arquivo %s", output_expected_results)
    with open(output_expected_results, 'w') as expected_results_file:
        expected_results_file.write('QueryNumber;DocNumber;DocScore\n')
        for query_number, query_data in queries.items():
            for doc_number, doc_score in query_data['results'].items():
                expected_results_file.write(f'{query_number};{doc_number};{doc_score}\n')
                

def read_inverted_list_config(file_path):
    instructions = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            instructions[key.strip()] = value.strip()
    return instructions

def process_xml_files(xml_files):
    logging.info("\nProcessando Arquivos XML\n")
    documents = {}
    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for record in root.findall('RECORD'):
            record_num = int(record.find('RECORDNUM').text)
            abstract = record.find('ABSTRACT')
            extract = record.find('EXTRACT')
            abstract_text = abstract.text if abstract is not None else extract.text if extract is not None else ""
            documents[record_num] = word_tokenize(abstract_text)
        logging.info("Arquivo %s Processado", xml_file)
    return documents

def generate_inverted_list(data, stop_words):
    logging.info("\nGerando Lista Invertida")
    inverted_list = {}
    for record_num, abstract_text in data.items():
        if isinstance(abstract_text, list):
            abstract_text = ' '.join(abstract_text)  # Convertendo lista para string
        words = abstract_text.split()
        for word in words:
            word = word.upper().strip(';')
            if word not in stop_words:
                if word not in inverted_list:
                    inverted_list[word] = [record_num]
                else:
                    inverted_list[word].append(record_num)
    return inverted_list

def write_inverted_list_to_csv(inverted_list, output_file):
    with open(output_file, 'w') as csv_file:
        csv_file.write('Word;DocumentIDs\n')
        for word, doc_ids in inverted_list.items():
            csv_file.write(f'{word};{doc_ids}\n')

# Função para carregar as stop words de um arquivo
def load_stop_words(file_path):
    with open(file_path, 'r') as file:
        stop_words = [word.strip().upper() for word in file.readlines()]
    return stop_words

def read_inverted_list(file_path):
    inverted_list = {}
    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            word = row[0]
            doc_ids = row[1:]
            inverted_list[word] = doc_ids
    return inverted_list

def process_inverted_list(inverted_list):
    logging.info("\nIndexando a Lista Invertida")
    vector_model = {}

    # Número total de documentos
    N = len(inverted_list)

    # Extraindo a lista de documentos de inverted_list
    document_list = list(set(doc_id for term_freqs in inverted_list.values() for doc_id in term_freqs))

    # Iterando sobre cada termo e suas frequências de documentos associadas
    for term, term_freqs in inverted_list.items():
        documents_occurred = list(set(term_freqs))
        
        idf = math.log(len(document_list) / len(documents_occurred))  # Calculating IDF

        # Estrutura de dados para armazenar o peso de cada documento para o prazo atual
        document_data = {}

        # Calculando o peso de cada documento para o prazo atual
        for document in documents_occurred:            
            # Verificando se o documento existe na lista
            if document in inverted_list[term]:
                # Calculando a frequência do termo
                tf = inverted_list[term].count(document)
                # Normalizando  TF
                tf_n = tf / len(inverted_list[term])
            else:
                # Se o documento não existir, retorne 0
                tf_n = 0
        
            weight = tf_n * idf  # Calculando o peso
            document_data[document] = weight

        # Armazenando IDF e pesos de documentos para o termo atual no modelo
        vector_model[term] = (idf, document_data)
    
    logging.info("\nIndexador Segundo o Modelo Vetorial Gerado")
    return vector_model

def write_vector_model(vector_model, output_file):
    field_names = ['word', 'data']
    with open(output_file, 'w+') as csv_file:
        writer = csv.DictWriter(csv_file, delimiter=';', lineterminator='\n', fieldnames=field_names)
        writer.writeheader()

        for term, (idf, document_data) in vector_model.items():
            writer.writerow({'word': term, 'data': document_data})

def load_inverted_list(file_path):
    logging.info("\nCarregando Lista Invertida - Leitura do CSV")
    inverted_list = {}
    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)  # Pular cabeçalho
        for row in reader:
            word = row[0]
            doc_ids = literal_eval(row[1])  # Convertendo a string em uma lista de documentos
            inverted_list[word] = doc_ids
    return inverted_list

def load_vector_model(file_path):
    logging.info("\nCarregando Modelo Vetorial - Leitura CSV")
    vector_model = defaultdict(list)
    
    with open(file_path, 'r') as file:
        next(file) 
        
        for line in file:
            # Divide a linha em palavra e dados
            word, data_str = line.strip().split(';')
            
            # Converte a string de dados em um dicionário usando literal_eval
            data = literal_eval(data_str)
            
            # Adiciona cada termo e peso à lista correspondente à classe no dicionário
            for doc_id, weight in data.items():
                vector_model[doc_id].append((word, weight))
    return vector_model

def load_queries(file_path):
    logging.info("\nCarregando Consultas (Queries) - Leitura CSV")
    queries = defaultdict(list)
    with open(file_path, 'r') as file:
        # Ler linhas do arquivo
        lines = file.readlines()
        
        # Iterar sobre as linhas para extrair as consultas
        i = 1  # Começar a partir da segunda linha, ignorando o cabeçalho
        while i < len(lines):
            line = lines[i].strip()  
            if line:  # Verificar se a linha não está vazia
                # Verificar se a próxima linha começa com espaços em branco, indicando uma continuação
                while i + 1 < len(lines) and lines[i + 1].startswith(' '):
                    # Adicionar a linha atual à próxima linha e remover espaços em branco no início
                    line += lines[i + 1].lstrip()
                    i += 1  
                    
                # Dividir a linha em duas partes no primeiro ponto e vírgula encontrado
                parts = line.split(';', 1)
                
                # Verificar se a linha foi dividida corretamente
                if len(parts) == 2:
                    query_number = int(parts[0].strip())  # Extrair o número da consulta e remover espaços em branco
                    query_text = parts[1].strip().strip('"').split()  # Extrair o texto da consulta e remover espaços em branco
                    
                    # Adicionar as palavras da consulta à lista de consultas correspondente ao número
                    queries[query_number] = query_text
                else:
                    print(f"Erro na linha: {line}")
            i += 1  
    return queries

def calculate_similarity(query, doc_vector):
    doc_vector = dict(doc_vector)
    if isinstance(doc_vector, dict):
        dot_product = sum((1 if word in query else 0) * weight for word, weight in doc_vector.items())
        query_magnitude = sqrt(len(query))  # Considerando o tamanho da lista como magnitude
        doc_magnitude = sqrt(sum(weight ** 2 for word, weight in doc_vector.items()))
        if query_magnitude == 0 or doc_magnitude == 0:
            return 0
        similarity = dot_product / (query_magnitude * doc_magnitude)
        return similarity
    return 0

def perform_search(vector_model, queries):
    logging.info("\nRealizando a Busca - Resposta Encontrada p/ Consulta")
    search_results = []
    for i, query in enumerate(queries, start=1):
        query_results = []
        for doc_id, doc_vector in vector_model.items():
            similarity = calculate_similarity(queries[query], doc_vector)
            query_results.append((similarity, doc_id))
        query_results.sort(reverse=True) 
        search_results.append((i, query_results))
    return search_results

def write_search_results(results, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=';')
        for query_id, query_results in results:
            for position, (similarity, doc_id) in enumerate(query_results, start=1):
                csv_writer.writerow([query_id, [position, doc_id, similarity]])
              

def main():
    logging.info("\nIniciando Implementação do Sistema de Recuperação em Memória Segundo Modelo Vetorial.")
    
    logging.info("\n\n\n-------------------------------------------------------------------------\n\n")
    
    # Processador de Consultas
    logging.info("\nInício Módulo Processador de Consultas")
    # Registra o tempo de início
    start_time = time.time()

    logging.info("\nLeitura do arquivo de configurações - pc.cfg")
    current_directory = os.getcwd()
    config_file = 'pc.cfg'
    config = read_configuration_file(current_directory + '\\src\\' + config_file)

    xml_file = config['LEIA']
    processed_queries_output = config['CONSULTAS']
    expected_results_output = config['ESPERADOS']

    process_queries(current_directory + '\\data\\' + xml_file, current_directory + '\\RESULT\\' + processed_queries_output, current_directory + '\\RESULT\\' + expected_results_output)
    # Registra o tempo de término
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info("\nTempo de Execução: %s segundos", math.ceil(execution_time))
    logging.info("\nFim Módulo Processador de Consultas")
    
    logging.info("\n\n\n-------------------------------------------------------------------------\n\n")

    # Gerador de Lista Invertida
    logging.info("\nInício Módulo Gerador Lista Invertida")
    # Registra o tempo de início
    start_time = time.time()
    logging.info("\nLeitura do arquivo de configurações - gli.cfg")
    inverted_list_config_file = 'gli.cfg'
    inverted_list_config = read_inverted_list_config(os.path.join(current_directory, 'src', inverted_list_config_file))
    xml_files = inverted_list_config['LEIA'].split(', ')
    output_file = inverted_list_config['ESCREVA']

    xml_data = process_xml_files([os.path.join(current_directory, file) for file in xml_files])
    
    logging.info("\nCarregando lista de Stop Words")
    # Carregar stop words
    stop_words = load_stop_words(os.path.join(current_directory, 'stopwords.txt'))
    logging.info("\n%s Stop Words Carregadas", len(stop_words))
    
    inverted_list = generate_inverted_list(xml_data, stop_words)
    logging.info("\nGravando Lista Invertida em CSV - Arquivo %s", os.path.join(current_directory, output_file))
    write_inverted_list_to_csv(inverted_list, os.path.join(current_directory, output_file))
    
    # Registra o tempo de término
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info("\nTempo de Execução: %s segundos", math.ceil(execution_time))
    logging.info("\nFim Módulo Gerador Lista Invertida")
    
    logging.info("\n\n\n-------------------------------------------------------------------------\n\n")
    
    # Indexador
    logging.info("\nInício Módulo Indexador")
    # Registra o tempo de início
    start_time = time.time()
    
    logging.info("\nLeitura do arquivo de configurações - index.cfg")
    current_directory = os.getcwd()
    index_config_file = 'index.cfg'
    index_config = read_configuration_file(os.path.join(current_directory, 'src', index_config_file))

    inverted_list_file = index_config['LEIA']
    output_file = index_config['ESCREVA']

    inverted_list = load_inverted_list(os.path.join(current_directory, inverted_list_file))
    
    # Indexar a lista invertida e salvar o modelo vetorial
    vector_model_index = process_inverted_list(inverted_list)
    logging.info("\nGravando Modelo Vetorial em CSV - Arquivo %s", os.path.join(current_directory, output_file))
    write_vector_model(vector_model_index, os.path.join(current_directory, output_file))
    # Registra o tempo de término
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info("\nTempo de Execução: %s segundos", math.ceil(execution_time))
    logging.info("\nFim Módulo Indexador")
    
    logging.info("\n\n\n-------------------------------------------------------------------------\n\n")
    
    #Buscador
    logging.info("\nInício Módulo Buscador")
    # Registra o tempo de início
    start_time = time.time()
    
    logging.info("\nLeitura do arquivo de configurações - busca.cfg")
    search_config_file = 'busca.cfg'
    search_config = read_configuration_file(os.path.join(current_directory, 'src', search_config_file))

    vector_model_file = search_config['MODELO']
    queries_file = search_config['CONSULTAS']
    results_file = search_config['RESULTADOS']

    # Carregar modelo vetorial
    vector_model = load_vector_model(os.path.join(current_directory, vector_model_file))

    # Carregar consultas
    queries = load_queries(os.path.join(current_directory, queries_file))

    # Realizar busca
    search_results = perform_search(vector_model, queries)

    # Escrever resultados
    logging.info("\nGravando RESULTADOS em CSV")
    write_search_results(search_results, os.path.join(current_directory, results_file))
    # Registra o tempo de término
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info("\nTempo de Execução: %s segundos", math.ceil(execution_time))
    logging.info("\nFim Módulo Buscador\n\n\n")
    

if __name__ == "__main__":
    main()
