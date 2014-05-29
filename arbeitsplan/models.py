# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
import datetime


# Create your models here.


class Mitglied (models.Model):
    user = models.OneToOneField(User)
    mitgliedsnummer = models.CharField(max_length = 10,
                                       help_text = "Mitgliedsnummer",
                                       default = 0)
    leistungbenachrichtigung = models.DateTimeField(help_text="Wann war die letzte Benachrichtigung zu einer Leistungsmeldung?",
                                                    default=datetime.datetime(1900,1,1))
    zuteilungsbenachrichtigung  = models.DateTimeField (help_text="Wann war die letzte Benachrichtigung zu einer Zuteilung?",
                                                        default=datetime.datetime(1900,1,1))

    def __unicode__ (self):
        return self.user.__unicode__()

class Aufgabengruppe (models.Model):
    gruppe = models.CharField (max_length=30,
                               help_text="Aussagefähiger Name für Gruppe von Aufgaben")
    verantwortlich = models.ForeignKey (User,
                                        help_text="Verantwortliches Vorstandsmitglied") 
    bemerkung = models.TextField(blank=True)

    def __unicode__ (self):
        return self.gruppe

    class Meta:
        verbose_name_plural = "Aufgabengruppen"
        verbose_name = "Aufgabengruppe"
    
class Aufgabe (models.Model):
    aufgabe = models.CharField (max_length=30)
    verantwortlich = models.ForeignKey (User,
                                        help_text="Verantwortliches Vorstandsmitglied")
    gruppe = models.ForeignKey (Aufgabengruppe)
    anzahl = models.IntegerField (default = 0,
                                  help_text="Wieviele Personen werden für diese Aufgabe gebraucht?")
    stunden = models.IntegerField (default = 0,
                                   help_text="Wieviele Stunden Arbeit pro Person?")
    
    datum = models.DateField (blank=True, null=True,
                              help_text="Wann fällt die Aufgabe an? (keine Angabe möglich)")

    bemerkung = models.TextField(blank=True)

    def __unicode__ (self):
        return self.aufgabe

    class Meta:
        verbose_name_plural = "Aufgaben"
        verbose_name = "Aufgabe"

class Stundenplan (models.Model):
    aufgabe = models.ForeignKey (Aufgabe)
    uhrzeit = models.IntegerField (help_text="Beginn")
    anzahl = models.IntegerField (default= 0,
                                  help_text="Wieviele Personen werden um diese Uhrzeit benötigt?")

    startZeit = 8
    stopZeit = 23
    
    def __unicode__ (self):
        return self.aufgabe.__unicode__() + "@" + str(self.uhrzeit) + ": " + str(self.anzahl)
    
    class Meta:
        verbose_name_plural = "Stundenpläne" 
        verbose_name = "Stundenplan" 
    
class Meldung (models.Model):
    erstellt = models.DateField (auto_now_add=True)
    veraendert = models.DateField (auto_now=True)
    melder = models.ForeignKey (User)
    aufgabe = models.ForeignKey (Aufgabe)

    GARNICHT = -1 
    WENNSMUSS = 0
    NORMAL = 1
    GERNE = 2

    PRAEFERENZ = (
        (GARNICHT, "Nein"), 
        (WENNSMUSS, "Wenn es sein muss"),
        (NORMAL, "Ok" ),
        (GERNE, "Gerne!"),
        )

    PRAEFERENZButtons = {
        GARNICHT: 'btn-default', # 'btn-mydefault', 
        GERNE: 'btn-default', # 'btn-mysuccess',
        NORMAL: 'btn-default', # 'btn-info', 
        WENNSMUSS: 'btn-default', # 'btn-mywarning', 
        }

    MODELDEFAULTS = {'prefMitglied': GARNICHT,
                     'prefVorstand': NORMAL,
                     'bemerkung': '',
                     'bemerkungVorstand': '', 
                    }
    prefMitglied = models.IntegerField (choices = PRAEFERENZ,
                                        default = NORMAL,
                                        help_text="Haben Sie Vorlieben für diese Aufgabe?",)
    prefVorstand = models.IntegerField (choices = PRAEFERENZ,
                                        default = NORMAL,
                                        help_text = "Trauen Sie diesem Mitglied die Aufgabe zu?",)

    bemerkung = models.TextField (blank=True)
    bemerkungVorstand = models.TextField (blank=True)
    
    def __unicode__ (self):
        return (self.melder.__unicode__() + " ; " +
                self.aufgabe.__unicode__() + " ; " +
                (self.veraendert.strftime("%d/%m/%y")
                 if self.veraendert else "--") 
                )

    class Meta:
        verbose_name_plural = "Meldungen"
        verbose_name = "Meldung"


