# -*- coding: utf-8 -*-

"""
Collect all the tables and column types relevant for django_tables2 here. 
"""

from django.utils.safestring import mark_safe
from django.utils.html import escape, format_html
from string import Template

import django_tables2
from django_tables2.utils import A  # alias for Accessor

import models
import unicodedata
import django.utils.encoding 

####################################
### Colum Types
####################################

class RadioButtonTable (django_tables2.Table):
        
    def render_radio (self, record, fieldname, choices, buttontexts):
        ## print bound_row._record 
        ## print type(bound_row._record )
        ## print getattr (bound_row._record, fieldname)
        # print "render_radio ", record

        try: 
            tmp = '\n'.join([
                format_html(u"""
                <label class="btn {4} {5}">
                <input type="radio" name="{0}_{1}_{2}"> {3}
                </label>
                """,
                fieldname,
                record['id'], 
                choice[0],
                choice[1],
                buttontexts[choice[0]],
                " active" if record[fieldname] == choice[0] else "",
                )
                for (counter, choice) in enumerate(choices)])        
        except TypeError:
            tmp = '\n'.join([
                format_html(u"""
                <label class="btn {4} {5}">
                <input type="radio" name="{0}_{1}_{2}"> {3}
                </label>
                """,
                fieldname,
                record.id, 
                choice[0],
                choice[1],
                buttontexts[choice[0]],
                " active" if getattr(record,fieldname) == choice[0] else "",
                )
                for (counter, choice) in enumerate(choices)])        
            
            
        return mark_safe("""<div class="btn-group-vertical" data-toggle="buttons">""" +
                          tmp +
                          """</div>""")




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
        fields=("gruppe", "aufgabe", "datum", "anzahl", "stunden", "bemerkung")

        # TODO: anzahl muss man wahrscheinlich auf die ANzahl FREIE Plaetze umrechnen!?!?

class AufgabenTableVorstand (django_tables2.Table):
    verantwortlicher = django_tables2.Column (accessor="verantwortlich.last_name",
                                              verbose_name="Verantwortlicher")
    id = django_tables2.LinkColumn ('arbeitsplan-aufgabenEdit',
                                          args=[A('pk')],
                                          # kwargs={'pk': A('pk')},
                                          verbose_name="Editieren")
    
    class Meta:
        model = models.Aufgabe
        attrs = {"class": "paleblue"}
        # fields=("aufgabe", "datum", django_tables2.A("verantwortlich.last_name"), "gruppe", "anzahl", "bemerkung")
        fields=("gruppe", "aufgabe", "datum", "anzahl", "stunden", "bemerkung", 'verantwortlicher', 'id')

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

class MeldungTable (RadioButtonTable):

    # id = django_tables2.Column ()
    
    aufgabe =  django_tables2.Column (accessor="aufgabe",
                                         verbose_name="Aufgabe")
    gruppe =   django_tables2.Column (accessor="gruppe",
                                         verbose_name="Aufgabengruppe")
    
    datum  =   django_tables2.Column (accessor="datum",
                                         verbose_name="Datum")

    stunden =   django_tables2.Column (accessor="stunden",
                                         verbose_name="Umfang (h)")
    
    prefMitglied = django_tables2.Column (accessor="prefMitglied",
                                      verbose_name="Vorlieben",
                                      empty_values=(), 
                                     )

    bemerkung = django_tables2.Column (accessor="bemerkung",
                                      verbose_name="Bemerkung",
                                      empty_values=(), 
                                     )

    def render_prefMitglied (self, value, record):
        return self.render_radio (choices=models.Meldung.PRAEFERENZ,
                                    buttontexts=models.Meldung.PRAEFERENZButtons,
                                    fieldname="prefMitglied",
                                    record=record)
            
    def render_bemerkung (self, value, record, bound_row):
        # print record
        # print bound_row
        tmp =  format_html (u'<textarea class="textinput textInput" id="id_bemerkung_{0}" name="bemerkung_{0}" placeholder="Bemerkung eingeben" rows=6>{1}</textarea>',
                                str(record['id']),
                                record['bemerkung'] if record['bemerkung'] else ""
                                )
            
        return tmp 
        
    class Meta:
        # model = models.Aufgabe 
        attrs = {"class": "paleblue"}

        fields = ('gruppe', 'aufgabe', 'datum', 'stunden', 'bemerkung', 'prefMitglied') 

