from controller.lambda_controller_api_nfe2 import lambda_handler

def lambda_function(event: dict, context: object) -> dict:

    print("Função Lambda invocada.")  # Log 1
    print(f"Evento recebido: {event}")  # Log 2

    # Obtém a resposta
    response = lambda_handler(event, context)
    
    print(f"Resposta gerada pela função lambda_handler: {response}")  # Log da resposta gerada
    return response