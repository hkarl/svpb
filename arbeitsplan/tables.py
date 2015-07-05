# -*- coding: utf-8 -*-

"""
Collect all the tables and column types relevant for django_tables2 here.
"""

from django.utils.safestring import mark_safe
from django.utils.html import escape, format_html
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

import django_tables2
from django_tables2.utils import A  # alias for Accessor

import models
import unicodedata


####################################
# Colum Types
####################################


class RadioButtonTable (django_tables2.Table):

    def render_radio(self, fieldname, choices, buttontexts, **kwargs):

        if 'bound_row' in kwargs:
            record = kwargs['bound_row']._record
        if 'record' in kwargs:
            record = kwargs['record']

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

        return mark_safe(u"""<div class="btn-group-vertical" data-toggle="buttons">""" +
                          tmp +
                          u"""</div>""")


class KontaktColumn(django_tables2.columns.Column):
    """Pass an accessor to a user object,
    this will be rendered with first and last name
    as well as clickable email link.
    """

    def __init__(self, *args, **kwargs):
        if (('order_by' not in kwargs) and
            ('accessor' in kwargs)):
            kwargs['order_by'] = (kwargs['accessor']+'.last_name',
                                  kwargs['accessor']+'.first_name',
                                  )
            ## print kwargs['order_by'], type(kwargs['order_by'])
            ## print kwargs['accessor'], type(kwargs['accessor'])
        super(KontaktColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        # print value
        return mark_safe(u'{1} {2}{0}'.format(
            (u' <a href="mailto:{0}">'
             u'<span class="glyphicon glyphicon-envelope">'
             u'</span></a>'.format(value.email)
             if value.email
             else ""),
            value.first_name,
            value.last_name,
            ))


class ValuedCheckBoxColumn(django_tables2.columns.Column):
    """A checkbox column where a pair of values is expected:
    name and whether the box is checked or not.
    Control tags (intergeres, not strings!):
    -1: show no field
    0: unchecked checkbox
    1: checked checkbox
    """

    def render(self, value):

        if value[0] == -1:
            return ""

        if len(value) > 2:
            text = value[2]
        else:
            text = ""

        return mark_safe(u'<input type="checkbox" value="1" name="' +
                         escape(value[1]) +
                         '" ' +
                         ("checked" if value[0]==1 else "") +
                         '/>' + text
                         )

class IntegerEditColumn(django_tables2.columns.Column):
    """A Column type to allow editing of a single integer value

    value should be a tuple: first entry the value to display/edit, 
    second entry the id/name of the inputbox 
    """

    def render(self, value):

        print "rendinger Integeer Edit Column"
        print value, type(value)
        return format_html('<input type="" value="{}" name="{}" />',
                           value[0],
                           value[1],
                           )
    

class TextareaInputColumn (django_tables2.columns.Column):

    def render(self, value):
        # print "render: ", value, self.__dict__
        return mark_safe (u'<input class="textinput textInput" id="id_bemerkungVorstand" maxlength="20" name="bemerkungVorstand" placeholder="Bemerkung Vorstand" value="'
                          +    escape (value) +
                          u'" type="text" />'
                        )


class RequiredAssignedColumn (django_tables2.columns.Column):
    """
    A column used by the stundenplan survey table.
    Renders both required and assigned numbers in one cell.
    """

    def render(self, value):
        # print value
        try:
            r = mark_safe(str(value['required']) +
                          " / " + str(value['zugeteilt']))
        except TypeError:
            r = ""

        return r


class LinkedColumn(django_tables2.columns.Column):
    """
    A column that redners a simple <a href>,
    assuming a tuple of values
    """

    def render(self, value):
        text, link = value

        if text:
            return mark_safe(u"<a href={0}>{1}</a>".format(link, text))
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

    klass = type(name, (django_tables2.Table,), attrs)

    t = klass(l)
    return t

##############################

def NameTableFactory (name, attrs, l, meta=None,
                      kontakt=None):
    """
    A Factory for django_tables2 with dynamic colums.
    Always adds a Nachame, Vorname column to the given attributes 
    """

    if kontakt:
        nameattrs = {'kontakt': KontaktColumn(
            accessor=kontakt[0],
            verbose_name=kontakt[1],
            empty_values=(),
            ),
                    }
    else:
        nameattrs = {'last_name': django_tables2.Column(verbose_name="Nachname"),
                    'first_name': django_tables2.Column(verbose_name="Vorname"),
                    }
    nameattrs.update(attrs)

    # we need to construct the meta field to ensure that the names are shown correctly: 
    if not meta:
        if kontakt:
            meta = {'sequence': ('kontakt',
                                 '...',
                                 )}
        else:
            meta = {'sequence': ('last_name',
                                 'first_name',
                                 '...')}

    return TableFactory(name, nameattrs, l,
                        meta=meta
                        )

##############################


def StundenplanTableFactory(l, showStunden=True):
    """
    A factory to produce a table with aufgaben and uhrzeiten columns.
    """

    newattrs = {}

    if showStunden:
        for i in range(models.Stundenplan.startZeit,
                       models.Stundenplan.stopZeit+1):
            newattrs['u'+str(i)] = RequiredAssignedColumn(
                accessor='u'+str(i),
                verbose_name=str(i)+'-'+str(i+1)
                )

    newattrs['aufgabe'] = django_tables2.Column(accessor='aufgabe')
    newattrs['gruppe'] = django_tables2.Column(accessor='gruppe',
                                               verbose_name="Aufgabengruppe")

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
                                           '...',
                                           )})

    return t


