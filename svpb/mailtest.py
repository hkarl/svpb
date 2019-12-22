import smtplib
from . import emailSettings

try: 
    server = smtplib.SMTP_SSL (emailSettings.EMAIL_HOST,
                               emailSettings.EMAIL_PORT,
                              )
except:
    server = smtplib.SMTP_SSL (emailSettings.EMAIL_HOST,)

server.set_debuglevel(1)

if emailSettings.EMAIL_USE_TLS:
    server.starttls()

server.login(emailSettings.EMAIL_HOST_USER,
             emailSettings.EMAIL_HOST_PASSWORD)
server.sendmail(emailSettings.DEFAULT_FROM_EMAIL,
                "holger.karl@uni-paderborn.de",
                "test von SVPB blab bla"
                )
