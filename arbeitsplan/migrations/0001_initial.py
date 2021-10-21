# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Aufgabe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('aufgabe', models.CharField(max_length=30)),
                ('anzahl', models.IntegerField(default=0, help_text='Wieviele Personen werden f\xc3\xbcr diese Aufgabe gebraucht?', verbose_name='Anzahl ben\xc3\xb6tigte Helfer')),
                ('stunden', models.IntegerField(default=0, help_text='Wieviele Stunden Arbeit pro Person?', verbose_name='Stunden')),
                ('datum', models.DateField(help_text='Wann f\xc3\xa4llt die Aufgabe an? (freilassen m\xc3\xb6glich)', null=True, blank=True)),
                ('bemerkung', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Aufgabe',
                'verbose_name_plural': 'Aufgaben',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Aufgabengruppe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gruppe', models.CharField(help_text='Aussagef\xc3\xa4higer Name f\xc3\xbcr Gruppe von Aufgaben', max_length=30)),
                ('bemerkung', models.TextField(blank=True)),
                ('verantwortlich', models.ForeignKey(help_text='Verantwortliches Vorstandsmitglied', to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ],
            options={
                'verbose_name': 'Aufgabengruppe',
                'verbose_name_plural': 'Aufgabengruppen',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Leistung',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('erstellt', models.DateTimeField(auto_now_add=True)),
                ('veraendert', models.DateTimeField()),
                ('benachrichtigt', models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0))),
                ('wann', models.DateField(help_text='An welchem Tag haben Sie die Leistung erbracht?')),
                ('zeit', models.DecimalField(help_text='Wieviel Zeit (in Stunden) haben Sie gearbeitet?', max_digits=3, decimal_places=1)),
                ('status', models.CharField(default=b'OF', max_length=2, choices=[(b'OF', b'Offen'), (b'AK', b'Akzeptiert'), (b'RU', b'R\xc3\xbcckfrage'), (b'NE', b'Abgelehnt')])),
                ('bemerkung', models.TextField(blank=True)),
                ('bemerkungVorstand', models.TextField(verbose_name='Bemerkung Vorstand', blank=True)),
                ('aufgabe', models.ForeignKey(to='arbeitsplan.Aufgabe', on_delete=models.PROTECT)),
                ('melder', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Leistung',
                'verbose_name_plural': 'Leistungen',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Meldung',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('erstellt', models.DateField(auto_now_add=True)),
                ('veraendert', models.DateField(auto_now=True)),
                ('prefMitglied', models.IntegerField(default=1, help_text='Haben Sie Vorlieben f\xc3\xbcr diese Aufgabe?', choices=[(-1, b'Nein'), (0, b'Wenn es sein muss'), (1, b'Ok'), (2, b'Gerne!')])),
                ('prefVorstand', models.IntegerField(default=1, help_text='Trauen Sie diesem Mitglied die Aufgabe zu?', choices=[(-1, b'Nein'), (0, b'Wenn es sein muss'), (1, b'Ok'), (2, b'Gerne!')])),
                ('bemerkung', models.TextField(blank=True)),
                ('bemerkungVorstand', models.TextField(blank=True)),
                ('aufgabe', models.ForeignKey(to='arbeitsplan.Aufgabe', on_delete=models.PROTECT)),
                ('melder', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Meldung',
                'verbose_name_plural': 'Meldungen',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Mitglied',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mitgliedsnummer', models.CharField(default=0, help_text='Mitgliedsnummer', max_length=10)),
                ('zuteilungsbenachrichtigung', models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0), help_text='Wann war die letzte Benachrichtigung zu einer Zuteilung?', verbose_name='Letzte Benachrichtigung')),
                ('zuteilungBenachrichtigungNoetig', models.BooleanField(default=True, help_text='Muss an diese Nutzer eine Benachrichtigung wegen \xc3\x84nderung der Zuteilungen gesendet werden?', verbose_name='Benachrichtigung zu Zuteilungen n\xc3\xb6tig?')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Mitglied',
                'verbose_name_plural': 'Mitglieder',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Stundenplan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uhrzeit', models.IntegerField(help_text='Beginn')),
                ('anzahl', models.IntegerField(default=0, help_text='Wieviele Personen werden um diese Uhrzeit ben\xc3\xb6tigt?')),
                ('aufgabe', models.ForeignKey(to='arbeitsplan.Aufgabe', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Stundenplan',
                'verbose_name_plural': 'Stundenpl\xe4ne',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StundenZuteilung',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uhrzeit', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Zuteilung einer Stunde',
                'verbose_name_plural': 'Zuteilungen f\xfcr einzelne Stunden',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Zuteilung',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('automatisch', models.BooleanField(default=False)),
                ('aufgabe', models.ForeignKey(to='arbeitsplan.Aufgabe', on_delete=models.PROTECT)),
                ('ausfuehrer', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Zuteilung',
                'verbose_name_plural': 'Zuteilungen',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='stundenzuteilung',
            name='zuteilung',
            field=models.ForeignKey(to='arbeitsplan.Zuteilung', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='aufgabe',
            name='gruppe',
            field=models.ForeignKey(to='arbeitsplan.Aufgabengruppe', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='aufgabe',
            name='teamleader',
            field=models.ForeignKey(related_name=b'teamleader_set', blank=True, to=settings.AUTH_USER_MODEL, help_text='Ein optinaler Teamleader f\xc3\xbcr die Aufgabe (nicht notwendig Vorstand)', null=True, verbose_name='Team-Leader', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='aufgabe',
            name='verantwortlich',
            field=models.ForeignKey(help_text='Verantwortliches Vorstandsmitglied', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
