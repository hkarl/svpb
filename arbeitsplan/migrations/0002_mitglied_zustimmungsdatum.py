# -*- coding: utf-8 -*-


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
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0), help_text='Wann hat der Nutzer Zustimmung erteilt?', verbose_name='Datum der Zustimmung'),
            preserve_default=True,
        ),
    ]
