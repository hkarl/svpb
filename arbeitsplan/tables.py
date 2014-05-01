# -*- coding: utf-8 -*-

"""
Collect all the tables and column types relevant for django_tables2 here. 
"""

from django.utils.safestring import mark_safe
from django.utils.html import escape
from string import Template

import django_tables2
import models
import unicodedata


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


class TextareaInputColumn (django_tables2.columns.Column):

    def render (self, value):
        print "render: ", value, self.__dict__
        return mark_safe ('<input class="textinput textInput" id="id_bemerkungVorstand" maxlength="20" name="bemerkungVorstand" placeholder="Bemerkung Vorstand" value="'
                          +    escape (value) +
                          '" type="text" />'
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

##############################



class LeistungBearbeitenTable (django_tables2.Table):

    ## bemerkungVorstand = TextareaInputColumn (orderable=False,
    ##                                          verbose_name="Bemerkung Vorstand")

    # Column.empty_values = ()
    
    def render_bemerkungVorstand (value, bound_row):

        # print value 
        # print bound_row._record.bemerkungVorstand
        ## return mark_safe ('<input class="textinput textInput" id="id_bermerkungVorstand_{0}" maxlength="20" name="bemerkungVorstand_{0}" placeholder="Bemerkung Vorstand" value="{1}" type="text" />'.format(str(bound_row._record.id),
        ##                         escape (bound_row._record.bemerkungVorstand),
        ##                         )
        ##                 )        
        return mark_safe ('<textarea class="textinput textInput" id="id_bermerkungVorstand_{0}" name="bemerkungVorstand_{0}" placeholder="Bemerkung Vorstand" rows=6>{1}</textarea>'.format(str(bound_row._record.id),
                                escape (bound_row._record.bemerkungVorstand),
                                )
                        )        


    def render_status (value, bound_row):
        ## tmp = Template("""
        ## <div id="div_id_status_${id}" class="ctrlHolder">
        ## <label for="id_status_${id} class="requiredField">
        ## <ul>
        ## ${rows}
        ## </ul>
        ## </div>
        ## """)

        ## for s in models.Leistung.STATUS:
        ##     row = """<li><label for="id_status_${0}" class
        ##     """

        tmp = '\n'.join(["""
            <label class="btn {5} {4}">
            <input type="radio" name="status_{0}_{2}" id="status_{0}_{2}"> {3}
            </label>
            """.format(bound_row._record.id,
                       counter,
                       status[0],
                       status[1],
                       " active" if bound_row._record.status == status[0] else "",
                       models.Leistung.STATUSButtons[status[0]])
                        for (counter, status) in enumerate(models.Leistung.STATUS)],
                        )
        
            
        return mark_safe("""
<div class="btn-group" data-toggle="buttons">
""" +
tmp +
"""
</div>    
    """)
    
    bemerkungVorstand = django_tables2.Column (empty_values=())
    
        
    class Meta:
        model = models.Leistung
        attrs = {"class": "paleblue"}
        exclude = ("erstellt", "veraendert", 'id')        
        sequence = ('melder', 'aufgabe', 'wann', 'zeit', 'auslagen', 'km',
                    'bemerkung', 'status', 'bemerkungVorstand')
    