def StundenplanEditFactory(l, aufgabe):
    """
    Produce a table with persons as row, uhrzeiten as columns.
    Checkboxes in the uhrzeit columns.
    """

    newattrs = {}

    # valus obtained from views/StundenplaeneEdit: 
    newattrs['anzahl'] = IntegerEditColumn(accessor='anzahl',
                                           verbose_name="Anzahl",
                                           empty_values=(),)
    
    for i in range(models.Stundenplan.startZeit,
                   models.Stundenplan.stopZeit+1):
        # print '----- ', i
        try: 
            benoetigt = aufgabe.stundenplan_set.filter(uhrzeit__exact=i)[0].anzahl
            # benoetigt = aufgabe.benoetigte_Anzahl(i)
        except Exception as e:
            print "eX: ", e
            benoetigt = 0
        # print benoetigt

        zugewiesen = aufgabe.zuteilung_set.filter(stundenzuteilung__uhrzeit=i).count()
        # zugewiesen = aufgabe.zugeteilte_Anzahl(i)
        # print zugewiesen

        newattrs['u'+str(i)] = ValuedCheckBoxColumn(accessor='u'+str(i),
                                                    # verbose_name=str(i)+'-'+str(i+1),
                                                    verbose_name=mark_safe('{} - {}'
                                                    '<span style="font-weight:normal">'
                                                    '<br> ({} / {})'
                                                    '</span>'.format(
                                                        i, i+1, benoetigt, zugewiesen),
                                                    ))

    return NameTableFactory("StundenplanEdit",
                            newattrs, l,
                            meta={'sequence': ('last_name',
                                               'first_name',
                                               'anzahl',
                                               '...')}
                            )

##############################


class AufgabenTable (django_tables2.Table):
    verantwortlicher = KontaktColumn(
        accessor="verantwortlich",
        verbose_name="Verantwortlicher")

    meldungen = django_tables2.Column(
        verbose_name="Vorliegende Meldungen",
        empty_values=(),
        orderable=False,
        )

    zuteilungen = django_tables2.Column(
        verbose_name="Erfolgte Zuteilungen",
        empty_values=(),
        orderable=False,
        )

    quickmeldung = django_tables2.Column(
        verbose_name="Quickmeldung",
        empty_values=(),
        orderable=False,
        )

    def render_meldungen(self, record):
        # return record.meldung_set.count()
        return record.numMeldungen()

    def render_zuteilungen(self, record):
        return record.zuteilung_set.count()

    def render_quickmeldung(self, record):
        user = self.context["request"].user

        try: 
            meldung = record.meldung_set.get(melder=user)
            meldung_exists = (meldung.bemerkung !=  models.Meldung.MODELDEFAULTS['bemerkung'] or
                              meldung.prefMitglied != models.Meldung.MODELDEFAULTS['prefMitglied'])
        except:
            meldung_exists = False

        return mark_safe('<a href="{}"> <i class="fa fa-hand-o-up fa-fw"></i></a> {}'.format(
            reverse('arbeitsplan-quickmeldung', args=[record.id]),
            '<i class="fa fa-check fa-fw"></i>' if meldung_exists else "",
            ))

    class Meta:
        model = models.Aufgabe
        attrs = {"class": "paleblue"}
        # fields=("aufgabe", "datum",
        # django_tables2.A("verantwortlich.last_name"),
        # "gruppe", "anzahl", "bemerkung")

        fields = ("gruppe", "aufgabe", "datum",
                  "stunden",
                  "anzahl",
                  "bemerkung",
                  "verantwortlicher",
                  "quickmeldung",
                  )

        exclude = ("meldungen", "zuteilungen", )