class MeldungTableVorstand (RadioButtonTable):

    
    aufgabe =  django_tables2.Column (accessor="aufgabe",
                                         verbose_name="Aufgabe")
    gruppe =   django_tables2.Column (accessor="aufgabe.gruppe",
                                         verbose_name="Aufgabengruppe")
    
    datum  =   django_tables2.Column (accessor="aufgabe.datum",
                                         verbose_name="Datum")

    stunden =   django_tables2.Column (accessor="aufgabe.stunden",
                                         verbose_name="Umfang (h)")
    
    prefMitglied = django_tables2.Column (accessor="prefMitglied",
                                      verbose_name="Vorlieben",
                                      empty_values=(), 
                                     )

    bemerkung = django_tables2.Column (accessor="bemerkung",
                                      verbose_name="Bemerkung",
                                      empty_values=(), 
                                     )
    melder_last = django_tables2.Column (accessor="melder.last_name",
                                         verbose_name="Melder Nachname")
    melder_first = django_tables2.Column (accessor="melder.first_name",
                                         verbose_name="Melder Vorname")

    ## bemerkungVorstand = django_tables2.Column (accessor="bemerkungVorstand",
    ##                                     verbose_name="Bemerkung Vorstand",
    ##                                     empty_values=(), 
    ##                                     )

    bemerkungVorstand = django_tables2.Column (empty_values=(),)
    
    def render_prefVorstand (self, value, record):


        return self.render_radio (choices=models.Meldung.PRAEFERENZ,
                                    buttontexts=models.Meldung.PRAEFERENZButtons,
                                    fieldname="prefVorstand",
                                    record=record)

    def render_bemerkungVorstand (self, value, record):
        tmp =  format_html (u'<textarea class="textinput textInput" id="id_bemerkungVorstand_{0}" name="bemerkungVorstand_{0}" placeholder="Bemerkung Vorstand" rows=6>{1}</textarea>',
                                str(record.id),
                                record.bemerkungVorstand if record.bemerkungVorstand else ""
                                )
        return tmp 

    
    class Meta (MeldungTable.Meta):
        model = models.Meldung 
        fields = ('gruppe', 'aufgabe', 'datum', 'stunden', 'melder_last', 'melder_first', 'bemerkung', 'prefMitglied', 'bemerkungVorstand', 'prefVorstand') 
    
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


    
class LeistungBearbeitenTable (RadioButtonTable):

    def render_bemerkungVorstand (value, bound_row):
        tmp =  format_html (u'<textarea class="textinput textInput" id="id_bermerkungVorstand_{0}" name="bemerkungVorstand_{0}" placeholder="Bemerkung Vorstand" rows=6>{1}</textarea>',
                            str(bound_row._record.id),
                            bound_row._record.bemerkungVorstand,
                            )
        return tmp 


    def render_status (self, value, bound_row):
        return self.render_radio (bound_row=bound_row,
                                  choices= models.Leistung.STATUS,
                                  buttontexts=models.Leistung.STATUSButtons,
                                  fieldname="status")
    
##         tmp = '\n'.join([format_html(u"""
##             <label class="btn {5} {4}">
##             <input type="radio" name="status_{0}_{2}" id="status_{0}_{2}"> {3}
##             </label>
##             """,
##             bound_row._record.id,
##             counter,
##             status[0],
##             status[1],
##             " active" if bound_row._record.status == status[0] else "",
##             models.Leistung.STATUSButtons[status[0]])
##             for (counter, status) in enumerate(models.Leistung.STATUS)]
##             )
        
            
##         return mark_safe("""
## <div class="btn-group" data-toggle="buttons">
## """ +
## tmp +
## """
## </div>    
##     """)
    
    bemerkungVorstand = django_tables2.Column (empty_values=())
    
        
    class Meta:
        model = models.Leistung
        attrs = {"class": "paleblue"}
        exclude = ("erstellt", "veraendert", 'id')        
        sequence = ('melder', 'aufgabe', 'wann', 'zeit', 'auslagen', 'km',
                    'bemerkung', 'status', 'bemerkungVorstand')
    
