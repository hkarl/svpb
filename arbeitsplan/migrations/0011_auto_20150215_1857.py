# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import arbeitsplan.models


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0010_auto_20150210_2116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aufgabe',
            name='aufgabe',
            field=models.CharField(unique=True, max_length=50, validators=[arbeitsplan.models.validate_notDot]),
            preserve_default=True,
        ),
    ]
