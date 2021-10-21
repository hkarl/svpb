# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boote', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='boat',
            name='briefing',
            field=models.CharField(default='', max_length=2000, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='booking',
            name='notified',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
