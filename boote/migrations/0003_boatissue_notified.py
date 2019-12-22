# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boote', '0002_auto_20160911_1258'),
    ]

    operations = [
        migrations.AddField(
            model_name='boatissue',
            name='notified',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