class AufgabenTableVorstand(django_tables2.Table):
    verantwortlicher = KontaktColumn(
        accessor="verantwortlich",
        verbose_name="Verantwortlicher")

    id = django_tables2.LinkColumn(
        'arbeitsplan-aufgabenEdit',
        args=[A('pk')],
        verbose_name="Editieren/ Löschen")

    meldungen = django_tables2.Column(
        verbose_name="Vorliegende Meldungen",
        empty_values=(),
        orderable=False,
        )

    zuteilungen = django_tables2.Column(
        verbose_name="Erfolgte Zuteilungen",
        empty_values=(),
        orderable=False,
        )

    fehlende_zuteilungen = django_tables2.Column(
        verbose_name="Noch offene Zuteilungen",
        empty_values=(),
        orderable=False,
        )

    def render_meldungen(self, record):
        # return record.meldung_set.count()
        return record.numMeldungen()

    def render_zuteilungen(self, record):
        return record.zuteilung_set.count()

    def render_fehlende_zuteilungen(self, record):
        return record.anzahl - record.zuteilung_set.count()

    class Meta:
        model = models.Aufgabe
        attrs = {"class": "paleblue"}

        # fields=("aufgabe", "datum",
        # django_tables2.A("verantwortlich.last_name"),
        # "gruppe", "anzahl", "bemerkung")

        fields = ("id",
                  "gruppe", "aufgabe", "datum",
                  "stunden",
                  "anzahl",
                  "meldungen",
                  "zuteilungen", "fehlende_zuteilungen",
                  "bemerkung",
                  'verantwortlicher',
                  )

        # TODO: anzahl muss man wahrscheinlich
        # auf die ANzahl FREIE Plaetze umrechnen!?!?


class AufgabengruppeTable(django_tables2.Table):

    id = django_tables2.LinkColumn('arbeitsplan-aufgabengruppeEdit',
                                   args=[A('pk')],
                                   verbose_name="Editieren",
                                   )

    verantwortlich = KontaktColumn()

    class Meta:
        model = models.Aufgabengruppe
        attrs = {"class": "paleblue"}
        fields = ('gruppe', 'verantwortlich', 'bemerkung', 'id', )
        # exclude = ('id',)


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


class ZuteilungTable(django_tables2.Table):
    ## verantwortlicher = django_tables2.Column(
    ##     accessor="aufgabe.verantwortlich.last_name",
    ##     verbose_name="Verantwortlicher")

    verantwortlicher = KontaktColumn(
        accessor="aufgabe.kontakt",
        verbose_name="Verantwortlicher",
        orderable=False,
        )

    datum = django_tables2.Column(accessor="aufgabe.datum",
                                  verbose_name="Datum")

    studenString = django_tables2.Column(
        verbose_name="Zeiten",
        accessor='stundenString',
        )

    class Meta:
        model = models.Zuteilung
        attrs = {"class": "paleblue"}

        fields = ("aufgabe", 'verantwortlicher', 'datum',
                  # 'stundenString',
                  )


