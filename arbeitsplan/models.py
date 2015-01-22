# -*- coding: utf-8 -*-

"""Django models for the Arbeitsplan at SVPB.

Main classes:

* :class:`Mitglied`: 1on1 with User, provides Vereins unique ID and dates of
  messages sent to User
* :class:`Aufgabe` : Describes a single task
* :class:`Aufgabengruppe` : Grouping :class:`Aufgabe` together,
  with responsible Mitglied
* :class:`Stundenplan` : How many people are needed for a given Aufgabe at a
  given hour?
* :class:`Meldung` : Mitglied wants to contribute to a given Aufgabe
* :class:`Zuteilung` : a task has been assigned to a particular Mitglied
* :class:`StundenZuteilung`: a Zuteilung might pertain only to particular
  times; represented via this class
* :class:`Leistung` : Mitglied claims to have performaed a certain amount of
  work on a particular job
"""

from django.db import models
from django.contrib.auth.models import User

import datetime
# needed for auto_now fields with veto
from django.utils.timezone import utc


### patch the display of a user:

User.__unicode__ = lambda s: u"%s %s (Nr.: %s)" % (s.first_name,
                                                   s.last_name,
                                                   s.mitglied.mitgliedsnummer)



class Mitglied (models.Model):

    """Provide additional information on a User by a 1:1 relationship:
    ID, dates of messages

    This class is a one-to-one relationship with user, extending
    information stored about a particular user. It provides an
    additional mitgliedsnummer, corresponding to Vereins-Data.  It
    also stores date when a message has been last sent to a Mitglied
    and whether it is necessary to sent a message.

    It is not possible to derive necessity of messaging form date of
    last message - there simply might not have anything happened to
    this member since its last message.
    """

    excelFields = [
        ('Vorname', 'user__first_name'),
        ('Nachname', 'user__last_name'),
        ('M/W', 'gender'), 
        ('email', 'user__email'), 
        ('ID', 'mitgliedsnummer'),
        ('Strasse', 'strasse'), 
        ('PLZ', 'plz'), 
        ('Ort', 'ort'), 
        ('Status', 'status'), 
        ('Arbeitslast', 'arbeitslast'), 
        ('# Meldungen', 'gemeldeteAnzahlAufgaben'), 
        ('Stunden Meldungen ', 'gemeldeteStunden'), 
        ('# Zuteilungen', 'zugeteilteAufgaben'), 
        ('Stunden Zuteilungen', 'zugeteilteStunden'),
        ('', ''), 
    ]
    
    user = models.OneToOneField(User)
    """Couple Mitglied to User via 1:1 field."""

    mitgliedsnummer = models.CharField(max_length=10,
                                       help_text="Mitgliedsnummer",
                                       default=0)
    """ID as assigned by Verein. Unique?! Use this as default login."""

    zuteilungsbenachrichtigung = models.DateTimeField(
        help_text="Wann war die letzte Benachrichtigung"
        " zu einer Zuteilung?",
        default=datetime.datetime(1900, 1, 1),
        verbose_name="Letzte Benachrichtigung",
        )
    """Date and time of most recent message to user"""

    zuteilungBenachrichtigungNoetig = models.BooleanField(
        help_text="Muss an diese Nutzer"
        " eine Benachrichtigung"
        " wegen Änderung der "
        "Zuteilungen gesendet werden?",
        default=False,
        verbose_name="Benachrichtigung zu Zuteilungen nötig?",
        )
    """Does Mitglied need a message?"""

    zustimmungsDatum = models.DateTimeField(
        help_text="Wann hat der Nutzer Zustimmung erteilt?",
        default=datetime.datetime(1900, 1, 1),
        verbose_name="Datum der Zustimmung",
        )
    """At what date did the member agree to the use of this system?"""

    geburtsdatum = models.DateField(
        help_text="Geburtsdatum des Mitglieds",
        default=datetime.datetime(1900, 1, 1),
        verbose_name="Geburtstag",
        )

    strasse = models.CharField(max_length=50,
                               verbose_name="Strasse und Hausnummer",
                               default="")

    plz = models.DecimalField(max_digits=5,
                              verbose_name="PLZ",
                              decimal_places=0,
                              default=0)

    gender = models.CharField(max_length=1,
                              verbose_name="Geschlecht",
                              default="M",
                              choices=(('M', 'M'), ('W', 'W')))

    ort = models.CharField(max_length=50,
                           verbose_name="Ort",
                           default="")

    STATUS_Erwachsene = "Er"
    STATUS_Jugendliche = "Ju"
    STATUS_Schueler = "Ss"
    STATUS_Kind = "Ki"
    STATUS_KindBeitragsfrei = "Kf"
    STATUS_PassivMitglied = "PM"
    STATUS_Nichtmitglied = "Nm"
    STATUS_Beitragsfrei = "Bf"
    STATUS_PartnerAktiv = "Pa"
    STATUS_PartnerPassiv = "Pp"

    STATUSDEFAULTS = (
        (STATUS_Erwachsene, "Erwachsene"),
        (STATUS_Jugendliche, "Jugendliche"),
        (STATUS_Schueler, u"Schüler, Studenten, BW, Zivi"),
        (STATUS_Kind, "Kind in Familie"),
        (STATUS_KindBeitragsfrei, "Kind in Familie, beitragsfrei"),
        (STATUS_PassivMitglied, "Passives Mitglied"),
        (STATUS_Nichtmitglied, "Nichtmitglied"),
        (STATUS_Beitragsfrei, "Beitragsfreies Mitglied"),
        (STATUS_PartnerAktiv, "Partner aktives Mitglied"),
        (STATUS_PartnerPassiv, "Partner passives Mitglied"),
    )

    status = models.CharField(max_length=20,
                              verbose_name="Mitgliedsstatus",
                              default=STATUS_Erwachsene,
                              choices=STATUSDEFAULTS)

    erstbenachrichtigt = models.BooleanField(
        verbose_name="Erstbenachrichtigung",
        help_text="Wurde die Erstbenachrichtigung mit Password bereits generiert?",
        default=False)

    arbeitslast = models.IntegerField(
        verbose_name="Arbeitslast (h/Jahr)",
        help_text="Wieviele Stunden pro Jahr muss dieses Mitglied arbeiten?",
        default=10,
        )

    def __unicode__(self):
        return self.user.__unicode__()

    def gemeldeteAnzahlAufgaben(self):
        return (Meldung.objects
                .filter(melder=self)
                .exclude(prefMitglied=Meldung.GARNICHT)
                .count())
        
    def gemeldeteStunden(self):
        """Compute hours for which the Mitglied has entered
        a Meldung. 
        """

        echteMeldungen = (Meldung.objects
                          .filter(melder=self)
                          .exclude(prefMitglied=Meldung.GARNICHT))

        return sum([m.aufgabe.stunden for m in echteMeldungen])

    def zugeteilteAufgaben(self):

        z = self.user.zuteilung_set.all()

        return z.count()
    
    def zugeteilteStunden(self, time=None):
        """Compute hours already assigned to this user.

        This is difficult because some aufgaben have easily identified hours,
        others have to be checked specifically for the
        stundenplan Zuteilung.

        :param time: -1: tasks from past,
                     +1: tasks from future,
                     0: Tasks without date (not sure this is useful?), 
                     None: do not filter assigned tasks any more. 
        :returns: Hours assigned to user, for the desired time frame.
        :rtype: int 
        """

        qs = self.user.zuteilung_set.all()

        if time == -1:
            qs = qs.filter(aufgabe__datum__lte=datetime.date.today())
        if time == +1:
            qs = qs.filter(aufgabe__datum__gt=datetime.date.today())
        if time == 0:
            qs = qs.filter(aufgabe__datum__isnull=True)

        stundenlist = [z.stunden() for z in qs]
        # print self.__unicode__(), time, stundenlist
        return sum(stundenlist)

    class Meta:
        verbose_name_plural = "Mitglieder"
        verbose_name = "Mitglied"


