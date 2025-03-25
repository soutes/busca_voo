import time
import datetime
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from bs4 import BeautifulSoup
import os
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
    urls = []
    data_inicio_ida = datetime.datetime.strptime(data_inicio_ida, "%Y-%m-%d")
    data_fim_ida = datetime.datetime.strptime(data_fim_ida, "%Y-%m-%d")
    
    while data_inicio_ida <= data_fim_ida:
        for destino in destinos:
            data_str_ida = data_inicio_ida.strftime("%Y-%m-%d")
            url = base_url.replace("{destino}", destino).replace("{data_inicio_ida}", data_str_ida)
            urls.append((url, destino))
        
        data_inicio_ida += datetime.timedelta(days=1)

    return urls

# Função de processamento e envio de email
def enviar_email(url, price):
    msg = MIMEMultipart()
    subject = f"Retorno Paris por - {price}"
    message = f"Retorno Paris por {price}<br><br>Link: <a href='{url}'>{url}</a>"
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

# Função de processamento da URL para Kayak
def processar_url_kayak(url, destino, driver, logs_by_dest, min_prices):
    print("Processando URL no Kayak:", url)
    driver.get(url)
    sleep(50)  # Aguarda 30 segundos para a página carregar
    wait = WebDriverWait(driver, 60)
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

# Função de processamento para Skiplagged
def processar_url_skiplagged(url, destino, driver, logs_by_dest, min_prices):
    print("Processando URL no Skiplagged:", url)
    driver.get(url)
    sleep(33)  # Aguarda 3 segundos para a página carregar
    
    wait = WebDriverWait(driver, 60)  # Aumenta o tempo de espera
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "trip-cost-small")))
    except Exception as e:
        print(f"Erro ao esperar o elemento na URL {url}: {e}")
        return None, None

    content = driver.page_source
    soup = BeautifulSoup(content, 'html.parser')
    
    price_divs = soup.find_all(class_="trip-cost-small")
    
    if not price_divs:
        print(f"Preço não encontrado na URL: {url}")
        return None, None
    
    for price_div in price_divs:
        price_span = price_div.find_next("span")
        if price_span:
            price_text = price_span.get_text(strip=True)
            print(f"Preço encontrado no Skiplagged na URL {url}: {price_text}")
            email_price = price_text  # Exemplo: "R$ 4.772"
            
            clean_price_str = price_text.replace('R$', '').replace('.', '').strip()
            timestamp = datetime.datetime.now()

            try:
                numeric_price = int(clean_price_str)
            except Exception as e:
                print(f"Erro ao converter o preço '{clean_price_str}' para inteiro para na URL {url}: {e}")
                return None, None

            if destino not in logs_by_dest:
                logs_by_dest[destino] = []

            if destino not in min_prices or numeric_price < min_prices[destino]:
                min_prices[destino] = numeric_price
                logs_by_dest[destino].append({
                    "timestamp": timestamp,
                    "price": numeric_price,
                    "url": url
                })
                print(f"Novo preço mais barato registrado para {destino} em {timestamp}: {numeric_price}")
            else:
                print(f"Preço {numeric_price} não é o menor para {destino}, mas será registrado.")

            logs_by_dest[destino].append({
                "timestamp": timestamp,
                "price": numeric_price,
                "url": url
            })

            return email_price, numeric_price
    
    return None, None

# Função de exportação para CSV
def export_logs_to_csv(logs_by_dest, filename="Retorno_Paris_Skiplaged.csv"):
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
    logs_by_dest = {}
    min_prices = {}  # Armazena o preço mais barato para cada destino
    
    base_url_kayak = "https://www.kayak.com.br/flights/{destino}/{data_inicio_ida}?sort=price_a"
    base_url_skiplagged = "https://skiplagged.com/flights/{destino}/{data_inicio_ida}"

    destinos_ida_kayak = ["ORY-FLN", "ORY-SAO"]
    destinos_ida_skiplagged = ["PAR/sao-paulo", "PAR/FLN"]
    
    # Geração das URLs com datas dinâmicas para o intervalo de datas de ida
    urls_ida_kayak = gerar_urls(base_url_kayak, destinos_ida_kayak, "2025-08-29", "2025-09-01")
    urls_ida_skiplagged = gerar_urls(base_url_skiplagged, destinos_ida_skiplagged, "2025-08-29", "2025-09-01")

    while True:
        print("Iniciando ciclo de pesquisa para Kayak:", datetime.datetime.now())
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Processa as URLs do Kayak
        for url, destino in urls_ida_kayak:
            email_price, numeric_price = processar_url_kayak(url, destino, driver, logs_by_dest, min_prices)
            if email_price is None or numeric_price is None:
                continue
            try:
                if numeric_price <= 2500:
                    enviar_email(url, email_price)
            except Exception as e:
                print(f"Erro ao processar o valor para a URL {url}: {e}")
        
        driver.quit()
        
        print("Aguardando 1 hora antes de processar o próximo site...")
        time.sleep(60)  # Aguarda 1 hora antes de processar o próximo site

        print("Iniciando ciclo de pesquisa para Skiplagged:", datetime.datetime.now())
        driver = webdriver.Chrome(options=chrome_options)
        
        # Processa as URLs do Skiplagged
        for url, destino in urls_ida_skiplagged:
            email_price, numeric_price = processar_url_skiplagged(url, destino, driver, logs_by_dest, min_prices)
            if email_price is None or numeric_price is None:
                continue
            try:
                if numeric_price <= 2500:
                    enviar_email(url, email_price)
            except Exception as e:
                print(f"Erro ao processar o valor para a URL {url}: {e}")
        
        driver.quit()
        
        # Exporta os dados coletados para CSV
        export_logs_to_csv(logs_by_dest)
        
        print("Ciclo finalizado. Aguardando 8 horas para o próximo ciclo.\n")
        time.sleep(28800)  # Aguarda 8 horas para o próximo ciclo

if __name__ == "__main__":
    main()
