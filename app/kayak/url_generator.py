import datetime

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
