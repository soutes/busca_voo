import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from email_handler import enviar_email
from url_generator import gerar_urls
from price_processor import processar_url
from csv_exporter import export_logs_to_csv

def main():
    logs_by_dest = {}
    min_prices = {}  # Armazena o preço mais barato para cada destino
    
    # Base URL com placeholders para as datas e destinos
    base_url = "https://www.kayak.com.br/flights/{destino}/{data_inicio_ida}?sort=price_a"
    
    # Lista de destinos (para a ida)
    destinos_ida = ["ORY-FLN", "ORY-SAO", "LIS-SAO", "LIS-FLN", "OPO-SAO"]
    
    # Geração das URLs com datas dinâmicas para o intervalo de datas de ida
    urls_ida = gerar_urls(base_url, destinos_ida, "2025-08-22", "2025-08-26")

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

        driver.quit()
        
        # Exporta os dados coletados para CSV
        export_logs_to_csv(logs_by_dest)
        
        print("Ciclo finalizado. Aguardando 5 horas para o próximo ciclo.\n")
        time.sleep(18000)  # Aguarda 5 horas para o próximo ciclo

if __name__ == "__main__":
    main()