class ZuteilungTableVorstand(django_tables2.Table):
    verantwortlicher = KontaktColumn(
        accessor="aufgabe.verantwortlich",
        verbose_name="Verantwortlicher")

    datum = django_tables2.Column(
        accessor="aufgabe.datum",
        verbose_name="Datum")

    ausfuehrer = KontaktColumn(accessor="ausfuehrer",
                               verbose_name="Ausführer")

    class Meta:
        model = models.Zuteilung
        attrs = {"class": "paleblue"}

        fields = ("aufgabe", 'verantwortlicher', 'datum', 'ausfuehrer')

##############################


class MeldungListeTable(django_tables2.Table):
    """A table to only display all Meldungen of a user.
    """

    aufgabenGruppe = django_tables2.Column(accessor="aufgabe.gruppe.gruppe",
                                           verbose_name="Aufgabengruppe")
    aufgabeName = django_tables2.Column(accessor="aufgabe.aufgabe",
                                        verbose_name="Aufgabe")
    aufgabenDatum = django_tables2.Column(accessor="aufgabe.datum",
                                          verbose_name="Datum")

    class Meta:
        model = models.Meldung
        attrs = {"class": "paleblue"}

        fields = ("aufgabenGruppe",
                  "aufgabeName",
                  "aufgabenDatum",
                  "prefMitglied",
                  "bemerkung",
                  )
        exclude = ("id", "erstellt", "veraendert",
                   "prefVorstand", "bemerkungVorstand",
                   )


class MeldungTable(RadioButtonTable):
    """A table to edit Meldungen.
    """
    # id = django_tables2.Column ()

    aufgabe = django_tables2.Column(accessor="aufgabe",
                                    verbose_name="Aufgabe")
    gruppe = django_tables2.Column(accessor="gruppe",
                                   verbose_name="Aufgabengruppe")

    datum = django_tables2.Column(accessor="datum",
                                  verbose_name="Datum")

    stunden = django_tables2.Column(accessor="stunden",
                                    verbose_name="Umfang (h)")

    prefMitglied = django_tables2.Column(accessor="prefMitglied",
                                         verbose_name="Vorlieben",
                                         empty_values=(),
                                         )

    bemerkung = django_tables2.Column(accessor="bemerkung",
                                      verbose_name="Bemerkung",
                                      empty_values=(),
                                      )

    anzahl = django_tables2.Column(
        verbose_name="Benötigte Helfer",
        empty_values=(),
        )

    meldungen = django_tables2.Column(
        verbose_name="Vorliegende Meldungen",
        empty_values=(),
        )

    zuteilungen = django_tables2.Column(
        verbose_name="Erfolgte Zuteilungen",
        empty_values=(),
        )

    fehlende_zuteilungen = django_tables2.Column(
        verbose_name="Noch offene Zuteilungen",
        empty_values=(),
        )

    def render_aufgabe(self, value, record):
        aufgabe = record['aufgabeObjekt']
        tooltext = mark_safe(u'Verantwortlicher: {0} {1}{2}'.format(
            aufgabe.verantwortlich.first_name,
            aufgabe.verantwortlich.last_name,
            u', Bemerkung: {0}'.format(
                aufgabe.bemerkung) if aufgabe.bemerkung else '',
            ))
        tmp = mark_safe(
            u'<div class="tooltip-demo">'
            '<a href="{0}"'
            'data-toggle="tooltip"'
            'title="{2}"'
            '>{1}</a></div>'.format(
                '#',
                value,
                tooltext,
                )
            )

        return tmp

    def render_prefMitglied(self, value, record):
        return self.render_radio(
            choices=models.Meldung.PRAEFERENZ,
            buttontexts=models.Meldung.PRAEFERENZButtons,
            fieldname="prefMitglied",
            record=record,
            )

    def render_bemerkung(self, value, record, bound_row):
        # print record
        # print bound_row
        tmp = format_html(
            u"""<textarea class="textinput textInput"
            id="id_bemerkung_{0}" name="bemerkung_{0}"
            placeholder="Bemerkung eingeben" rows=6>{1}</textarea>""",
            str(record['id']),
            record['bemerkung'] if record['bemerkung'] else ""
            )

        return tmp

    class Meta:

        # model = models.Aufgabe
        attrs = {"class": "paleblue"}

        fields = ('gruppe', 'aufgabe', 'datum',
                  'stunden',
                  'anzahl',
                  "meldungen",
                  'bemerkung',
                  'prefMitglied')

        exclude = ("fehlende_zuteilungen", 'zuteilungen')


