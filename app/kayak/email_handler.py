import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from pathlib import Path

# Carrega as variáveis de ambiente do arquivo .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
EMAIL_DESTINO = os.getenv('EMAIL_DESTINO')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

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
