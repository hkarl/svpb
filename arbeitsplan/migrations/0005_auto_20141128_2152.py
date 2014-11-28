# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0004_mitglied_geburtsdatum'),
    ]

    operations = [
        migrations.AddField(
            model_name='mitglied',
            name='erstbenachrichtigt',
            field=models.BooleanField(default=False, help_text=b'Wurde die Erstbenachrichtigung mit Password bereits generiert?', verbose_name=b'Erstbenachrichtigung'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mitglied',
            name='ort',
            field=models.CharField(default=b'', max_length=50, verbose_name=b'Ort'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mitglied',
            name='plz',
            field=models.DecimalField(default=0, verbose_name=b'PLZ', max_digits=5, decimal_places=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mitglied',
            name='strasse',
            field=models.CharField(default=b'', max_length=50, verbose_name=b'Strasse und Hausnummer'),
            preserve_default=True,
        ),
    ]
