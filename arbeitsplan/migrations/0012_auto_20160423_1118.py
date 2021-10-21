# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arbeitsplan', '0011_auto_20150215_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leistung',
            name='zeit',
            field=models.DecimalField(help_text='Wieviel Zeit (in Stunden) haben Sie gearbeitet? Eingabe von Zentelstunden m\xc3\xb6glich. Je nach Browsereinstellung mit . oder , die Nachkommastelle abtrennen: 1.4 oder 1,4 f\xc3\xbcr 1 Stunde 24 Minuten. ', max_digits=3, decimal_places=1),
            preserve_default=True,
        ),
    ]
