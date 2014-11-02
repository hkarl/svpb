# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0002_mitglied_zustimmungsdatum'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aufgabe',
            name='aufgabe',
            field=models.CharField(max_length=50),
        ),
    ]
