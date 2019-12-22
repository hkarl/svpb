"""
Define a command that should be run from a crontab.
This one should check consistency of Meldungen:
at most one Meldung per Aufgabe, per User. 
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.utils import translation
from django.conf import settings

from django.core.mail import send_mail

import arbeitsplan.models as models

import datetime
import pprint

from collections import defaultdict

class Command(BaseCommand):
    """Go through all Users and Aufgaben.
    Check whether at most one Meldung exist.
    """

    args = ""
    help = "Check Meldung consistency, send out warning emails"
    emailTemplate = "upcomingJob"

    def handle(self, *args, **options):
        # set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        self.stdout.write('meldungConsistent: Checking on ' +
                          str(datetime.date.today()))

        inconsistent_users = defaultdict(list)

        for u in models.User.objects.all():
            for a in models.Aufgabe.objects.all():
                mqs = models.Meldung.objects.filter(melder=u, aufgabe=a)
                c = mqs.count()
                if c > 1:
                    inconsistent_users[u].append(a)

        print(inconsistent_users)

        if inconsistent_users:
            subject = "SVPB: PROBLEM with Meldungenkonsistenz"
            body = pprint.pformat(inconsistent_users)
        else:
            subject = "SVPB: Meldungen all good"
            body = "rechoice"

        send_mail(subject,
                  body,
                  "mein@svpb.de",
                  ['holger.karl@uni-paderborn.de'],
                  fail_silently=False)


        ## for kontakt, liste in kontaktKontext.iteritems():
        ##     if kontakt.email:
        ##         mail.send(
        ##             [kontakt.email],
        ##             template="upcomingJob-Kontakt",
        ##             context={'liste': liste,
        ##                      'verantwortlich': kontakt,
        ##                      },
        ##             )


        translation.deactivate()
