import time
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from bs4 import BeautifulSoup
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pathlib import Path

# Carrega as variáveis de ambiente do arquivo .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
EMAIL_DESTINO = os.getenv('EMAIL_DESTINO')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Função para gerar URLs com datas dinâmicas e destinos variáveis
def gerar_urls(base_url, destinos, data_inicio_ida, data_fim_ida):
    """
    Gera uma lista de URLs com datas variáveis entre 'data_inicio_ida' e 'data_fim_ida'
    para todos os destinos fornecidos.
    """
    urls = []
    # Convertendo as datas para objetos datetime
    data_inicio_ida = datetime.datetime.strptime(data_inicio_ida, "%Y-%m-%d")
    data_fim_ida = datetime.datetime.strptime(data_fim_ida, "%Y-%m-%d")
    
    # Gerando todas as datas para ida
    while data_inicio_ida <= data_fim_ida:
        for destino in destinos:
            # Formatar as datas como string no formato esperado pela URL
            data_str_ida = data_inicio_ida.strftime("%Y-%m-%d")

            # Gerar a URL com as datas para a ida
            url = base_url.replace("{destino}", destino).replace("{data_inicio_ida}", data_str_ida)
            urls.append((url, destino))  # Armazenando a URL e o destino
        
        # Avançar para o próximo dia
        data_inicio_ida += datetime.timedelta(days=1)

    return urls

# Função de processamento e envio de email
def enviar_email(url, price):
    msg = MIMEMultipart()
    subject = f"Pariu Europa - {price}"
    message = f"Pariu Europa - {price}<br><br>Link: <a href='{url}'>{url}</a>"
    msg['Subject'] = subject
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINO
    msg.add_header('Content-Type', 'text/html')
    msg.attach(MIMEText(message, 'html'))
    
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        s.sendmail(EMAIL_REMETENTE, [EMAIL_DESTINO], msg.as_string())
        s.quit()
        print(f"E-mail enviado para a URL: {url} com preço {price}")
    except Exception as e:
        print(f"Erro ao enviar e-mail para a URL {url}: {e}")

# Função de processamento da URL
def processar_url(url, destino, driver, logs_by_dest, min_prices):
    print("Processando URL:", url)
    driver.get(url)
    sleep(30)  # Aguarda 30 segundos para a página carregar
    wait = WebDriverWait(driver, 50)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Mais barato']")))
    except Exception as e:
        print(f"Erro ao esperar o elemento na URL {url}: {e}")
        return None, None

    content = driver.page_source
    soup = BeautifulSoup(content, 'html.parser')
    mais_barato_div = soup.find('div', attrs={'aria-label': 'Mais barato'})
    if not mais_barato_div:
        print(f"Div 'Mais barato' não encontrada na URL: {url}")
        return None, None

    price_span = mais_barato_div.find('span', string=lambda t: t and "R$" in t)
    if not price_span:
        print(f"Preço não encontrado na URL: {url}")
        return None, None

    # Valor original para e-mail
    price_text = price_span.get_text(strip=True)
    print(f"Preço encontrado na URL {url}: {price_text}")
    email_price = price_text  # Exemplo: "R$ 4.772"
    
    # Valor limpo para conversão e gráfico
    clean_price_str = price_text.replace('R$', '').replace('.', '').strip()
    timestamp = datetime.datetime.now()

    try:
        numeric_price = int(clean_price_str)
    except Exception as e:
        print(f"Erro ao converter o preço '{clean_price_str}' para inteiro para na URL {url}: {e}")
        return None, None

    # Inicializa o destino no dicionário se necessário
    if destino not in logs_by_dest:
        logs_by_dest[destino] = []

    # Verifica se o preço encontrado é o menor até agora para o destino
    if destino not in min_prices or numeric_price < min_prices[destino]:
        min_prices[destino] = numeric_price  # Atualiza o menor preço encontrado
        logs_by_dest[destino].append({
            "timestamp": timestamp,
            "price": numeric_price,
            "url": url
        })
        print(f"Novo preço mais barato registrado para {destino} em {timestamp}: {numeric_price}")
    else:
        print(f"Preço {numeric_price} não é o menor para {destino}, mas será registrado.")

    # Registra o preço atual, independentemente de ser o mais barato ou não
    logs_by_dest[destino].append({
        "timestamp": timestamp,
        "price": numeric_price,
        "url": url
    })

    return email_price, numeric_price

