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
from typing import Optional, Tuple, Dict

# Carrega as variáveis de ambiente do arquivo .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
EMAIL_DESTINO = os.getenv('EMAIL_DESTINO')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Função para gerar URLs com datas dinâmicas e destinos variáveis
def gerar_urls(base_url: str, destinos: list, data_inicio_ida: str, data_fim_ida: str) -> list:
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

# Função de envio de email
def enviar_email(url: str, price: str) -> None:
    msg = MIMEMultipart()
    subject = f"Retorno Paris por - {price}"
    message = f"Retorno Paris por {price}<br><br>Link: <a href='{url}'>{url}</a>"
    msg['Subject'] = subject
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINO
    msg.add_header('Content-Type', 'text/html')
    msg.attach(MIMEText(message, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
            s.sendmail(EMAIL_REMETENTE, [EMAIL_DESTINO], msg.as_string())
        print(f"E-mail enviado para a URL: {url} com preço {price}")
    except Exception as e:
        print(f"Erro ao enviar e-mail para a URL {url}: {e}")

# Função de processamento da URL para Kayak
def processar_url_kayak(url: str, destino: str, driver: webdriver.Chrome, logs_by_dest: Dict[str, list], min_prices: Dict[str, int]) -> Optional[Tuple[str, int]]:
    """Processa a URL do Kayak e extrai o preço."""
    print("Processando URL no Kayak:", url)
    driver.get(url)
    sleep(20)  # Aguarda 3 segundos para a página carregar
    
    try:
        wait = WebDriverWait(driver, 120)
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

    # Preço limpo
    price_text = price_span.get_text(strip=True)
    print(f"Preço encontrado na URL {url}: {price_text}")
    
    clean_price_str = price_text.replace('R$', '').replace('.', '').strip()
    try:
        numeric_price = int(clean_price_str)
    except ValueError:
        print(f"Erro ao converter o preço '{clean_price_str}' para inteiro")
        return None, None

    # Registro de preço
    if destino not in logs_by_dest:
        logs_by_dest[destino] = []

    if destino not in min_prices or numeric_price < min_prices[destino]:
        min_prices[destino] = numeric_price
        logs_by_dest[destino].append({"timestamp": datetime.datetime.now(), "price": numeric_price, "url": url})

    return price_text, numeric_price

# Função de processamento para Skiplagged
def processar_url_skiplagged(url: str, destino: str, driver: webdriver.Chrome, logs_by_dest: Dict[str, list], min_prices: Dict[str, int]) -> Optional[Tuple[str, int]]:
    """Processa a URL do Skiplagged e extrai o preço."""
    print("Processando URL no Skiplagged:", url)
    driver.get(url)
    sleep(20)  # Aguarda 3 segundos para a página carregar
    
    wait = WebDriverWait(driver, 60)
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
            clean_price_str = price_text.replace('R$', '').replace('.', '').strip()
            try:
                numeric_price = int(clean_price_str)
            except ValueError:
                print(f"Erro ao converter o preço '{clean_price_str}' para inteiro")
                return None, None

            if destino not in logs_by_dest:
                logs_by_dest[destino] = []

            if destino not in min_prices or numeric_price < min_prices[destino]:
                min_prices[destino] = numeric_price
                logs_by_dest[destino].append({"timestamp": datetime.datetime.now(), "price": numeric_price, "url": url})

            return price_text, numeric_price
    
    return None

# Função de exportação para CSV
def export_logs_to_csv(logs_by_dest_kayak: Dict[str, list], logs_by_dest_skiplagged: Dict[str, list], kayak_filename: str = "kayak_logs.csv", skiplagged_filename: str = "skiplagged_logs.csv") -> None:
    # Exportando os logs do Kayak
    all_logs_kayak = []
    for dest, log_list in logs_by_dest_kayak.items():
        for record in log_list:
            record_with_dest = record.copy()
            record_with_dest['destination'] = dest
            record_with_dest['source'] = 'Kayak'  # Adiciona a origem (Kayak)
            all_logs_kayak.append(record_with_dest)

    if all_logs_kayak:
        df_kayak = pd.DataFrame(all_logs_kayak)
        df_kayak['timestamp'] = pd.to_datetime(df_kayak['timestamp'])
        df_kayak.sort_values('timestamp', inplace=True)
        df_kayak.to_csv(kayak_filename, index=False)
        print(f"Dados do Kayak exportados para {kayak_filename}")

    # Exportando os logs do Skiplagged
    all_logs_skiplagged = []
    for dest, log_list in logs_by_dest_skiplagged.items():
        for record in log_list:
            record_with_dest = record.copy()
            record_with_dest['destination'] = dest
            record_with_dest['source'] = 'Skiplagged'  # Adiciona a origem (Skiplagged)
            all_logs_skiplagged.append(record_with_dest)

    if all_logs_skiplagged:
        df_skiplagged = pd.DataFrame(all_logs_skiplagged)
        df_skiplagged['timestamp'] = pd.to_datetime(df_skiplagged['timestamp'])
        df_skiplagged.sort_values('timestamp', inplace=True)
        df_skiplagged.to_csv(skiplagged_filename, index=False)
        print(f"Dados do Skiplagged exportados para {skiplagged_filename}")

def main():
    logs_by_dest_kayak = {}
    min_prices_kayak = {}
    logs_by_dest_skiplagged = {}
    min_prices_skiplagged = {}
    
    base_url_kayak = "https://www.kayak.com.br/flights/{destino}/{data_inicio_ida}?sort=price_a"
    base_url_skiplagged = "https://skiplagged.com/flights/{destino}/{data_inicio_ida}"

    destinos_ida_kayak = ["ORY-FLN", "ORY-SAO"]
    destinos_ida_skiplagged = ["PAR/sao-paulo", "PAR/FLN"]
    
    urls_ida_kayak = gerar_urls(base_url_kayak, destinos_ida_kayak, "2025-08-29", "2025-09-01")
    urls_ida_skiplagged = gerar_urls(base_url_skiplagged, destinos_ida_skiplagged, "2025-08-29", "2025-09-01")

    while True:
        # Coletando dados do Kayak
        print("Iniciando ciclo de pesquisa para Kayak:", datetime.datetime.now())
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=chrome_options)
        
        for url, destino in urls_ida_kayak:
            email_price, numeric_price = processar_url_kayak(url, destino, driver, logs_by_dest_kayak, min_prices_kayak)
            if email_price and numeric_price:
                if numeric_price <= 2500:
                    enviar_email(url, email_price)
        
        driver.quit()
        
        # Intervalo entre o site Kayak e Skiplagged
        print("Aguardando 1 minuto antes de processar o Skiplagged...")
        time.sleep(60)
        
        # Coletando dados do Skiplagged
        print("Iniciando ciclo de pesquisa para Skiplagged:", datetime.datetime.now())
        driver = webdriver.Chrome(options=chrome_options)
        
        for url, destino in urls_ida_skiplagged:
            email_price, numeric_price = processar_url_skiplagged(url, destino, driver, logs_by_dest_skiplagged, min_prices_skiplagged)
            if email_price and numeric_price:
                if numeric_price <= 2500:
                    enviar_email(url, email_price)
        
        driver.quit()
        
        # Exporta os dados coletados para CSV
        export_logs_to_csv(logs_by_dest_kayak, logs_by_dest_skiplagged)
        
        print("Ciclo finalizado. Aguardando 8 horas para o próximo ciclo.\n")
        time.sleep(28800)  # Aguarda 8 horas para o próximo ciclo

if __name__ == "__main__":
    main()