class Aufgabengruppe (models.Model):
    gruppe = models.CharField(max_length=30,
                              help_text="Aussagefähiger Name für Gruppe"
                              " von Aufgaben")

    verantwortlich = models.ForeignKey(User,
                                       help_text="Verantwortliches "
                                       "Vorstandsmitglied")

    bemerkung = models.TextField(blank=True)

    def __unicode__(self):
        return self.gruppe

    class Meta:
        verbose_name_plural = "Aufgabengruppen"
        verbose_name = "Aufgabengruppe"
        ordering = ['gruppe']

class Aufgabe(models.Model):
    aufgabe = models.CharField(max_length=50)
    verantwortlich = models.ForeignKey(User,
                                       help_text="Verantwortliches "
                                       "Vorstandsmitglied")
    teamleader = models.ForeignKey(User,
                                   related_name="teamleader_set",
                                   help_text="Ein optionaler Teamleader für "
                                   "die Aufgabe (nicht notwendig Vorstand)",
                                   verbose_name="Team-Leader",
                                   blank=True, null=True,
                                   )

    gruppe = models.ForeignKey(Aufgabengruppe)
    anzahl = models.IntegerField(default=0,
                                 help_text="Wieviele Personen werden für "
                                 "diese Aufgabe gebraucht?",
                                 verbose_name="Anzahl benötigte Helfer")

    stunden = models.IntegerField(default=0,
                                  help_text="Wieviele Stunden Arbeit "
                                  "pro Person?",
                                  verbose_name="Stunden",
                                  )

    datum = models.DateField(blank=True, null=True,
                             help_text="Wann fällt die Aufgabe an? "
                             "(freilassen möglich)")

    bemerkung = models.TextField(blank=True)

    def kontakt(self):
        if self.teamleader:
            return self.teamleader
        else:
            return self.verantwortlich

    def numMeldungen(self):
        """How many Meldungen of status better than No!
        exist for this Aufgabe?
        """
        # print Meldung.GARNICHT
        return self.meldung_set.exclude(prefMitglied=
                                        Meldung.GARNICHT).count()

    def has_Stundenplan(self):
        """Is there a STundenplan for this Aufgabe?"""

        return self.stundenplan_set.filter(anzahl__gt=0).count() > 0

    def is_open(self):
        """Do enough Zuteilungen already exist for this Aufgabe?"""

        return self.zuteilung_set.count() < self.anzahl

    def __unicode__(self):
        return u"{} ({})".format(self.aufgabe, self.id)

    class Meta:
        verbose_name_plural = "Aufgaben"
        verbose_name = "Aufgabe"
        ordering = ['aufgabe']


