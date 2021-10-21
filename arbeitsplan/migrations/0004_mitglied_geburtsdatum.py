# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0003_auto_20141102_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='mitglied',
            name='geburtsdatum',
            field=models.DateField(default=datetime.datetime(1900, 1, 1, 0, 0), help_text='Geburtsdatum des Mitglieds', verbose_name='Geburtstag'),
            preserve_default=True,
        ),
    ]
