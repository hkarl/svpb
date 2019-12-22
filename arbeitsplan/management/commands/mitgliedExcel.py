# -*- coding: utf-8 -*-

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
from django.db import models

import arbeitsplan.models as ap_models

import datetime
import pprint
import os 

import xlsxwriter
from xlsxcursor import XlsxCursor

def get_attribute(instance, name):
    """helper function: getattr does not follow foreign keys; 
    this version here does. 
    """
    
    if hasattr(instance, name):
        return getattr(instance, name)

    names = name.split('__')
    name = names.pop(0)
    if len(names) == 0:
        return ''

    if hasattr(instance, name):
        value = getattr(instance, name)
        return get_attribute(value, '__'.join(names))

    return ''


class Command(BaseCommand):
    """Produce an Excel file of all the Mitglieder. 
    With differnt filters applied. 
    """
    args = ""
    help = "Produce excel file of all Mitglieder"


    def ExcelExport(self, qs, cursor, mod=None):
        """Turn a query set into an Excel sheet. 
        """

        if not mod:
            mod = qs.model

        for (fieldname, fieldkey) in mod.excelFields:
            cursor(fieldname)

        cursor("Noch zu leistende Stunden")
        cursor.cr()

        row = 2
        for r in qs:
            for  (fieldname, fieldkey) in mod.excelFields:
                a = get_attribute(r, fieldkey)
                if hasattr(a, '__call__'):
                    a = a()
                cursor(a)
            cursor("=MAX(0,J{}-R{})".format(row, row))
            cursor.cr()
            row += 1 
            
        return None

    def createSheet (self, workbook, name, qs, mod=None):
        sheet = workbook.add_worksheet(name)
        sheet.set_column(0, 20, 15)
        cursor = XlsxCursor (workbook, sheet)
        self.ExcelExport(qs,
                         cursor,
                         mod)


    def uebersichtsblatt(self, workbook):
        # Uebersichtsblatt
        uebersicht = workbook.add_worksheet('Uebersicht')
        uebersicht.set_column(0, 0, 30)
        uebersicht.set_column(1, 3, 60)
        cursor = XlsxCursor(workbook, uebersicht)
        cursor("Übersicht der einzelnen Kategorien")
        cursor.cr()
        cursor.cr()
        cursor("Alle Mitglieder")
        cursor("Kein Filter")
        cursor.cr()
        cursor("Aktive Mitglieder")
        cursor("Mitglieder, die sich mind. 1x angemeldet haben")
        cursor.cr()
        
        cursor("Inaktive Mitglieder")        
        cursor("Mitglieder, die sich noch nicht angemeldet haben")
        cursor.cr()
        
        cursor("Aktive, ohne Meldung")        
        cursor("Angemeldet, aber keine Meldung abgegeben")        
        cursor("Nicht unbedingt eine Problem; z.B. für Mitglieder die direkt eingeteilt wurden")        
        cursor.cr()
        
        cursor("Aktive, ohne Zuteilung")        
        cursor("Angmeldet, aber keine Aufgabe wurde zugeteilt")        
        cursor("Bedenklich (selbst Schnellzuweisung erstellt Zuweisung). Sollte zugeteilt werden!")        
        cursor.cr()
        
        cursor("Aktive, weder Meldung,Zuteilung")        
        cursor("Angemeldet, aber weder Meldung abgeben noch Zuteilung erfolgt.")        
        cursor("Sehr bedenklich. Braucht Rücksprache, falls Arbeitslast.")        
        cursor.cr()
        
        cursor("Ruecksprache")        
        cursor("Mitglieder mit Arbeitslast (egal ob aktiv oder nicht), ohne Meldung, ohne Zuteilung. ")
        cursor("Problemfälle! Die müssen was tun, haben es gibt keine Aufgabe. Brauchen Rücksprache und Ermunterung!")
        cursor.cr()

        cursor("Abkassieren")
        cursor("Mitglieder, deren Arbeitslast größer ist als die akzeptierten geleisteten Stunden")
        cursor("Am Jahresende sind das die Mitglieder, von denen Geld abgebucht werden muss.")
        cursor.cr()
        
        return
        
    def handle(self, *args, **options):
        # set the locale right, to get the dates represented correctly

        translation.activate(settings.LANGUAGE_CODE)

        # take all the Mitglieder, first

        workbook = xlsxwriter.Workbook(os.path.join(
            settings.SENDFILE_ROOT,
            'mitglieder.xlsx'))

        self.uebersichtsblatt(workbook)
        
        # die einzelnen Inahlte: 
        self.createSheet(workbook,
                         'Alle Mitglieder',
                         ap_models.Mitglied.objects.all())

        self.createSheet(workbook,
                         'Aktive Mitglieder',
                         ap_models.Mitglied.objects.filter(user__is_active=True)
                         )

        self.createSheet(workbook,
                         'Inaktive Mitglieder',
                         ap_models.Mitglied.objects.filter(user__is_active=False),
                         )

        self.createSheet(workbook,
                         'Aktive, ohne Meldung',
                         [m
                          for m in ap_models.Mitglied.objects.filter(user__is_active=True)
                          if m.gemeldeteAnzahlAufgaben() == 0],
                          ap_models.Mitglied                          
                         )
                
        self.createSheet(workbook,
                         'Aktive, ohne Zuteilung',
                         [m
                          for m in ap_models.Mitglied.objects.filter(user__is_active=True)
                          if m.zugeteilteAufgaben() == 0],
                          ap_models.Mitglied                          
                         )

        self.createSheet(workbook,
                         'Aktive, weder Meldung,Zuteilung',
                         [m
                          for m in ap_models.Mitglied.objects.filter(user__is_active=True)
                          if (m.gemeldeteAnzahlAufgaben() == 0 and
                              m.zugeteilteAufgaben() == 0)], 
                         ap_models.Mitglied                          
                         )

        self.createSheet(workbook,
                         'Ruecksprache',
                         [m
                          for m in ap_models.Mitglied.objects.all()
                          if (m.gemeldeteAnzahlAufgaben() == 0 and
                              m.zugeteilteAufgaben() == 0 and
                              m.arbeitslast > 0)], 
                         ap_models.Mitglied                          
                         )

        self.createSheet(workbook,
                         'Abkassieren',
                         [m
                          for m in ap_models.Mitglied.objects.all()
                          if (m.arbeitslast > m.akzeptierteStunden())], 
                         ap_models.Mitglied                          
                         )

        workbook.close()
        
        # send_mail(subject,
        #           body,
        #           "mein@svpb.de",
        #           ['holger.karl@uni-paderborn.de'],
        #           fail_silently=False)


        translation.deactivate()
