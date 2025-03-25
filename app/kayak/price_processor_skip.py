import datetime
from bs4 import BeautifulSoup
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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