import json
import urllib3
import boto3
import os
import uuid  

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME") 

s3_client = boto3.client('s3')

def move_Image(bucket,image,destino): 
    doc = image.split('/')[-1]
    s3=boto3.client("s3") 
    folder = "dinheiro" if destino.lower() == "dinheiro" else "outros"
    s3.copy_object(CopySource={"Bucket":bucket,"Key":image}, Bucket=bucket, Key=f"{folder}/{doc}") 
    

def upload_to_s3(data, bucket_name, payment_type):
    try:
        json_data = json.dumps(data)
        # Define the folder based on payment type
        folder = 'dinheiro/' if payment_type in ['dinheiro', 'pix'] else 'outros/'
        file_name = f"{folder}arquivo_{uuid.uuid4()}.json"
        s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=json_data)
        print(f"Arquivo JSON salvo com sucesso em {bucket_name}/{file_name}.")
        return True
    except Exception as e:
        print(f"Erro ao salvar o arquivo no S3: {e}")
        return False

def process_with_llm(extracted_data):
    prompt = f"""Instruction:
You are an expert in receipt data extraction focused on the financial sector. Your task is to analyze, detect, recognize, and extract key financial data from the OCR text of a receipt image. You will receive the output from an OCR system (like Textract), which may contain various fields with potentially different names or formats.

Please extract the following key fields into a strictly formatted JSON object, even if the field names differ slightly in the input:
1. nome_emissor: string | 'None'
2. CNPJ_emissor: string | 'None'
3. endereco_emissor: string | 'None'
4. CNPJ_CPF_consumidor: string | 'None'
5. data_emissao: string | 'None'
6. numero: string | 'None'
7. serie_nota_fiscal: string | 'None'
8. valor_total: string | 'None'
9. forma_pgto: string | 'None'

Output strictly in this JSON format. Here are some examples of how to identify each field based on the returned OCR text:
- nome_emissor: Look for company names and exclude terms like "consumidor" or "cliente".
- CNPJ_emissor: Format must be '00.000.000/0000-00', check for 14 digits.
- endereco_emissor: Should start with common address prefixes like "RUA" or "R".
- CNPJ_CPF_consumidor: Look for identifiers near "consumidor", must be formatted corretamente.
- data_emissao: Look for date formats 'DD/MM/YYYY' or 'DD-MM-YYYY'.
- numero: Look for terms like "Numero" or "No.".
- serie_nota_fiscal: Extract any series information found.
- valor_total: Look for monetary values with exatamente duas casas decimais.
- forma_pgto: Determine if payment is 'Pix', 'Dinheiro', or 'outros'.

Here is the extracted data from the receipt: {json.dumps(extracted_data)}. 

Return ONLY a JSON object with the specified fields and their values."""

    data = {
        "model": os.getenv("MODEL"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1024,
        "top_p": 0.7
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    http = urllib3.PoolManager()
    timeout = 2000
    
    try:
        response = http.request(
            "POST",
            API_URL,
            body=json.dumps(data).encode('utf-8'),
            headers=headers,
            timeout=timeout
        )

        if response.status == 200:
            llm_response = response.data.decode('utf-8')
            print("Resposta crua do LLM:", llm_response)  # Imprimindo resposta crua

            try:
                llm_data = json.loads(llm_response)
                json_result = llm_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if json_result:
                    try:
                        parsed_result = json.loads(json_result)
                        # Captura o tipo de pagamento após a análise do resultado
                        payment_type = parsed_result.get("forma_pgto", "None").lower()
                        # Agora fazemos o upload para o S3
                        if upload_to_s3(parsed_result, S3_BUCKET_NAME, payment_type):
                            return parsed_result
                        else:
                            return "Erro ao fazer upload do JSON para o S3."
                    except json.JSONDecodeError as json_err:
                        print(f"Erro de JSONDecode: {json_err}")
                        return f"Erro na decodificação do JSON retornado pelo LLM: {json_err}"
                else:
                    return "Nenhum dado retornado pelo LLM."
            except json.JSONDecodeError as json_err:
                print(f"Erro de JSONDecode: {json_err}")
                print("Resposta do LLM que causou o erro:", llm_response)  # Imprimindo resposta que causou erro
                return f"Erro na decodificação da resposta do LLM: {json_err}"
        else:
            return f"Erro ao se comunicar com o LLM: {response.status}"
    except Exception as e:
        return f"Erro na integração com o LLM: {str(e)}"