class Zuteilung (models.Model):
    aufgabe = models.ForeignKey (Aufgabe)
    ausfuehrer = models.ForeignKey (User)
    automatisch = models.BooleanField (default=False)
    
    class Meta:
        verbose_name_plural = "Zuteilungen"

    def __unicode__ (self):
        # print self.stundenzuteilung_set.all() 
        return (self.aufgabe.__unicode__() + ": " + self.ausfuehrer.__unicode__() 
                + (" @ " + ','.join([s.__unicode__() for s in self.stundenzuteilung_set.all()] ))
                # + ('@' + ','.join(self.StundenZuteilung_set.all().values('uhrzeit')))
                )
    
    class Meta:
        verbose_name_plural = "Zuteilungen"
        verbose_name = "Zuteilung"

class StundenZuteilung (models.Model):
    zuteilung = models.ForeignKey (Zuteilung)
    uhrzeit = models.IntegerField (blank=True, null=True)

    class Meta:
        verbose_name = "Zuteilung einer Stunde"
        verbose_name_plural = "Zuteilungen für einzelne Stunden"

    def __unicode__ (self):
        return str(self.uhrzeit) 

    
class Leistung (models.Model):
    melder = models.ForeignKey (User)
    aufgabe = models.ForeignKey (Aufgabe)
    erstellt = models.DateField (auto_now_add=True)
    veraendert = models.DateField (auto_now=True)
    wann = models.DateField (help_text="An welchem Tag haben Sie die Leistung erbracht?",
                             ) 
    zeit = models.DecimalField (max_digits=3,
                                decimal_places = 1,
                                help_text="Wieviel Zeit (in Stunden) haben Sie gearbeitet?", 
                                )
    auslagen = models.DecimalField (max_digits=6,
                                    decimal_places = 2,
                                    help_text = "Hatten Sie finanzielle Auslagen? Bitte Belege vorlegen!",
                                    default = 0, 
                                    ) 
    km = models.DecimalField (max_digits= 4,
                              decimal_places = 0,
                              help_text = "Hatten Sie Wegstrecken, für die Sie km-Vergütung erhalten?",
                              default = 0, 
                              )
    
    OFFEN =  'OF'
    ACK = 'AK'
    RUECKFRAGE = 'RU'
    NEG = 'NE'
    
    STATUS = (
        (OFFEN, 'Offen'), 
        (ACK, 'Akzeptiert'), 
        (RUECKFRAGE, 'Rückfrage'), 
        (NEG, 'Abgelehnt'), 
        )

    STATUSButtons = {
        OFFEN: 'btn-default', # 'btn-mydefault', 
        ACK: 'btn-default', # 'btn-mysuccess', 
        RUECKFRAGE: 'btn-default', # 'btn-mywarning', 
        NEG: 'btn-default', # 'btn-mydanger', 
        }
    status = models.CharField (max_length=2,
                               choices = STATUS,
                               default = OFFEN) 
    
    bemerkung = models.TextField (blank=True)
    bemerkungVorstand = models.TextField (blank=True,
                                          verbose_name="Bemerkung Vorstand")
            
    class Meta:
        verbose_name_plural = "Leistungen"
        verbose_name = "Leistung"

    def __unicode__ (self):
        return (self.melder.__unicode__() + " ; " +
                self.aufgabe.__unicode__() + " ; " +
                (self.veraendert.strftime("%d/%m/%y")
                 if self.veraendert else "--") 
                )

