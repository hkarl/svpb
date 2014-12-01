# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0006_mitglied_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='mitglied',
            name='status',
            field=models.CharField(default=b'', max_length=20, verbose_name=b'Mitgliedsstatus'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mitglied',
            name='zuteilungBenachrichtigungNoetig',
            field=models.BooleanField(default=False, help_text=b'Muss an diese Nutzer eine Benachrichtigung wegen \xc3\x84nderung der Zuteilungen gesendet werden?', verbose_name=b'Benachrichtigung zu Zuteilungen n\xc3\xb6tig?'),
        ),
    ]