class MeldungTableVorstand (RadioButtonTable):

    aufgabe = django_tables2.Column(accessor="aufgabe",
                                    verbose_name="Aufgabe")

    gruppe = django_tables2.Column(accessor="aufgabe.gruppe",
                                   verbose_name="Aufgabengruppe")

    datum = django_tables2.Column(accessor="aufgabe.datum",
                                  verbose_name="Datum")

    stunden = django_tables2.Column(accessor="aufgabe.stunden",
                                    verbose_name="Umfang (h)")

    prefMitglied = django_tables2.Column(accessor="prefMitglied",
                                         verbose_name="Vorlieben Melder",
                                         empty_values=(),
                                         )

    bemerkung = django_tables2.Column(accessor="bemerkung",
                                      verbose_name="Bemerkung Melder",
                                      empty_values=(),
                                      )

    ## melder_last = django_tables2.Column (accessor="melder.last_name",
    ##                                      verbose_name="Melder Nachname")
    ## melder_first = django_tables2.Column (accessor="melder.first_name",
    ##                                      verbose_name="Melder Vorname")

    melder = KontaktColumn(accessor="melder",
                           verbose_name="Melder",
                           # order_by=("melder.last_name", "melder.first_name"),
                           )

    ## bemerkungVorstand = django_tables2.Column (accessor="bemerkungVorstand",
    ##                                     verbose_name="Bemerkung Vorstand",
    ##                                     empty_values=(), 
    ##                                     )

    bemerkungVorstand = django_tables2.Column(
        empty_values=(),
        verbose_name="Bemerkungen des Vorstandes")

    prefVorstand = django_tables2.Column(
        accessor="prefVorstand",
        verbose_name="Vorlieben des Vorstandes",
        empty_values=(),
        )

    def render_prefVorstand(self, value, record):

        return self.render_radio(
            choices=models.Meldung.PRAEFERENZ,
            buttontexts=models.Meldung.PRAEFERENZButtons,
            fieldname="prefVorstand",
            record=record)

    def render_bemerkungVorstand (self, value, record):
        tmp =  format_html (u'<textarea class="textinput textInput" id="id_bemerkungVorstand_{0}" name="bemerkungVorstand_{0}" placeholder="Bemerkung Vorstand" rows=6>{1}</textarea>',
                            str(record.id),
                            record.bemerkungVorstand if record.bemerkungVorstand else ""
                            )
        return tmp


    class Meta(MeldungTable.Meta):
        model = models.Meldung 
        fields = ('gruppe', 'aufgabe', 'datum', 'stunden',
                  # 'melder_last', 'melder_first',
                  'melder',
                  'bemerkung', 'prefMitglied',
                  'bemerkungVorstand', 'prefVorstand')
        exclude = ('melder_last', 'melder_first',)

##############################

def SaldenTableFactory (l):

    attrs = {}
    for s in models.Leistung.STATUS:
        attrs[s[0]] = LinkedColumn(verbose_name=s[1] + ' (h)')

    attrs['zugeteilt'] = LinkedColumn(verbose_name="Zugeteilt insgesamt (h)")
    attrs['past'] = django_tables2.Column(
        verbose_name="Zuteilungen vergangener Aufgaben (h)")
    attrs['future'] = django_tables2.Column(
        verbose_name="Zuteilungen zukünftiger Aufgaben (h)")
    attrs['nodate'] = django_tables2.Column(
        verbose_name="Zuteilungen Aufgaben ohne Datum (h)")

    t = NameTableFactory("salden", attrs, l,
                         kontakt=('user', 'Mitglied'),
                         meta={'sequence': ('kontakt',
                             ## 'last_name',
                             ##                'first_name',
                                            'zugeteilt',
                                            'past',
                                            'future',
                                            'nodate',
                                            '...')
                               })
    return t

##############################


