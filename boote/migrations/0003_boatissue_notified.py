# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boote', '0002_auto_20170114_1233'),
    ]

    operations = [
        migrations.AddField(
            model_name='boatissue',
            name='notified',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
