"""
Run year-end work statistics
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation
from django.db.models import Sum, Count

import arbeitsplan.models as models


class Command(BaseCommand):
    """Go through all Users and Aufgaben.
    Check whether at most one Meldung exist.
    """

    args = ""
    help = "Produce statistics for yearly analysis"

    def handle(self, *args, **options):
        # set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)

        # Leistungen

        with open('leistungen.csv', 'w') as csvfile:
            csvfile.write('#AufgabeNr, Aufgabe, Gruppe, Angefordert(h), Geleistet(h), #Personen\n')
            l = models.Leistung.objects.values('aufgabe','aufgabe__aufgabe',
                                               'aufgabe__anzahl','aufgabe__stunden',
                                               'aufgabe__gruppe__gruppe')\
                .annotate(geleistet=Sum('zeit'))\
                .annotate(melder=Count('melder', distinct=True))

            # self.stdout.write('#'.join(['{}-{}'.format(x[0], x[1]) for x in l[0].items()]))

            for ll in l:
                csvfile.write('{},{},{},{},{},{}\n'.format(
                    ll['aufgabe'],
                    ll['aufgabe__aufgabe'].encode('utf8'),
                    ll['aufgabe__gruppe__gruppe'].encode('utf8'),
                    ll['aufgabe__anzahl'] * ll['aufgabe__stunden'],
                    int(ll['geleistet']),
                    ll['melder'],
                ))



        translation.deactivate()