def ZuteilungsTableFactory (tuple):
    l, aufgabenQs = tuple

    attrs = {}

    attrs['zugeteilt'] = django_tables2.Column(verbose_name=
                                               "Bereits zugeteilt (h)")

    for a in aufgabenQs:
        tag = (unicodedata.normalize('NFKD',
                                    a.aufgabe).encode('ASCII', 'ignore')
               )
        attrs[tag] = ValuedCheckBoxColumn(
            verbose_name=mark_safe((u'<a href="{}">{}</a>, {}h'
                                    '<span style="font-weight:normal">'
                                    u'<br>({})'
                                    u'<br>Benötigt: {}'
                                    u'<br>Zugeteilt: {}'
                                    u'{}'
                                    '</span>'
                                    .format(reverse('arbeitsplan-aufgabenEdit',
                                                    args=(a.id,)),
                                            a.aufgabe,
                                            a.stunden,
                                            a.gruppe,
                                            a.anzahl,
                                            a.zuteilung_set.count(),
                                            # the following expression is the same as appears in
                                            # the ZuteilungUebersichtView
                                            # TODO: perhaps move that to class aufgabe, to produce an edit link
                                            # to its stundenplan if it exists? 
                                            ('<br>' + mark_safe(u'<a href="{0}">Stundenplan</a>'
                                                                .format(reverse ('arbeitsplan-stundenplaeneEdit',
                                                                                 args=(a.id,)),
                                                                                 ))
                                             if a.has_Stundenplan()
                                             else ''
                                                )
                                    ))),
            orderable=False)
    # TODO: in verbose_name hier noch Anzahl benötigt, anzahl zugeteilt eintragen


    t = NameTableFactory('ZuteilungsTable', attrs, l,
                         kontakt=('mitglied', 'Mitglied'))

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

    aufgabe = django_tables2.Column(accessor="aufgabe.aufgabe",
                                    verbose_name="Aufgabe")

    class Meta:
        model = models.Leistung
        attrs = {"class": "paleblue"}
        fields = (  # 'melder_last', 'melder_first',
                    'aufgabe', 'wann', 'zeit',
                    'status',
                    'bemerkung', 'bemerkungVorstand')

class LeistungBearbeitenTable (RadioButtonTable):

    def render_bemerkungVorstand (value, bound_row):
        tmp =  format_html (u'<textarea class="textinput textInput" id="id_bermerkungVorstand_{0}" name="bemerkungVorstand_{0}" placeholder="Bemerkung Vorstand" rows=6>{1}</textarea>',
                            str(bound_row._record.id),
                            bound_row._record.bemerkungVorstand,
                            )
        return tmp


    def render_status (self, value, bound_row):
        return self.render_radio(bound_row=bound_row,
                                 choices=models.Leistung.STATUS,
                                 buttontexts=models.Leistung.STATUSButtons,
                                 fieldname="status")

    bemerkungVorstand = django_tables2.Column(empty_values=(),
                                              verbose_name = "Bemerkungen des Vorstandes")

    melder = KontaktColumn()

    class Meta:
        model = models.Leistung
        attrs = {"class": "paleblue"}
        exclude = ("erstellt", "veraendert", 'id', 'benachrichtigt')        
        sequence = ('melder', 'aufgabe', 'wann', 'zeit', 
                    'bemerkung', 'status', 'bemerkungVorstand')


class BaseEmailTable (RadioButtonTable):

    anmerkung = django_tables2.Column(empty_values=(),
                                      verbose_name="Individuelle Anmerkung",
                                      )

    sendit = django_tables2.Column(verbose_name="Senden?",
                                           accessor="sendit",
                                           orderable=False,
                                           empty_values=(),
                                           )

    def render_sendit(value, bound_row):
        tmp = format_html(u'<div class="checkbox"> <input name="sendit_{0}" type="checkbox" {1}></div>',
                          str(bound_row._record.id),
                          "checked" if bound_row._record.sendit else "",
                          )
        return tmp

    def render_anmerkung(value, bound_row):
        tmp = format_html (u'<textarea class="textinput textInput" id="id_anmerkung_{0}"'
                            ' name="anmerkung_{0}" placeholder="Individuelle Anmerkung"'
                            ' rows=4>{1}</textarea>',
                            str(bound_row._record.id),
                            bound_row._record.anmerkung,
                            )
        return tmp

