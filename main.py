import requests
import qrcode
import json
import time
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente
load_dotenv()

# Chaves e URLs
ID_CLIENTE = os.getenv('ID_CLIENTE')
CHAVE_SECRETA = os.getenv('CHAVE_SECRETA')
URL_TOKEN = 'https://oauth.livepix.gg/oauth2/token'
URL_API = 'https://api.livepix.gg/v2/payments'

# Obtém o token de acesso
def obter_token():
    try:
        dados = {
            'grant_type': 'client_credentials',
            'client_id': ID_CLIENTE,
            'client_secret': CHAVE_SECRETA,
            'scope': 'payments:write'
        }
        
        resposta = requests.post(URL_TOKEN, data=dados)
        resposta.raise_for_status()
        return resposta.json()
    
    except Exception as erro:
        print(f"Erro ao obter token: {erro}")
        return None

# Cria um pagamento com o valor de amount
def criar_pagamento(token_acesso):
    cabecalhos = {
        'Authorization': f'Bearer {token_acesso}',
        'Content-Type': 'application/json'
    }
    
    dados_pagamento = {
        'amount': 100,  # R$1,00 - Valor definido em centavos
        'currency': 'BRL',
        'redirectUrl': 'https://www.google.com/'
    }
    
    try:
        resposta = requests.post(
            URL_API,
            headers=cabecalhos,
            json=dados_pagamento
        )
        
        resposta.raise_for_status()
        return resposta.json()
    
    except requests.exceptions.RequestException as erro:
        print(f"Erro ao criar pagamento: {erro}")
        return None

# Extrai o id do pagamento e usa em outra endpoint para obter o Pix Copia e Cola
def obter_codigo_pix(id_pagamento):
    url = f'https://webservice.livepix.gg/checkout/payment/{id_pagamento}'
    
    cabecalhos = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://checkout.livepix.gg',
        'referer': 'https://checkout.livepix.gg/'
    }
    
    dados = {"method": "pix"}
    
    try:
        resposta = requests.post(url, headers=cabecalhos, json=dados)
        resposta.raise_for_status()
        return resposta.json()['code']
    except Exception as erro:
        print(f"Erro ao obter código PIX: {erro}")
        return None

# Pega o código Pix (Copia e Cola), converte para uma imagem png (Pix QR Code) e salva no diretório
def gerar_qrcode(codigo_pix, nome_arquivo='pagamento.png'):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(codigo_pix)
    qr.make(fit=True)
    
    imagem = qr.make_image(fill_color="black", back_color="white")
    imagem.save(nome_arquivo)
    return nome_arquivo

def base():
    # Obtém o token de acesso
    token = obter_token()
    if not token:
        return
    
    # Cria o pagamento
    resultado = criar_pagamento(token['access_token'])
    if resultado:
        print("Pagamento criado com sucesso!")
        print(f"URL de checkout: {resultado['data']['redirectUrl']}")
        
        # Extrai o ID do pagamento da URL de checkout
        id_pagamento = resultado['data']['redirectUrl'].split('/')[-1]
        
        # Aguarda um momento para garantir que o pagamento foi processado
        time.sleep(1)
        
        # Obtém o código PIX
        codigo_pix = obter_codigo_pix(id_pagamento)
        if codigo_pix:
            # Gera o QR code
            arquivo_qr = gerar_qrcode(codigo_pix)
            print(f"QR Code gerado com sucesso: {arquivo_qr}")
            print("\nPIX Copia e Cola:")
            print(f"{codigo_pix}\n")

if __name__ == '__main__':
    base()
