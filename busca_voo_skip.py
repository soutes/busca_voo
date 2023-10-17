from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import os
import smtplib
import email.message
from dotenv import load_dotenv
from pathlib import Path 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


driver=webdriver.Chrome()
url = 'https://skiplagged.com/flights/FLN/madrid/2024-04-06'
driver.get(url)
sleep(20)


content = driver.page_source
soup = BeautifulSoup(content)


for span in soup.findAll('span',attrs={'class':'span2 trip-cost'}):
    price = span.text[-4:]


temp_price = soup.find("div", {"class": "span2 trip-cost"})
price = temp_price.find("span", {"class": ""})
lst_price = []
lst_price.append(price.text)


lista_limpa = lst_price
lista_limpa = [w.replace('R$\xa0', '') for w in lista_limpa]
lista_limpa = [w.replace('.', '') for w in lista_limpa]
menor_preco = lista_limpa[0]
print(menor_preco)


def enviar_email():
    msg = MIMEMultipart()
            
    message = "Voo por R$ "+str(menor_preco)+ "\n\n no link "+str(url);

    env_path = Path('.')/'.env'
    load_dotenv(dotenv_path = env_path)
            
    #msg = email.message.Message()
    msg['Subject'] = "Voo abaixo de 2k"
    msg['From'] = 'aqui vai o email remetente'
    msg['To'] = 'aqui vai o email destino'
    password = 'aqui vai a senha' 
    msg.add_header('Content-Type', 'text/html')
    #msg.set_payload(html )
            
    # add in the message body
    msg.attach(MIMEText(message, 'html'))

    s = smtplib.SMTP('smtp.gmail.com: 587')
    s.starttls()
    # Login Credentials for sending the mail
    s.login(msg['From'], password)
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.quit()


if int(menor_preco)<=2000:
    enviar_email()
    print("Email Enviado")
#driver.quit()
#sleep(50)