# Função de exportação para CSV
def export_logs_to_csv(logs_by_dest, filename="logs_coletados.csv"):
    all_logs = []
    for dest, log_list in logs_by_dest.items():
        for record in log_list:
            record_with_dest = record.copy()
            record_with_dest['destination'] = dest
            all_logs.append(record_with_dest)
    
    if not all_logs:
        print("Nenhum dado para exportar.")
        return
    
    df = pd.DataFrame(all_logs)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values('timestamp', inplace=True)
    
    # Verifica se o arquivo já existe
    if os.path.exists(filename):
        existing_df = pd.read_csv(filename, parse_dates=['timestamp'])
        df_combined = pd.concat([existing_df, df], ignore_index=True)
        df_combined.drop_duplicates(inplace=True)
        df_combined.sort_values('timestamp', inplace=True)
        df_combined.to_csv(filename, index=False)
        print(f"Dados combinados exportados para {filename}")
    else:
        df.to_csv(filename, index=False)
        print(f"Dados exportados para {filename}")

def main():
    # Dicionário para armazenar os logs agrupados por destino
    logs_by_dest = {}
    min_prices = {}  # Armazena o preço mais barato para cada destino
    
    # Base URL com placeholders para as datas e destinos
    base_url = "https://www.kayak.com.br/flights/{destino}/{data_inicio_ida}?sort=price_a"
    
    # Lista de destinos (para a ida)
    destinos_ida = ["FLN-MAD", "FLN-AMS", "FLN-LIS", "FLN-OPO", "FLN-ROM"]
    
    # Geração das URLs com datas dinâmicas para o intervalo de datas de ida
    urls_ida = gerar_urls(base_url, destinos_ida, "2025-04-18", "2025-04-22")
    
    # Lista de destinos invertida (para a volta)
    destinos_volta = ["MAD-FLN", "AMS-FLN", "LIS-FLN", "OPO-FLN", "ROM-FLN"]
    
    # Geração das URLs com datas dinâmicas para o intervalo de datas de volta
    urls_volta = gerar_urls(base_url, destinos_volta, "2025-04-30", "2025-05-05")

    while True:
        print("Iniciando ciclo de pesquisa para Ida:", datetime.datetime.now())
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Processa as URLs de ida
        for url, destino in urls_ida:
            email_price, numeric_price = processar_url(url, destino, driver, logs_by_dest, min_prices)
            if email_price is None or numeric_price is None:
                continue
            try:
                if numeric_price <= 2000:
                    enviar_email(url, email_price)
            except Exception as e:
                print(f"Erro ao processar o valor para a URL {url}: {e}")

        print("Aguardando 1 hora para a pesquisa de volta...")
        time.sleep(3600)  # Aguarda 1 hora antes de pesquisar a volta

        print("Iniciando ciclo de pesquisa para Volta:", datetime.datetime.now())

        # Processa as URLs de volta
        for url, destino in urls_volta:
            email_price, numeric_price = processar_url(url, destino, driver, logs_by_dest, min_prices)
            if email_price is None or numeric_price is None:
                continue
            try:
                if numeric_price <= 2000:
                    enviar_email(url, email_price)
            except Exception as e:
                print(f"Erro ao processar o valor para a URL {url}: {e}")

        driver.quit()
        
        # Exporta os dados coletados para CSV
        export_logs_to_csv(logs_by_dest)
        
        print("Ciclo finalizado. Aguardando 5 horas para o próximo ciclo.\n")
        time.sleep(18000)  # Aguarda 5 horas para o próximo ciclo

if __name__ == "__main__":
    main()
