import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from email_handler import enviar_email
from url_generator import gerar_urls
from price_processor_kayak import processar_url_kayak
from price_processor_skip import processar_url_skiplagged
from csv_exporter_kayak import export_logs_to_csv_kayak
from csv_exporter_skip import export_logs_to_csv_skiplagged

def processar_coleta(urls, driver, processador, logs_by_dest, min_prices, email_limit=2000):
    """
    Função genérica para processar as URLs, coletar os preços e enviar e-mails quando necessário.
    """
    for url, destino in urls:
        email_price, numeric_price = processador(url, destino, driver, logs_by_dest, min_prices)
        if email_price and numeric_price:
            if numeric_price <= email_limit:
                enviar_email(url, email_price)

def main():
    # Dicionários para armazenar logs e preços mínimos para Kayak e Skiplagged
    logs_by_dest_kayak = {}
    min_prices_kayak = {}  # Armazena o preço mais barato para cada destino no Kayak
    
    logs_by_dest_skiplagged = {}
    min_prices_skiplagged = {}  # Armazena o preço mais barato para cada destino no Skiplagged
    
    # Base URL com placeholders para as datas e destinos
    base_url_kayak = "https://www.kayak.com.br/flights/{destino}/{data_inicio_ida}?sort=price_a"
    base_url_skiplagged = "https://skiplagged.com/flights/{destino}/{data_inicio_ida}"

    # Lista de destinos para o Kayak e Skiplagged
    destinos_retorno_kayak = ["ORY-FLN", "ORY-SAO", "MAD-SAO", "MAD-FLN"]
    destinos_retorno_skiplagged = ["PAR/sao-paulo", "PAR/FLN", "MAD/sao-paulo", "MAD/FLN"]
    
    # Geração das URLs com datas dinâmicas para o intervalo de datas de ida
    urls_retorno_kayak_1 = gerar_urls(base_url_kayak, destinos_retorno_kayak, "2025-08-31", "2025-09-01")
    urls_retorno_kayak_2 = gerar_urls(base_url_kayak, destinos_retorno_kayak, "2025-09-03", "2025-09-07")
    urls_retorno_skiplagged_1 = gerar_urls(base_url_skiplagged, destinos_retorno_skiplagged, "2025-08-31", "2025-09-01")
    urls_retorno_skiplagged_2 = gerar_urls(base_url_skiplagged, destinos_retorno_skiplagged, "2025-09-03", "2025-09-07")

    # Unindo as URLs geradas dos dois intervalos de datas
    urls_retorno_kayak = urls_retorno_kayak_1 + urls_retorno_kayak_2
    urls_retorno_skiplagged = urls_retorno_skiplagged_1 + urls_retorno_skiplagged_2

    while True:
        # Coletando dados do Kayak
        print("Iniciando ciclo de pesquisa para Kayak:", datetime.datetime.now())
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Processa as URLs de Kayak
        processar_coleta(urls_retorno_kayak, driver, processar_url_kayak, logs_by_dest_kayak, min_prices_kayak)
        
        driver.quit()

        # Exporta os dados do Kayak
        export_logs_to_csv_kayak(logs_by_dest_kayak)

        # Intervalo entre o site Kayak e Skiplagged
        print("Aguardando 1 minuto antes de processar o Skiplagged...")
        time.sleep(60)

        # Coletando dados do Skiplagged
        print("Iniciando ciclo de pesquisa para Skiplagged:", datetime.datetime.now())
        driver = webdriver.Chrome(options=chrome_options)
        
        # Processa as URLs de Skiplagged
        processar_coleta(urls_retorno_skiplagged, driver, processar_url_skiplagged, logs_by_dest_skiplagged, min_prices_skiplagged)
        
        driver.quit()

        # Exporta os dados do Skiplagged
        export_logs_to_csv_skiplagged(logs_by_dest_skiplagged)
        
        print("Ciclo finalizado. Aguardando 8 horas para o próximo ciclo.\n")
        time.sleep(28800)  # Aguarda 8 horas para o próximo ciclo

if __name__ == "__main__":
    main()