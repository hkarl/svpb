# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0007_auto_20141201_2134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aufgabe',
            name='teamleader',
            field=models.ForeignKey(related_name='teamleader_set', blank=True, to=settings.AUTH_USER_MODEL, help_text='Ein optionaler Teamleader f\xc3\xbcr die Aufgabe (nicht notwendig Vorstand)', null=True, verbose_name='Team-Leader', on_delete=CASCADE),
            preserve_default=True,
        ),
    ]
