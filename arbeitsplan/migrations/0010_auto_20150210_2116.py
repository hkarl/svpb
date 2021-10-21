# -*- coding: utf-8 -*-


from django.db import models, migrations
import phonenumber_field.modelfields
import arbeitsplan.models


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0009_mitglied_arbeitslast'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='aufgabe',
            options={'ordering': ['aufgabe'], 'verbose_name': 'Aufgabe', 'verbose_name_plural': 'Aufgaben'},
        ),
        migrations.AlterModelOptions(
            name='aufgabengruppe',
            options={'ordering': ['gruppe'], 'verbose_name': 'Aufgabengruppe', 'verbose_name_plural': 'Aufgabengruppen'},
        ),
        migrations.AddField(
            model_name='mitglied',
            name='festnetz',
            field=phonenumber_field.modelfields.PhoneNumberField(default='', max_length=128, verbose_name='Festnetznummer', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mitglied',
            name='mobil',
            field=phonenumber_field.modelfields.PhoneNumberField(default='', max_length=128, verbose_name='Mobilnummer', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='aufgabe',
            name='aufgabe',
            field=models.CharField(max_length=50, validators=[arbeitsplan.models.validate_notDot]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='meldung',
            name='prefMitglied',
            field=models.IntegerField(default=1, help_text='Haben Sie Vorlieben f\xc3\xbcr diese Aufgabe?', verbose_name='Pr\xc3\xa4ferenz', choices=[(-1, 'Nein'), (0, 'Wenn es sein muss'), (1, 'Ok'), (2, 'Gerne!')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mitglied',
            name='gender',
            field=models.CharField(default='M', max_length=1, verbose_name='Geschlecht', choices=[('M', 'M'), ('W', 'W')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mitglied',
            name='status',
            field=models.CharField(default='Er', max_length=20, verbose_name='Mitgliedsstatus', choices=[('Er', 'Erwachsene'), ('Ju', 'Jugendliche'), ('Ss', 'Sch\xfcler, Studenten, BW, Zivi'), ('Ki', 'Kind in Familie'), ('Kf', 'Kind in Familie, beitragsfrei'), ('PM', 'Passives Mitglied'), ('Nm', 'Nichtmitglied'), ('Bf', 'Beitragsfreies Mitglied'), ('Pa', 'Partner aktives Mitglied'), ('Pp', 'Partner passives Mitglied')]),
            preserve_default=True,
        ),
    ]
