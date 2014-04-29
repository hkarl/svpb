# -*- coding: utf-8 -*-

"""
Collect all the tables and column types relevant for django_tables2 here. 
"""

import django_tables2
import models


####################################
### Colum Types
####################################



class ValuedCheckBoxColumn (django_tables2.columns.Column):
    """A checkbox column where a pair of values is expected:
    name and whether the box is checked or not.
    Control tags:
    -1: show no field
    0: unchecked checkbox
    1: checked checkbox 
    """
    
    def render (self, value):
        if value[0] == -1:
            return ""
        
        return mark_safe ('<input type="checkbox" value="1" name="' +
                          escape(value[1]) +
                          '" ' +
                          ("checked" if value[0]==1 else "") +
                          '/>'
                          )
    
##############################
## Table facotires
##############################



def TableFactory (name, attrs, l, meta={}):
    """takes
    - a name for the new django_tables2 class
    - a dictoranry with column_name: column_types
    - a list of data to be used for the table 

    return klass 
    """

    metadict = dict(attrs={"class":"paleblue",
                            "orderable":"True",
                           # "width":"90%"
                    })


    metadict.update(meta)
    attrs['Meta'] = type('Meta',
                         (),
                         metadict,
                        )
    
    klass = type (name, (django_tables2.Table,), attrs)

    t = klass(l)
    return t 

##############################

def NameTableFactory (name, attrs, l):
    """
    A Factory for django_tables2 with dynamic colums.
    Always adds a Nachame, Vorname column to the given attributes 
    """

    nameattrs = {'last_name': django_tables2.Column(verbose_name="Nachname"),
                'first_name': django_tables2.Column(verbose_name="Vorname"),
                }
    nameattrs.update(attrs)

    return TableFactory (name, nameattrs, l,
                         meta={'sequence': ('last_name', 'first_name', '...')})

##############################

class AufgabenTable (django_tables2.Table):
    verantwortlicher = django_tables2.Column (accessor="verantwortlich.last_name",
                                              verbose_name="Verantwortlicher")
    class Meta:
        model = models.Aufgabe
        attrs = {"class": "paleblue"}
        # fields=("aufgabe", "datum", django_tables2.A("verantwortlich.last_name"), "gruppe", "anzahl", "bemerkung")
        fields=("aufgabe", "datum", "gruppe", "anzahl", "bemerkung")

        # TODO: anzahl muss man wahrscheinlich auf die ANzahl FREIE Plaetze umrechnen!?!?


##############################

class ZuteilungTable (django_tables2.Table):
    ausfuehrer_last = django_tables2.Column (accessor="ausfuehrer.last_name",
                                              verbose_name="Ausführer")
    class Meta:
        model = models.Zuteilung
        attrs = {"class": "paleblue"}

        fields = ("aufgabe", )

##############################

class MeldungTable (django_tables2.Table):
    melder_last = django_tables2.Column (accessor="melder.last_name",
                                         verbose_name="Nachname")
    melder_first = django_tables2.Column (accessor="melder.first_name",
                                         verbose_name="Vorname")
    aufgabe =  django_tables2.Column (accessor="aufgabe",
                                         verbose_name="Aufgabe")
    class Meta:
        model = models.Meldung
        attrs = {"class": "paleblue"}

        exclude = ("erstellt","veraendert", 'melder')

##############################

def SaldenTableFactory (l):

    attrs = {}
    for s in models.Leistung.STATUS:
        attrs[s[0]] = django_tables2.Column(verbose_name=s[1])

    t = NameTableFactory ("salden", attrs, l)
    return t 

##############################


def ZuteilungsTableFactory (l, aufgabenQs):
    attrs={}
    for a in aufgabenQs:
        tag = unicodedata.normalize('NFKD', a.aufgabe).encode('ASCII', 'ignore')
        attrs[tag] = ValuedCheckBoxColumn(verbose_name=a.aufgabe,
                                          orderable=False)

    t = NameTableFactory ('ZuteilungsTable', attrs, l)
 
    return t 
