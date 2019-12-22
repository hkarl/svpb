"""
Define a command that should be run from a crontab.
Check offene oder Rueckfragen Leistungsmeldungen. 
Send an email to the person in charge. 
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.utils import translation
from django.conf import settings


from post_office import mail

import arbeitsplan.models as models

import datetime
import pprint

from collections import defaultdict

class Command(BaseCommand):
    """Go through all Leistungen that have not been 
    processed by verantwortlicher. 
    """

    args = ""
    help = "Send out Reminders that Leistungsmeldungen should be processed."
    emailTemplate = "leistungReminder"

    def handle(self, *args, **options):
        # set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        offeneLeistungen = (models.Leistung.objects.
                            filter(
                                erstellt__lte=datetime.date.today()-datetime.timedelta(days=7)).
                            exclude(
                                status=models.Leistung.ACK).
                            exclude(
                                status=models.Leistung.NEG)
                            )

        print(offeneLeistungen)
        kontakte = {l.aufgabe.kontakt() for l in offeneLeistungen}

        print(kontakte)
        
        for k in kontakte: 
            mail.send(
                [k.email], # to address
                template="leistungReminder",
            )

        call_command('send_queued_mail')

        translation.deactivate()
