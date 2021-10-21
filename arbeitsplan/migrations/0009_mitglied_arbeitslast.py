# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0008_auto_20141208_1906'),
    ]

    operations = [
        migrations.AddField(
            model_name='mitglied',
            name='arbeitslast',
            field=models.IntegerField(default=10, help_text='Wieviele Stunden pro Jahr muss dieses Mitglied arbeiten?', verbose_name='Arbeitslast (h/Jahr)'),
            preserve_default=True,
        ),
    ]