class Stundenplan (models.Model):
    aufgabe = models.ForeignKey(Aufgabe)
    uhrzeit = models.IntegerField(help_text="Beginn")
    anzahl = models.IntegerField(default=0,
                                 help_text="Wieviele Personen werden um "
                                 "diese Uhrzeit benötigt?")

    startZeit = 8
    stopZeit = 23

    def __unicode__(self):
        return (self.aufgabe.__unicode__() +
                "@" + str(self.uhrzeit) +
                ": " + str(self.anzahl))

    class Meta:
        verbose_name_plural = "Stundenpläne"
        verbose_name = "Stundenplan"


class Meldung (models.Model):
    erstellt = models.DateField(auto_now_add=True)
    veraendert = models.DateField(auto_now=True)
    melder = models.ForeignKey(User)
    aufgabe = models.ForeignKey(Aufgabe)

    GARNICHT = -1
    WENNSMUSS = 0
    NORMAL = 1
    GERNE = 2

    PRAEFERENZ = (
        (GARNICHT, "Nein"),
        (WENNSMUSS, "Wenn es sein muss"),
        (NORMAL, "Ok"),
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
                                        verbose_name = "Präferenz", 
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
    aufgabe = models.ForeignKey(Aufgabe)
    ausfuehrer = models.ForeignKey(User)
    automatisch = models.BooleanField(default=False)

    def __unicode__(self):
        # print self.stundenzuteilung_set.all() 
        return (self.aufgabe.__unicode__() + ": " + self.ausfuehrer.__unicode__() 
                + (" @ " + ','.join([s.__unicode__() for s in self.stundenzuteilung_set.all()] ))
                # + ('@' + ','.join(self.StundenZuteilung_set.all().values('uhrzeit')))
                )

    def save(self, *args, **kwargs):
        super(Zuteilung, self).save(*args, **kwargs)
        self.ausfuehrer.zuteilungBenachrichtigungNoetig = True
        self.ausfuehrer.save()


    def delete(self, *args, **kwargs):
        self.ausfuehrer.zuteilungBenachrichtigungNoetig = True
        self.ausfuehrer.save()
        super(Zuteilung, self).delete(*args, **kwargs)

    def stunden(self):
        """Compute the hours allocated to this zuteilung.
        Depends on whether a Stundenplan exists for this job.
        """

        tmp = self.aufgabe.stundenplan_set.filter(anzahl__gt=0).count()
        if tmp > 0:
            return tmp
        else:
            return self.aufgabe.stunden

    def stundenTuple(self):
        """Produce a list of tuples with the Stunden
        correpsonding to this Zuteilung. Compress it
        so that only consecutive intervals show up. 

        Arguments:
        - `self`:
        """

        outlist = []    
        inlist = sorted([s.uhrzeit for s in self.stundenzuteilung_set.all()])

        ## print self.aufgabe, self.ausfuehrer, inlist
        try: 
            if inlist:
                now = inlist.pop(0)
                currentTuple = (now, now+1)
                while inlist:
                    now = inlist.pop(0)
                    if now == currentTuple[1]:
                        currentTuple = (currentTuple[0], now +1)
                    else:
                        outlist.append(currentTuple)
                        currentTuple = (now, now+1)

                outlist.append(currentTuple)
        except Exception as e:
            print e 

        ## print "outlist: ", outlist 
        return outlist


    def stundenString(self):
        st = self.stundenTuple()
        r = ', '.join([
            '{0} Uhr - {1} Uhr'.format(s[0], s[1])
            for s in st
            ])

        return r

    class Meta:
        verbose_name_plural = "Zuteilungen"
        verbose_name = "Zuteilung"


class StundenZuteilung(models.Model):
    zuteilung = models.ForeignKey(Zuteilung)
    uhrzeit = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super(StundenZuteilung, self).save(*args, **kwargs)
        self.zuteilung.ausfuehrer.zuteilungBenachrichtigungNoetig = True
        self.zuteilung.ausfuehrer.save()

    def delete(self, *args, **kwargs):
        self.zuteilung.ausfuehrer.zuteilungBenachrichtigungNoetig = True
        self.zuteilung.ausfuehrer.save()
        super(StundenZuteilung, self).delete(*args, **kwargs)

    class Meta:
        verbose_name = "Zuteilung einer Stunde"
        verbose_name_plural = "Zuteilungen für einzelne Stunden"

    def __unicode__(self):
        return str(self.uhrzeit)


class Leistung (models.Model):
    melder = models.ForeignKey (User)
    aufgabe = models.ForeignKey (Aufgabe)
    erstellt = models.DateTimeField (auto_now_add=True)
    # veraendert = models.DateTimeField (auto_now=True)
    veraendert = models.DateTimeField ()
    benachrichtigt = models.DateTimeField (default=datetime.datetime(1900,1,1))
    wann = models.DateField (help_text="An welchem Tag haben Sie die Leistung erbracht?",
                             ) 
    zeit = models.DecimalField (max_digits=3,
                                decimal_places = 1,
                                help_text="Wieviel Zeit (in Stunden) haben Sie gearbeitet?", 
                                )
    ## auslagen = models.DecimalField (max_digits=6,
    ##                                 decimal_places = 2,
    ##                                 help_text = "Hatten Sie finanzielle Auslagen? Bitte Belege vorlegen!",
    ##                                 default = 0, 
    ##                                 ) 
    ## km = models.DecimalField (max_digits= 4,
    ##                           decimal_places = 0,
    ##                           help_text = "Hatten Sie Wegstrecken, für die Sie km-Vergütung erhalten?",
    ##                           default = 0, 
    ##                           )

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
    status = models.CharField(max_length=2,
                              choices = STATUS,
                              default = OFFEN) 

    bemerkung = models.TextField(blank=True)
    bemerkungVorstand = models.TextField(blank=True,
                                         verbose_name="Bemerkung Vorstand")

    class Meta:
        verbose_name_plural = "Leistungen"
        verbose_name = "Leistung"


    def save(self, veraendert=True, *args, **kwargs):
        """
        Override the save method to realize a auto_now field with a veto.
        That is necessary for the email send logic, where save is called
        with autonow=False.

        Arguments:

        - `self`:
        - `veraendert`: IF true, the veranedert field is updated,
                        similar to an auto_now field;
                        else, no update (veto'ing the auto_now behavior)
        - `*args`: Passed through to super class
        - `**kwargs`: Passed through to super class
        """
        if veraendert:
            self.veraendert = (datetime.datetime.
                                   utcnow().replace(tzinfo=utc))

        return super(Leistung, self).save(*args, **kwargs)

    def __unicode__ (self):
        return (self.melder.__unicode__() + " ; " +
                self.aufgabe.__unicode__() + " ; " +
                (self.veraendert.strftime("%d/%m/%y")
                 if self.veraendert else "--") 
                )



## this is just debug code for the meldung issue - trying to figure out why there are double instances
from django.db.models.signals import pre_save, pre_init, post_save
from django.dispatch import receiver 

## @receiver(pre_init, sender=Meldung)
## def meldungDebugPreInit (sender, args, **kwargs):
##     print "Meldung Pre Init : ", args, kwargs

## @receiver(pre_save, sender=Meldung)
## def meldungDebugPreSave (sender, **kwargs):
##     print "Meldung PreSave: ", kwargs
    
## @receiver(post_save, sender=Meldung)
## def meldungDebugPostSave (sender, **kwargs):
##     print "Meldung PostSave: ", kwargs
    
