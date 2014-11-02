# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mitglied',
            name='zustimmungsDatum',
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0), help_text=b'Wann hat der Nutzer Zustimmung erteilt?', verbose_name=b'Datum der Zustimmung'),
            preserve_default=True,
        ),
    ]
