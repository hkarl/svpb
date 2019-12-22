# -*- coding: utf-8 -*-


"""
Define a command to run at the end of a year. 
Goal: go over everybody registered in the second half of that year. 
Set the arbeitslast of those users to the default.

Notify the geschaeftsfuehere! 
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.utils import translation
from django.conf import settings

from django.core.mail import send_mail

import arbeitsplan.models as models

import datetime
import pprint


class Command(BaseCommand):

    args = ""
    help = "Set all new Mitglieder's Arbeitslast to standard value. New is anybody how joined in the second half of a year"

    def handle(self, *args, **options):
        thisyear = datetime.datetime.now().year
        midyear = datetime.datetime(thisyear, 7, 1)

        newmitglieder = models.Mitglied.objects.filter(
            user__date_joined__gte=midyear)

        for m in newmitglieder:
            m.arbeitlast = settings.JAHRESSTUNDEN
            m.save()

        # Mail:
        subject = "Arbeitsstunden neuer Mitglieder auf Jahressoll angepasst"
        to = ['hkarl@ieee.org', 'dieter.peitz@svpb.de']
        fromEmail = "mein@svpb.de"

        body = """
Für folgende Mitglieder wurden die Arbeitsstunden auf das Jahressoll gesetzt: 

{}

Ist das nicht korrekt, bitte die entsprechenden Mitglieder direkt in der Webseite editieren.

Rückfragen bitte an mein@svpb.de
        """.format('\n'.join(['- ' + m.__unicode__() for m in newmitglieder]))


        send_mail(subject,
                  body,
                  fromEmail,
                  to,
                  fail_silently=False)
        
