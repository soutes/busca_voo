
# Projeto: Buscador de Passagens Aéreas com Python

Este projeto utiliza **Ciência de Dados**, **Python** e **Web Scraping** para automatizar a busca de passagens aéreas e notificações por e-mail quando os preços caem abaixo de um valor predefinido. Utilizando bibliotecas como `requests`, `BeautifulSoup`, `Selenium`, entre outras, este código facilita a vida de quem quer economizar sem precisar ficar o tempo todo pesquisando manualmente.

## Como funciona

### Objetivo

O objetivo deste projeto é realizar buscas automáticas de passagens aéreas em sites como **Kayak** e **Skiplagged**, coletando os preços e enviando e-mails automaticamente quando uma passagem dentro do orçamento for encontrada.

O processo é realizado de maneira automatizada, utilizando Python e Web Scraping, com a execução do script de pesquisa a cada 8 horas.

### Como o código foi estruturado

O projeto é estruturado da seguinte forma:

- **app/kayak**: Contém o código principal e as funções auxiliares.
  - **main_kayak_skip.py**: Código principal que executa as buscas, coleta os preços e envia e-mails com as passagens encontradas.
  - **email_handler.py**: Função para envio de e-mails
  - **url_generator.py**: Função para gerar URLs de pesquisa
  - **price_processor_kayak.py**: Função para processar os preços no Kayak
  - **price_processor_skip.py**: Função para processar os preços no Skiplagged
  - **csv_exporter_kayak.py**: Função para exportar logs do Kayak
  - **csv_exporter_skip.py**: Função para exportar logs do Skiplagged

### Funcionalidades principais

1. **Busca de preços**: O código acessa os sites de busca de passagens e coleta os preços de diferentes datas de viagem.
2. **Comparação de preços**: Compara o preço encontrado com o valor limite pré-definido.
3. **Notificação por e-mail**: Caso o preço caia abaixo do valor desejado, o código envia automaticamente um e-mail.
4. **Armazenamento dos dados**: Todos os dados coletados (preços, timestamps e URLs) são armazenados em logs e exportados para arquivos CSV.
5. **Automatização**: A coleta de preços e envio de e-mails ocorre a cada 8 horas de forma automatizada, sem necessidade de intervenção manual.

## Estrutura do Repositório

```bash
├── app
│   └── kayak
│       ├── main_kayak_skip.py        # Código principal de busca de passagens e envio de e-mails
│       ├── email_handler.py          # Função para envio de e-mails
│       ├── url_generator.py          # Função para gerar URLs de pesquisa
│       ├── price_processor_kayak.py  # Função para processar os preços no Kayak
│       ├── price_processor_skip.py   # Função para processar os preços no Skiplagged
│       ├── csv_exporter_kayak.py    # Função para exportar logs do Kayak
│       ├── csv_exporter_skip.py     # Função para exportar logs do Skiplagged
├── README.md                        # Documentação do projeto
├── .gitignore                       # Arquivo para ignorar arquivos não desejados no Git
└── outros arquivos de imagem e dados  # Imagens e dados de exemplo
```

## Como usar

1. **Clone o repositório**:

```bash
git clone https://github.com/soutes/busca_voo.git
cd busca_voo
```

2. **Instale as dependências**:

Este projeto utiliza **Poetry** para gerenciar dependências. Caso não tenha o Poetry instalado, você pode instalá-lo com o comando:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Depois, instale as dependências do projeto:

```bash
poetry install
```

3. **Executar o código**:

Você pode rodar o código executando o script `main_kayak_skip.py` diretamente:

```bash
poetry run python app/kayak/main_kayak_skip.py
```

Isso iniciará a coleta de dados e notificações automáticas conforme o código for executado.

4. **Configuração de E-mail**:

Certifique-se de que você tenha configurado corretamente as variáveis de ambiente para o envio de e-mails (utilizando um serviço como o Gmail). As variáveis necessárias são:

- `EMAIL_REMETENTE`: Seu e-mail de remetente.
- `EMAIL_DESTINO`: O e-mail de destino para o qual as notificações serão enviadas.
- `EMAIL_PASSWORD`: A senha ou chave de aplicativo para autenticação no seu e-mail.

## Exemplo de código

Aqui está um exemplo de como o código funciona:

```python
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

    price_text = price_span.get_text(strip=True)
    if numeric_price <= 2000:
        enviar_email(url, email_price)
```
