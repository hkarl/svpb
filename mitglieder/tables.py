# -*- coding: utf-8 -*-

import django_tables2
from django.contrib.auth.models import User


class MitgliederTable(django_tables2.Table):

    mitgliedsnummer = django_tables2.Column(accessor="mitglied.mitgliedsnummer")

    edit = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountOtherEdit' record.pk %}\"> Editieren </a></i>",
        verbose_name=u"Editieren",
        orderable=False,
        empty_values=(),
        )

    delete = django_tables2.TemplateColumn(
        "<a href=\"{% url 'accountDelete' record.pk %}\"> Löschen </a></i>",
        verbose_name=u"Löschen",
        orderable=False,
        empty_values=(),
        )
     

    class Meta:
        model = User

        attrs = {"class": "paleblue"}
        
        fields = ('first_name',
                  'last_name',
                  'mitgliedsnummer',
                  'edit',
                  'delete',
                  )