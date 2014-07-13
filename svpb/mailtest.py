import smtplib
import emailSettings

server = smtplib.SMTP_SSL (emailSettings.EMAIL_HOST)
server.set_debuglevel(1)
server.login(emailSettings.EMAIL_HOST_USER,
             emailSettings.EMAIL_HOST_PASSWORD)
server.sendmail(emailSettings.DEFAULT_FROM_EMAIL,
                "holger.karl@uni-paderborn.de",
                "test von SVPB blab bla"
                )
