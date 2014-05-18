# -*- coding: utf-8 -*-

"""
Collect all the tables and column types relevant for django_tables2 here.
"""

from django.utils.safestring import mark_safe
from django.utils.html import escape, format_html


import django_tables2
from django_tables2.utils import A  # alias for Accessor

import models
import unicodedata


####################################
# Colum Types
####################################


class RadioButtonTable (django_tables2.Table):

    def render_radio(self, fieldname, choices, buttontexts, **kwargs):
        ## print bound_row._record 
        ## print type(bound_row._record )
        ## print getattr (bound_row._record, fieldname)
        # print "render_radio ", record

        print kwargs
        if 'bound_row' in kwargs:
            record = kwargs['bound_row']._record
        if 'record' in kwargs:
            record = kwargs['record']
        print 'rec: ', record

        try:
            tmp = '\n'.join([
                format_html(u"""
                <label class="btn {4} {5}">
                <input type="radio" name="{0}_{1}" value="{2}"> {3}
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
                <input type="radio" name="{0}_{1}" value="{2}"> {3}
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
    Control tags (intergeres, not strings!):
    -1: show no field
    0: unchecked checkbox
    1: checked checkbox 
    """
    
    def render (self, value):
        # print value 
        if value[0] == -1:
            return ""

        if len(value)>2:
            text = value[2]
        else:
            text = ""
            
        return mark_safe ('<input type="checkbox" value="1" name="' +
                          escape(value[1]) +
                          '" ' +
                          ("checked" if value[0]==1 else "") +
                          '/>' + text 
                          )


class TextareaInputColumn (django_tables2.columns.Column):

    def render (self, value):
        # print "render: ", value, self.__dict__
        return mark_safe ('<input class="textinput textInput" id="id_bemerkungVorstand" maxlength="20" name="bemerkungVorstand" placeholder="Bemerkung Vorstand" value="'
                          +    escape (value) +
                          '" type="text" />'
                        )
    

class RequiredAssignedColumn (django_tables2.columns.Column):
    """
    A column used by the stundenplan survey table. Renders both required and assigned  numbers in one cell.
    """

    def render (self, value):
        # print value
        try: 
            r = mark_safe (str(value['required']) + " / " + str(value['zugeteilt']))
        except TypeError:
            r = ""
            
        return r

class LinkedColumn (django_tables2.columns.Column):
    """
    A column that redners a simple <a href>, assuming a tuple of values 
    """

    def render (self, value):
        text, link = value

        if text: 
            return mark_safe("<a href={0}>{1}</a>".format(link, text))
        else:
            return "-" 

            
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

def NameTableFactory (name, attrs, l, meta=None):
    """
    A Factory for django_tables2 with dynamic colums.
    Always adds a Nachame, Vorname column to the given attributes 
    """

    nameattrs = {'last_name': django_tables2.Column(verbose_name="Nachname"),
                'first_name': django_tables2.Column(verbose_name="Vorname"),
                }
    nameattrs.update(attrs)

    return TableFactory (name, nameattrs, l,
                         meta=meta if meta else {'sequence': ('last_name', 'first_name', '...')})

##############################


def StundenplanTableFactory (l):
    """
    A factory to produce a table with aufgaben and uhrzeiten columns. 
    """

    newattrs = {}
    for i in  range(models.Stundenplan.startZeit,
                         models.Stundenplan.stopZeit+1):
        ## newattrs['u'+str(i)] = django_tables2.Column (accessor='u'+str(i),
        ##                                        verbose_name = str(i)+'-'+str(i+1))
        newattrs['u'+str(i)] = RequiredAssignedColumn (accessor='u'+str(i),
                                               verbose_name = str(i)+'-'+str(i+1))
        
    ## newattrs['id'] = django_tables2.LinkColumn ('arbeitsplan-stundenplaeneEdit',
    ##                                     args=[A('id'),],
    ##                                     verbose_name="Zuteilung editieren")
    newattrs['aufgabe'] = django_tables2.Column(accessor='aufgabe')
    newattrs['gruppe'] = django_tables2.Column(accessor='gruppe', verbose_name="Aufgabengruppe")

    newattrs['gemeldet'] = django_tables2.Column(accessor='gemeldet',
                                                  verbose_name="# Meldungen")
    newattrs['required'] = django_tables2.Column(accessor='required',
                                                  verbose_name="# Anforderungen")
    newattrs['zugeteilt'] = django_tables2.Column(accessor='zugeteilt',
                                                   verbose_name ="# Zuteilungen")

    newattrs['editlink'] = django_tables2.Column(accessor="editlink",
                                                  verbose_name="Zuteilen")

    newattrs['stundenplanlink'] = django_tables2.Column(accessor="stundenplanlink",
                                                        verbose_name="Stundenplan")

    t = TableFactory ("Stundenplan",
                         newattrs, l,
                         meta = {'sequence': ('aufgabe', 'gruppe', # 'id',
                                              'editlink', 'stundenplanlink',  
                                              'required', 'gemeldet', 'zugeteilt', 
                                              '...', )})
        
    return t


def StundenplanEditFactory (l):
    """
    Produce a table with persons as row, uhrzeiten as columns. Checkboxes in the uhrzeit columns. 
    """

    newattrs = {}

    for i in  range(models.Stundenplan.startZeit,
                         models.Stundenplan.stopZeit+1):
        ## newattrs['u'+str(i)] = django_tables2.Column (accessor='u'+str(i),
        ##                                        verbose_name = str(i)+'-'+str(i+1))
        newattrs['u'+str(i)] = ValuedCheckBoxColumn (accessor='u'+str(i),
                                                verbose_name = str(i)+'-'+str(i+1))

    return NameTableFactory ("StundenplanEdit",
                             newattrs, l,
                             meta = {'sequence': ('last_name', 'first_name', '...')}
                             )
    
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
                                          verbose_name="Editieren")
    
    class Meta:
        model = models.Aufgabe
        attrs = {"class": "paleblue"}
        # fields=("aufgabe", "datum", django_tables2.A("verantwortlich.last_name"), "gruppe", "anzahl", "bemerkung")
        fields=("gruppe", "aufgabe", "datum", "anzahl", "stunden", "bemerkung", 'verantwortlicher', 'id')

        # TODO: anzahl muss man wahrscheinlich auf die ANzahl FREIE Plaetze umrechnen!?!?


########################

class StundenplanTable (django_tables2.Table):
    id = django_tables2.LinkColumn ('arbeitsplan-stundenplaeneEdit',
                                      args=[A('id'),],
                                      verbose_name="Stundenplan editieren")
    aufgabe = django_tables2.Column (accessor='aufgabe')
    gruppe = django_tables2.Column (accessor='gruppe__gruppe', verbose_name="Aufgabengruppe")

    u0 = django_tables2.Column (accessor='u0', verbose_name='0-1')
    u1 = django_tables2.Column (accessor='u1', verbose_name='0-1')
    u2 = django_tables2.Column (accessor='u2', verbose_name='0-1')
    u3 = django_tables2.Column (accessor='u3', verbose_name='0-1')
    u4 = django_tables2.Column (accessor='u4', verbose_name='0-1')
    u5 = django_tables2.Column (accessor='u5', verbose_name='0-1')
    u6 = django_tables2.Column (accessor='u6', verbose_name='0-1')
    u7 = django_tables2.Column (accessor='u7', verbose_name='0-1')
    u8 = django_tables2.Column (accessor='u8', verbose_name='0-1')
    u9 = django_tables2.Column (accessor='u9', verbose_name='0-1')
    u10 = django_tables2.Column (accessor='u10', verbose_name='0-1')
    u11 = django_tables2.Column (accessor='u11', verbose_name='0-1')
    u12 = django_tables2.Column (accessor='u12', verbose_name='0-1')
    u13 = django_tables2.Column (accessor='u13', verbose_name='0-1')
    u14 = django_tables2.Column (accessor='u14', verbose_name='0-1')
    u15 = django_tables2.Column (accessor='u15', verbose_name='0-1')
    u16 = django_tables2.Column (accessor='u16', verbose_name='0-1')
    u17 = django_tables2.Column (accessor='u17', verbose_name='0-1')
                            
    class Meta:
        # model = models.Aufgabe
        attrs = {"class": "paleblue"}
        # fields = ('aufgabe', 'gruppe', 'id', )

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

    bemerkungVorstand = django_tables2.Column (empty_values=(),
                                               verbose_name = "Bemerkungen des Vorstandes")
    prefVorstand = django_tables2.Column (accessor="prefVorstand",
                                      verbose_name="Vorlieben des Vorstandes",
                                      empty_values=(), 
                                     )
    
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
        attrs[s[0]] = LinkedColumn(verbose_name=s[1])

    attrs['zugeteilt'] = LinkedColumn(verbose_name="Zugeteilt (h)")
    t = NameTableFactory ("salden", attrs, l)
    return t 

##############################


def ZuteilungsTableFactory (tuple):
    l, aufgabenQs = tuple

    attrs={}
    for a in aufgabenQs:
        tag = unicodedata.normalize('NFKD', a.aufgabe).encode('ASCII', 'ignore')
        attrs[tag] = ValuedCheckBoxColumn(verbose_name= (u"{} ({})".format (a.aufgabe,
                                                                               a.gruppe,)),
                                          orderable=False)

    attrs['zugeteilt'] = django_tables2.Column(verbose_name="Bereits zugeteilt (h)")

    t = NameTableFactory ('ZuteilungsTable', attrs, l)
 
    return t 

##############################


class LeistungTable(django_tables2.Table):
    """
    Show the Leistungen of an individual member.
    """

    ## melder_last = django_tables2.Column (accessor="melder.last_name",
    ##                                      verbose_name="Melder Nachname")
    ## melder_first = django_tables2.Column (accessor="melder.first_name",
    ##                                      verbose_name="Melder Vorname")

    aufgabe = django_tables2.Column (accessor="aufgabe.aufgabe",
                                     verbose_name="Aufgabe")
    class Meta:
        model = models.Leistung
        attrs = {"class": "paleblue"}
        fields = (# 'melder_last', 'melder_first',
                    'aufgabe', 'wann', 'zeit',
                    'status',
                    'auslagen', 'km', 'bemerkung', 'bemerkungVorstand')
    
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

    bemerkungVorstand = django_tables2.Column (empty_values=(),
                                               verbose_name = "Bemerkungen des Vorstandes")


    class Meta:
        model = models.Leistung
        attrs = {"class": "paleblue"}
        exclude = ("erstellt", "veraendert", 'id')        
        sequence = ('melder', 'aufgabe', 'wann', 'zeit', 'auslagen', 'km',
                    'bemerkung', 'status', 'bemerkungVorstand')
