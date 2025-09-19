import json
import boto3
import base64
import uuid
import traceback
import logging
from service.textract_api_nfe2 import analyze_file
from service.llm_api_nfe2 import process_with_llm , move_Image


logger = logging.getLogger(__name__)  
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    bucket_name = 'api-nfe2'
    try:
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Corpo da requisição não encontrado."})
            }
        
        body = event['body']
        
        # Decodificar se estiver em base64
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body)

        if isinstance(body, str):
            body = body.encode('utf-8')

        # Processar o arquivo multipart para extrair os bytes da imagem
        boundary = body.split(b'\r\n')[0]
        parts = body.split(boundary)[1:-1]

        for part in parts:
            if b'Content-Disposition' in part:
                header, content = part.split(b'\r\n\r\n', 1)
                content = content.rstrip(b'\r\n')  # Conteúdo do arquivo em bytes
                
                # Opcional: Gerar chave única para o arquivo no S3 e armazenar o arquivo (caso necessário)
                unique_id = str(uuid.uuid4())
                image_key = f'notas/{unique_id}.jpg'

                # Armazenar a imagem no bucket S3 (se ainda for necessário)
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=image_key,
                    Body=content
                )
                print(f'Imagem {image_key} enviada com sucesso.')

                # Processar a imagem diretamente com Textract (analyze_file agora recebe o arquivo em bytes)
                extracted_data = analyze_file(content)  # Passa o conteúdo em bytes para análise
                logger.info(json.dumps(extracted_data, indent = 2))

                # Enviar dados para o LLM
                processed_response = process_with_llm(extracted_data)
                logger.info(json.dumps(processed_response, indent = 2))
                move_Image(bucket_name,image_key, processed_response.get("forma_pgto").lower())

                # Devolver a resposta com os dados extraídos e processados
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'mensagem': 'Imagem enviada com sucesso!',
                        'dados_extraidos': extracted_data,
                        'resposta_llm': processed_response
                    }, ensure_ascii=False)
                }

    except Exception as e:
        logger.info(traceback.format_exc())
        print(f"Erro ao processar o evento: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Erro interno: {str(e)}")
        }
