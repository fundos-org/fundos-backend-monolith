import smtplib, ssl
from email.message import EmailMessage
port = 587
smtp_server = "smtp.zeptomail.in"
username="emailapikey"
password = "PHtE6r0IQe26iWB59BQG7KC7Q8akM417r7k2JFYVt9tKC/cGTE0A+o95m2TmoxwrUPATRvbOydhqs+uV4b3TIW7qND5IXWqyqK3sx/VYSPOZsbq6x00btVkSdUzbU47vctZp3CHRudffNA=="
message = "Test email sent successfully."
msg = EmailMessage()
msg['Subject'] = "Test Email"
msg['From'] = "noreply@fundos.solutions"
msg['To'] = "legal@fundos.solutions"
msg.set_content(message)
try:
    if port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(username, password)
            server.send_message(msg)
    elif port == 587:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
    else:
        print ("use 465 / 587 as port value")
        exit()
    print ("successfully sent")
except Exception as e:
    print (e)