from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import errors as mongoerrors
import os
from dotenv import load_dotenv
# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()
import requests
import json
from datetime import datetime, date

# # URIs do projeto
# Mongo DB Atlas
uri_mongo = f"mongodb+srv://{os.getenv('DB_USER')}:{os.getenv('DB_PWD')}@{os.getenv('DB_CLUSTER')}/?retryWrites=true&w=majority&appName=Cluster0"
# API Awesome Cotação Dolar
uri_currency_quotes_dolar = f"https://economia.awesomeapi.com.br/json/daily/USD-BRL/30?" + os.getenv('API_KEY')
# API Awesome Cotação Euro
uri_currency_quotes_euro = f"https://economia.awesomeapi.com.br/json/daily/EUR-BRL/30?" + os.getenv('API_KEY')

# Realiza a conexão com o MongoDB.
def conectar(uri:str)->MongoClient:
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
    except mongoerrors.ConnectionFailure as e:
        client = None
        print(e)
    return client   

# Realiza a criação do Database e da Coleção de dados JSON.
def criar_database(uri:str, database:str, collection:str)->str:
   try:
      client = conectar(uri=uri)

      databases = client.list_database_names()
    
      if database in databases:  # Verifica se o Database já existe. Caso contrário o cria.
        db = client[database]
        colecao = db[collection]
        colecoes = db.list_collection_names()

      if collection not in colecoes: # Verifica se a Coleção já exsite. Caso contrário a cria.
        db = client[database]
        db.create_collection(collection)
        
      return database, collection
   except mongoerrors.PyMongoError as e:
      print(f"Erro ao criar o Database/Collection: {e}")
   finally:
      client.close()

# Carrega os dados tratados, obtidos via API (JSON) para a Coleção no MongoDB.
def carregar_dados(uri:str, data:list, database:str, collection:str )->None:
    try:
        client = conectar(uri=uri)

        databases = client.list_database_names()

        if database in databases: 
            db = client[database]
            colecao = db[collection]
            colecao.insert_many(data)
        else:
            print(f"Database: Erro")
       
    except mongoerrors.PyMongoError as e:
        print(f"Erro ao carregar os dados: {e}")
    finally:
        client.close()      

# Extrai os dados via API e retorna uma coleção (JSON)
def extrair_dados(uri:str)->json:
    try:
        response = requests.get(url=uri)
        data = response.json()
    except Exception as e:
        data = None
        print(f"Erro ao extrair os dados!: {e}")

    return data       

# Realiza os tratamentos necessários nos dados antes de enviar para a coleção no MongoDB.
def transformar_dados(data:json)->list:

    lista_dados = []

    moeda_de = data[0]['code']
    moeda_para = data[0]['codein']
    conversao = data[0]['name']

    lista_dados.append
    (
        {
                "moeda_de" : moeda_de,
                "moeda_para" : moeda_para,
                "conversao" : conversao,
                "valor_maximo" : data[0]['high'],
                "valor_minimo" : data[0]['low'],
                "variacao" : data[0]['varBid'],
                "porcentagem_variacao" : data[0]['pctChange'],
                "valor_compra" : data[0]['bid'],
                "valor_venda" : data[0]['ask'],
                "data_negociacao" : datetime.strftime(datetime.fromtimestamp(int(data[0]['timestamp'])), '%d/%m/%Y %H:%M:%S') 
            }
    )        

    for i, d in enumerate(data[1:]):
        lista_dados.append(
            {
                "moeda_de" : moeda_de,
                "moeda_para" : moeda_para,
                "conversao" : conversao,
                "valor_maximo" : data[i]['high'],
                "valor_minimo" : data[i]['low'],
                "variacao" : data[i]['varBid'],
                "porcentagem_variacao" : data[i]['pctChange'],
                "valor_compra" : data[i]['bid'],
                "valor_venda" : data[i]['ask'],
                "data_negociacao" : datetime.strftime(datetime.fromtimestamp(int(data[i]['timestamp'])), '%d/%m/%Y %H:%M:%S') 
            }
        )
        
    return lista_dados        

def main():
    try:
        # Extrai os dados via API do site https://economia.awesomeapi.com.br
        dados = extrair_dados(uri=uri_currency_quotes_euro)

        if dados:

            # Faz os tratamentos necessarios nos dados
            dados_tratados = transformar_dados(data=dados)

            # Cria o database e a coleção no MongoDB
            database, collection = criar_database(uri=uri_mongo, database="engenharia_dados", collection="currency_quotes")

            # Carrega os dados tratados na coleção no MongoDB
            carregar_dados(uri=uri_mongo, data=dados_tratados, database=database, collection=collection)  
    except Exception as e:
        print(f"Erro de execução do processo de ETL: {e}")      


if __name__ == '__main__':
    main()