import sys
import os
import boto3
import json
import logging
import pandas as pd
import pymysql

def lambda_mysql_backup(event, context):

    # Gerar logs de estado da execução
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Váriaveis Globais
    BUCKET_NAME = os.environ.get('BUCKET_NAME')
    AWS_SECRETNAME = os.environ.get('AWS_SECRETNAME')
    CSV_FILENAME = os.environ.get('CSV_FILENAME')

    #Conexão e serialização AWS Secret Manager
    try:
        # Conexão Secret Manager
        session = boto3.Session()
        client = session.client('secretsmanager')
        # Nome do segredo
        secret_name = AWS_SECRETNAME
        # Recupera o segredo
        response = client.get_secret_value(SecretId=secret_name)
        # Serialização json
        secret = json.loads(response['SecretString'])
        logger.info("Erro no Secret Manager")
    except Exception as e:
        logger.error(f"Erro Secret Manager: {e}")
        sys.exit()

    # Conexão com o banco de dados
    try:
        connection = pymysql.connect(
            host=secret.RDS_HOST, 
            user=secret.USER_NAME,
            passwd=secret.PASSWORD, 
            db=secret.DB_NAME, connect_timeout=5)
        logger.info("Conectado com sucesso ao banco de dados")
    except Exception as e:
        logger.error(f"Erro ao se conectar ao banco de dados: {e}")
        sys.exit()

    # Query SQL para consulta no banco de dados
    try:
        query_cursor = pd.read_sql_query(
            '''
            SELECT #nomedacoluna FROM #nomedatabela
            ''', connection)
        logger.info("Consulta SQL executada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao executar consulta SQL: {e}")
        sys.exit()

    # Exportar os dados da consulta SQL para um arquivo CSV
    try:
        query_cursor.to_csv(f'/tmp/{CSV_FILENAME}')
        logger.info("Dados exportados com sucesso para arquivo CSV")
    except Exception as e:
        logger.error(f"Erro ao exportar dados para CSV: {e}")
        sys.exit()

    # Conexão S3 
    try:
        s3 = boto3.client('s3')
        logger.info("Conectado com sucesso ao S3")
    except Exception as e:
        logger.error(f"Erro ao conectar ao S3: {e}")
        sys.exit()
      
     # Faz o upload do arquivo CSV para o S3 
    try:
        s3.upload_file(f'/tmp/{CSV_FILENAME}', BUCKET_NAME, CSV_FILENAME)
        logger.info("Arquivo CSV carregado com sucesso no S3")
    except Exception as e:
        logger.error(f"Erro ao fazer upload do arquivo CSV para o S3: {e}")
        sys.exit()


## Lambda 1 - Exporta dados da Query SQL para um arquivo CSV

## 1 - Conexão com Banco de Dados 
## 2 - Query que vai realizar consulta no banco de dados
## 3 - Exporta os dados obtidos pela query SQL para um arquivo CSV
## 4 - Enviar o arquivo CSV para um bucket no S3