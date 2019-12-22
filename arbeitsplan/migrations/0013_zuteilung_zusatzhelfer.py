# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0012_auto_20160423_1118'),
    ]

    operations = [
        migrations.AddField(
            model_name='zuteilung',
            name='zusatzhelfer',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
