import datetime
from bs4 import BeautifulSoup
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    # Registra o preço atual, independente de ser o mais barato ou não
    logs_by_dest[destino].append({
        "timestamp": timestamp,
        "price": numeric_price,
        "url": url
    })

    return email_price, numeric_price
