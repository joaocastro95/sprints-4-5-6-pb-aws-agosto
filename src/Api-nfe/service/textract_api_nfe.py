import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Configuração do logger
logger = logging.getLogger(__name__)  # Corrigido para usar __name__
logger.setLevel(logging.INFO)

# Inicializando o cliente Textract
textract_client = boto3.client('textract')

def analyze_file(file_bytes):
    """
    Envia o arquivo em bytes para o Textract e retorna o texto extraído em JSON.
    
    Parâmetros:
        file_bytes (bytes): O conteúdo do arquivo em bytes.
    
    Retorna:
        list: Resultados da análise do Textract em formato JSON.
    """
    try:
        # Chama o Textract para analisar o documento usando o tipo de análise "FORMS"
        response = textract_client.analyze_document(
            Document={'Bytes': file_bytes},
            FeatureTypes=["TABLES", "FORMS"]
        )
        
        logger.info("Análise do Textract completa!")
        
        extracted_text = extract_text_from_blocks(response["Blocks"])  # Corrigido para o nome da função
        
        return extracted_text
    
    except (BotoCoreError, ClientError) as e:  # Corrigido a indentação
        logger.error(f"Erro ao analisar o documento: {str(e)}")  # Usando logger para erros
        raise


def extract_text_from_blocks(blocks: list) -> str:
    """
    Extrai o texto dos blocos retornados pela análise do Textract.

    Parâmetros:
        blocks (list): Lista de blocos retornada pela resposta do Textract.

    Retorna:
        str: Texto concatenado extraído dos blocos de texto.
    """
    line_text = [block["Text"] for block in blocks if block["BlockType"] == "LINE"]
    extracted_text = "\n".join(line_text)
    print(f"Texto extraído: {extracted_text[:50]}...")  # Mostrando os primeiros 50 caracteres
    
    return extracted_text