class LeistungEmailTable(BaseEmailTable):

    # a purely computed field: 
    schonbenachrichtigt = django_tables2.Column (verbose_name="Schon benachrichtigt?",
                                            orderable=False,
                                            empty_values=(),
                                            )

    def render_schonbenachrichtigt(value, bound_row):
        return ("Ja"
                if (bound_row._record.veraendert <
                    bound_row._record.benachrichtigt)
                else "Nein")

    melder = KontaktColumn()

    class Meta:
        model = models.Leistung
        attrs = {"class": "paleblue"}
        exclude = ("erstellt", "veraendert", 'id', 'benachrichtigt')
        sequence = ('melder', 'aufgabe', 'wann', 'zeit',
                    'bemerkung', 'status', 'bemerkungVorstand',
                    'schonbenachrichtigt',
                    'anmerkung', 'sendit'
                    )

class ZuteilungEmailTable(BaseEmailTable):

    user = KontaktColumn(verbose_name="Mitglied")

    zuteilungBenachrichtigungNoetig = django_tables2.Column(verbose_name="Nötig?",
                                                            orderable=False,
                                                            empty_values=(),
                                                            )

    def render_zuteilungBenachrichtigungNoetig(value, bound_row):
        return ("Ja"
                if bound_row._record.zuteilungBenachrichtigungNoetig
                else "Nein")

    class Meta:
        model = models.Mitglied
        attrs = {"class": "paleblue"}
        exclude = ('id',
                   'mitgliedsnummer',
                   'zustimmungsDatum',
                   'geburtsdatum',
                   'strasse',
                   'plz',
                   'gender',
                   'ort',
                   'erstbenachrichtigt',
                   'festnetz',
                   'mobil',
                   )
        sequence = ('user',
                    'zuteilungsbenachrichtigung',
                    'zuteilungBenachrichtigungNoetig',
                    'anmerkung', 'sendit',
                    )

class MeldungsAufforderungsEmailTable(BaseEmailTable):

    user = KontaktColumn(verbose_name="Mitglied")

    numMeldungen = django_tables2.Column(verbose_name="# Meldungen",
                                         orderable=False,
                                         empty_values=(),
                                         )

    numZuteilungen = django_tables2.Column(verbose_name="# Zuteilungen",
                                         orderable=False,
                                         empty_values=(),
                                         )
    
    stundenZuteilungen = django_tables2.Column(verbose_name="Zuteilungen (Stunden)",
                                         orderable=False,
                                         empty_values=(),
                                         )
    
    def render_numMeldungen(value, bound_row):
        return (bound_row._record.gemeldeteAnzahlAufgaben())
    
    def render_numZuteilungen(value, bound_row):
        return (bound_row._record.zugeteilteAufgaben())
    
    def render_stundenZuteilungen(value, bound_row):
        return (bound_row._record.zugeteilteStunden())
    
    class Meta:
        model = models.Mitglied
        attrs = {"class": "paleblue"}
        exclude = ('id',
                   'mitgliedsnummer',
                   'zustimmungsDatum',
                   'geburtsdatum',
                   'strasse',
                   'plz',
                   'gender',
                   'ort',
                   'erstbenachrichtigt',
                   'festnetz',
                   'mobil',
                   'zuteilungsbenachrichtigung',
                   'zuteilungBenachrichtigungNoetig',
                   )
        sequence = ('user',
                    'numMeldungen',
                    'numZuteilungen',
                    'stundenZuteilungen',
                    'anmerkung', 'sendit',
                    )

        

class ImpersonateTable(django_tables2.Table):

    ## first_name = django_tables2.Column (accessor="user.first_name")
    ## last_name = django_tables2.Column (accessor="user.last_name")

    mitgliedsnummer = django_tables2.Column(accessor="mitglied.mitgliedsnummer")

    id = django_tables2.LinkColumn('impersonate-start',
                                   args=[A('pk')],
                                   verbose_name="Nutzer darstellen",
                                   )

    class Meta:
        model = User

        attrs = {"class": "paleblue"}
        fields = ('first_name',
                  'last_name',
                  'mitgliedsnummer',
                  'id',
                  )

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
