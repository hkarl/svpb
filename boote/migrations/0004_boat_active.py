# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boote', '0003_boatissue_notified'),
    ]

    operations = [
        migrations.AddField(
            model_name='boat',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
