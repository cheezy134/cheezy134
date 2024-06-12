import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

def send_email(sender_email, receiver_email, subject, body, smtp_server, smtp_port, login, password):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(login, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
