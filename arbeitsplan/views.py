# -*- coding: utf-8 -*-

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import View, ListView, CreateView
from django.views.generic import FormView, UpdateView, DeleteView
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, F, Count
from django.contrib.auth import logout
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command

from collections import defaultdict
from post_office import mail

import datetime
from django.utils.timezone import utc

from pprint import pprint as pp

import django_tables2
import unicodedata

import types 
import collections
import os

# Arbeitsplan-Importe: 
import models
import forms
from tables import *  # TODO: change import not to polute name space
from svpb.settings import JAHRESSTUNDEN, STATIC_ROOT, SENDFILE_ROOT

from sendfile import sendfile

#################

def isVorstand(user):
    return user.groups.filter(name='Vorstand')

def isTeamlead(user):
    return user.teamleader_set.count() > 0 

def isVorstandOrTeamleader(user):
    return isVorstand(user) or isTeamlead(user)

class isVorstandMixin(object):
    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def dispatch(self, *args, **kwargs):
        return super(isVorstandMixin, self).dispatch(*args, **kwargs)

class isVorstandOrTeamleaderMixin(object):
    @method_decorator(user_passes_test(isVorstandOrTeamleader, login_url="/keinVorstand/"))
    def dispatch(self, *args, **kwargs):
        return super(isVorstandOrTeamleaderMixin, self).dispatch(*args, **kwargs)


###############


def logout_view(request):
    # print "logout view"
    logout(request)
    return render(request, "registration/logged_out.html", {})

###############


class FilteredListView(ListView):
    """A fairly generic way of specifying a view that returns a table
    that can be filtered, along specified fields.
    """

    # Specify the following:
    title = ""
    template_name = "arbeitsplan_tff.html"
    tableClass = None
    tableClassFactory = None
    tabletitle = None

    tableform = None
    # tableform should be dict with keys: name, value for the submit button

    tableformHidden = []

    filtertitle = None
    filterform_class = None
    filterconfig = []
    # filterconfig: a list of tuples,
    # with (fieldnmae in form, filter keyword to apply)

    # help texts for the page template
    intro_text = ""
    post_text = ""
    todo_text = ""
    discuss_text = ""

    # pass additional context into template, if given.
    # must  be dictionary
    context = {}

    # fallback, if no actual data is provided:
    model = None

    # Only as variable needed:
    filterform = None  # yes, this should be an instance variable, to pass around 

    def get_context_data(self, **kwargs):
        context = super(FilteredListView, self).get_context_data()
        context['title'] = self.title
        context['filterform'] = self.filterform
        context['filtertitle'] = self.filtertitle
        context['tabletitle'] = self.tabletitle
        context['tableform'] = self.tableform

        context['tableformHidden'] = self.tableformHidden
        context['fullpath'] = self.request.get_full_path()

        context['intro_text'] = mark_safe(self.intro_text)
        context['post_text'] = mark_safe(self.post_text)

        if isVorstand(self.request.user):
            context['todo_text'] = mark_safe(self.todo_text)
            context['discuss_text'] = mark_safe(self.discuss_text)

        context.update(self.context)
        return context

    def apply_filter(self, qs=None):
        """process filterconfig: a list of pairs of strings
        - first string: field name to be handled in filterform
        - second string: filter expression; clenead data of the
           first string is passed as parameter.
           (if empty, do not apply filter, just process the form.
           useful to subclasses overriding this method)
        """

        if qs is None:
            qs = self.model.objects.all()

        if 'filter' not in self.request.GET:
            if self.filterform_class: 
                self.filterform = self.filterform_class()
                filterconfig = []
                fieldsWithInitials = [k
                                      for k, v
                                      in self.filterform.fields.iteritems()
                                      if v.initial is not None]
                filterconfig = [(x[0], x[1], self.filterform.fields[x[0]].initial)
                                for x in self.filterconfig
                                if x[0] in fieldsWithInitials]

                for fieldname, filterexp, initialValues in filterconfig:
                    if isinstance(filterexp, basestring):
                        qs = qs.filter(**{filterexp: initialValues})
                    elif isinstance(filterexp, types.FunctionType):
                        qs = filterexp(self,
                                       qs,
                                       initialValues)
                    else:
                        print "warning: filterxpression not recognized"
        else:
            self.filterform = self.filterform_class(self.request.GET)
            filterconfig = self.filterconfig

            if self.filterform.is_valid():
                # apply filters
                # print "filter: ", self.filterform.cleaned_data
                for fieldname, filterexp in filterconfig:
                    # print fieldname, filterexp
                    if ((self.filterform.cleaned_data[fieldname] is not None) and
                        (self.filterform.cleaned_data[fieldname] != "")):
                        if isinstance(filterexp, basestring):
                            qs = qs.filter(**{filterexp:
                                              self.filterform.cleaned_data[fieldname]})
                        elif isinstance(filterexp, types.FunctionType):
                            qs = filterexp(self,
                                           qs,
                                           self.filterform.cleaned_data[fieldname])
                        else:
                            print "warning: filterxpression not recognized"
                            print filterexp
            else:
                print "filterform not valid"

        return qs

    def get_filtered_table(self, qs):
        if self.tableClassFactory:
            f = self.tableClassFactory
            table = f(qs)
        else:
            table = self.tableClass(qs)
        django_tables2.RequestConfig(self.request).configure(table)

        return table

    def get_data(self):
        """Provide the data to be used in the get_queryset.
        Defaults here to return all data of the model; typically overwritten in
        derived classes.
        """

        return self.model.objects.all()

    def annotate_data(self, qs):
        """Once the data has been obtained and filtered,
        use this method to further annotate it.
        Typically turns the queryset into a list of dictionaries
        """

        return qs

    def get_queryset(self):
        """standard way of displaying a filtered table,
        might have to be overwritten if some non-standard
        processing is necessary,
        e.g., to determine the table depending on user role
        """
        qs = self.get_data()
        qs = self.apply_filter(qs)
        qs = self.annotate_data(qs)
        table = self.get_filtered_table(qs)
        return table


###############


#######################################################################
#   AUFGABEN
#######################################################################


class AufgabenUpdate (SuccessMessageMixin, UpdateView):
    model = models.Aufgabe
    form_class = forms.AufgabeForm
    template_name = "arbeitsplan_aufgabenCreate.html"
    # success_url = "home.html"
    success_url = reverse_lazy("arbeitsplan-aufgaben")
    success_message = 'Die  <a href="%(url)s">Aufgabe %(id)s</a> wurde erfolgreich verändert.'
    title = "Aufgabe ändern"
    buttontext = "Änderung eintragen"

    def get_success_message(self, cleaned_data):
        """See documentation at:
        https://docs.djangoproject.com/en/1.6/ref/contrib/messages/
        """
        msg = mark_safe(self.success_message % dict(cleaned_data,
                                                    url = reverse('arbeitsplan-aufgabenEdit',
                                                                  args=(self.object.id,)), 
                                                      id=self.object.id))

        # messages.warning(self.request, "aber komisch ist die schon")

        # print "succesS_msg: ", msg
        return msg

    def get_context_data(self, **kwargs):
        context = super(AufgabenUpdate, self).get_context_data(**kwargs)
        context['title'] = self.title
        context['buttontext'] = self.buttontext

        # hier Stundenplanwerte aus DB holen
        # a dict with default values, to be overwirtten with
        # values from data base
        # then converted back into a list to be passed into the template
        stundenplan = dict([(u, 0) for u in range(models.Stundenplan.startZeit,
                                                  models.Stundenplan.stopZeit+1)])
        for s in models.Stundenplan.objects.filter(aufgabe=self.object):
            stundenplan[s.uhrzeit] = s.anzahl

        context['stundenplan'] = stundenplan.items()

        context['loeschknopf'] = self.object.verantwortlich ==  self.request.user

        return context

    def get_form_kwargs(self):
        kwargs = super(AufgabenUpdate, self).get_form_kwargs()
        kwargs.update({
            'request': self.request
            })
        return kwargs

    def form_valid(self, form):

        if '_delete' in self.request.POST:
            print "redirecting to delete", self.object.id
            return redirect('arbeitsplan-aufgabenDelete',
                            pk=self.object.id)

        # store the aufgabe
        super(AufgabenUpdate, self).form_valid(form)

        # manipulate the stundenplan
        stundenplan = collections.defaultdict(int,
                                              form.cleaned_data['stundenplan'])
        print "stundenplan: ", stundenplan 
        for u in range(models.Stundenplan.startZeit,
                       models.Stundenplan.stopZeit+1):
            anzahl = stundenplan[u]
            sobj, created = models.Stundenplan.objects.update_or_create(
                aufgabe=self.object,
                uhrzeit=u,
                defaults={'anzahl': anzahl})

        return redirect(self.request.get_full_path())


class AufgabeLoeschen(DeleteView):
    model = models.Aufgabe
    success_url = reverse_lazy('arbeitsplan-aufgaben')
    template_name = "aufgabe_confirm_delete.html"

    def get_object(self, queryset=None):
        obj = super(AufgabeLoeschen, self).get_object()
        if not obj.verantwortlich == self.request.user:
            from django.http import Http404
            # TODO: nicer error message
            messages.error(self.request,
                           "Sie dürfen diese Aufgabe nicht löschen! Nur der verantworliche Vorstand darf das!")
            raise Http404
        return obj

    def get(self, request, *args, **kwargs):
        try:
            r = super(AufgabeLoeschen, self).get(request, *args, **kwargs)
            messages.success(self.request,
                             "Die Aufgabe wurde erfolgreich gelöscht.")
            return r
        except:
            return redirect('arbeitsplan-aufgaben')


###############################

class ListAufgabenView (FilteredListView):

    # filterform_class = forms.AufgabengruppeFilterForm
    filterform_class = forms.AufgabenDatumFilter
    title = "Alle Aufgaben anzeigen"
    filtertitle = "Filter nach Aufgabengruppe oder Zeitintervall"
    tabletitle = "Aufgabenliste"
    filterconfig = [('aufgabengruppe', 'gruppe__gruppe'),
                    ('von', 'datum__gte'),
                    ('bis', 'datum__lte'),
                    ]
    model = models.Aufgabe
    intro_text = """
    Die Tabelle zeigt die anstehenden Aufgaben an.
    <ul>
    <li> Aufgaben ohne Datum sind an flexiblen Terminen zu erledigen. </li>
    <li> Bei Aufgaben mit Datum  erfolgt die Zeitabsprachen individuell oder nach Einteilung. </li> 
    <li> Die Spalte Verantwortlicher benennt den Koordinator der Aufgabe. </li>
    <li> Die Spalte Quickmeldung erlaubt eine vereinfachte Meldung für eine Aufgabe. Klicken Sie auf das Handsymbol; ein Haken in der Zeile markiert Aufgaben, für die Sie sich gemeldet haben.</li>
    </ul>
    """
    ## todo_text = """
    ## <li> Spalten klickbar machen: Aufgabe, Verantowrtlicher (direkt email senden?)  </li>
    ## <li> Bemerkung als Popover umbauen?  </li>  
    ## """

    def get_filtered_table(self, qs):

        if isVorstand(self.request.user):
            self.tableClass = AufgabenTableVorstand
        else:
            self.tableClass = AufgabenTable

        table = super(ListAufgabenView, self).get_filtered_table(qs)

        # return self.get_filtered_table (self.model.objects.all())
        return table 

#####################


class SimpleCreateView(CreateView):

    def get_context_data(self, **kwargs):
        context = super(SimpleCreateView, self).get_context_data(**kwargs)
        context['title'] = self.title
        context['buttontext'] = self.buttontext

        return context

class SimpleUpdateView(UpdateView):

    def get_context_data(self, **kwargs):
        context = super(SimpleUpdateView, self).get_context_data (**kwargs)
        context['title'] = self.title
        context['buttontext'] = self.buttontext

        return context


################################################

class AufgabenCreate (isVorstandMixin, SimpleCreateView):
    model = models.Aufgabe
    form_class = forms.AufgabeForm
    template_name = "arbeitsplan_aufgabenCreate.html"
    success_url = reverse_lazy("home")
    title = "Neue Aufgabe anlegen"
    buttontext = "Aufgabe anlegen"

    def get_form_kwargs(self):
        kwargs = super(SimpleCreateView, self).get_form_kwargs()
        kwargs.update({
            'request': self.request
            })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(AufgabenCreate, self).get_context_data(**kwargs)
        context['stundenplan'] = [(u, 0)
                                  for u in range(
                                      models.Stundenplan.startZeit,
                                      models.Stundenplan.stopZeit+1)]
        return context

    def form_valid(self, form):

        # store the aufgabe
        super(AufgabenCreate, self).form_valid(form)

        # and now store the STundenplan entries
        for uhrzeit, anzahl  in form.cleaned_data['stundenplan'].iteritems():
            sobj = models.Stundenplan (aufgabe = self.object,
                                       uhrzeit = uhrzeit,
                                       anzahl = anzahl)
            sobj.save()

        messages.success(self.request,
                         "Die Aufgabe wurde erfolgreich angelegt."
                         )

        return super(AufgabenCreate, self).form_valid(form)

    def form_invalid(self, form):
        """When the form is invalid, the normal processing scheme forgets
        the stunden added to the stundenplan. They ARE in the querydict,
        but we have to put them back into the context
        explcitily, as the normal get_context_data simply writes an empty list.
        TODO: check whether the pulling in from the querydict
        shouldn't be more elegantly done in the get_context_data; that's
        where it really belongs. 
        """
        # print "Aufgabe Create, form invalid"

        # add the uhrzeiten from querydict back into the context !?
        context = self.get_context_data(form=form)
        stundenplandict = dict(context['stundenplan'])
        # print 'std before: ', stundenplandict
        for k, v in self.request.POST.iteritems():
            print k, v
            try:
                u, uu = k.split('_')
                stundenplandict[int(uu)] = int(v)
            except Exception as e:
                # print "problem: ", e
                pass

        context['stundenplan'] = [(k, v)
                                  for k, v
                                  in stundenplandict.iteritems()]

        return self.render_to_response(context)
        # return super(AufgabenCreate, self).form_invalid(form)

class AufgabengruppeCreate(isVorstandMixin, SimpleCreateView):
    model = models.Aufgabengruppe
    success_url = reverse_lazy("home")
    title = "Neue Aufgabengruppe anlegen"
    buttontext = "Aufgabengruppe anlegen"
    template_name = "arbeitsplan_aufgabengruppeCreate.html"
    form_class = forms.AufgabengruppeForm

class AufgabengruppeList(isVorstandMixin, FilteredListView):
    title = "Aufgabegruppen"
    tableClass = AufgabengruppeTable
    intro_text = "Übersicht über alle Aufgabengruppe."
    model = models.Aufgabengruppe


class AufgabengruppeUpdate(isVorstandMixin, SimpleUpdateView):
    model = models.Aufgabengruppe
    template_name = "arbeitsplan_aufgabengruppeCreate.html"
    title = "Aufgabengruppe ändern"
    form_class = forms.AufgabengruppeForm
    buttontext = "Aufgabengruppe ändern"
    success_url = reverse_lazy("arbeitsplan-aufgabengruppeList")

    def form_valid (self, form):
        messages.success(self.request,
                         "Die Aufgabengruppe wurde erfolgreich "
                         "editiert")

        return super(AufgabengruppeUpdate, self).form_valid(form)


########################################################################################
#########   MELDUNG 
########################################################################################

class MeldungEdit (FilteredListView):

    def processUpdate (self, request):
        for k, value in request.POST.iteritems():
            if (k.startswith('bemerkung') or
                k.startswith('prefMitglied') or
                k.startswith('prefVorstand') 
                ):
                key, id = k.split('_', 1)

                id = int(id)

                safeit = False

                try:
                    m = models.Meldung.objects.get(id=id)
                except models.Meldung.DoesNotExist:
                    print "consistency of dsatabase destryoed"
                    # TODO: display error 
                    continue 

                if key == 'bemerkung':
                    if m.bemerkung <> value: 
                        m.bemerkung = value
                        safeit = True
                        messages.success(request,
                                         u"Bei Aufgabe {0} wurde die Bemerkung aktualisiert".
                                         format(str(id)))

                if key == 'bemerkungVorstand' and isVorstand(self.request.user):
                    if m.bemerkungVorstand <> value: 
                        m.bemerkungVorstand = value
                        safeit = True
                        messages.success(request,
                                         u"Bei Aufgabe {0} wurde die Bemerkung des Vorstandes aktualisiert".
                                         format(str(id)))

                if key == 'prefMitglied':
                    if m.prefMitglied <> value:
                        m.prefMitglied  = value
                        safeit = True
                        messages.success(request,
                                         u"Bei Aufgabe {0} wurde die Präferenz aktualisiert".
                                         format(str(id)))

                if key == 'prefVorstand' and isVorstand(self.request.user):
                    if m.prefVorstand <> value:
                        m.prefVorstand  = value
                        safeit = True
                        messages.success(request,
                                         u"Bei Aufgabe {0} wurde die Präferenz des Vorstandes aktualisiert".
                                         format(str(id)))

                if safeit:
                    m.save()
            else:
                # not interested in those keys
                pass


class CreateMeldungenView (MeldungEdit):
    """
    Display a table with all Aufgaben and fields
    to set preferences and add remarks.
    Accept updates and enter them into the Meldung table.
    Intended for the non-Vorstand user.
    """

    title = "Meldungen für Aufgaben eintragen oder ändern"
    # filterform_class = forms.AufgabengruppeFilterForm
    filterform_class = forms.AufgabenDatumFilter
    filtertitle = "Meldungen nach Aufgabengruppen filtern"
    tabletitle = "Meldungen für Aufgaben eintragen oder ändern"
    tableform = {'name': "eintragen",
                 'value': "Meldungen eintragen/ändern"}
    filterconfig = [('aufgabengruppe', 'gruppe__gruppe'),
                    ('von', 'datum__gte'),
                    ('bis', 'datum__lte'),
                    ]
    model = models.Aufgabe
    tableClass = MeldungTable

    intro_text = """
    Tragen Sie bitte ein, an welchen Aufgaben Sie mitarbeiten möchten.
    Wählen Sie dazu für die entsprechende Aufgabe eine entsprechende
    Vorliebe in der letzen Spalte aus (oder lassen Sie die Vorliebe
    auf `Nein'). Sie können noch zusätlich eine Bemerkung eingeben
    (z.B., wenn Sie die Aufgaben mit einem Partner zusammenarbeiten
    erledigen möchten oder nur zu bestimmten Uhrzeiten können).
    <p>
    Sie können die Aufgabenliste eingrenzen, in dem Sie nach
    Aufgabengruppen filtern. Wählen Sie aus der Liste aus und drücken
    dann auf `Filter anwenden'.
    <p>
    Zeigen Sie auf den Aufgabennamen um ggf. weitere Information
    über die Aufgabe zu sehen.
    """

    ## todo_text = """
    ## <li> Über Button-Farben nachdenken </li>
    ## <li> Über das Nutzen von Tooltips nachdenken - zweischneidig </li>
    ## """

    def get_queryset(self):

        qsAufgaben = self.apply_filter ()

        # fill the table with all aufgaben
        # overwrite preferences and bemerkung if for them, a value exists
        aufgabenliste = []
        for a in qsAufgaben:
            # initialize with values from Aufgabe
            # z = a.zuteilung_set.count()
            d = {'aufgabe': a.aufgabe,
                 'gruppe': a.gruppe,
                 'datum': a.datum,
                 'stunden': a.stunden,
                 'aufgabeObjekt': a,
                 'anzahl': a.anzahl,
                 # 'meldungen': a.meldung_set.count(),
                 'meldungen': a.numMeldungen(), 
                 ## 'zuteilungen': z,
                 ## 'fehlende_zuteilungen': a.anzahl - z,
                 'zuteilungen': None,
                 'fehlende_zuteilungen': None,
                }
            # add what we can find from Meldung:
            m, newcreated = models.Meldung.objects.get_or_create(
                aufgabe=a,
                melder=self.request.user,
                defaults = models.Meldung.MODELDEFAULTS, 
                )
            d['id'] = m.id 
            d['prefMitglied'] = m.prefMitglied
            d['bemerkung'] = m.bemerkung

            # and collect
            aufgabenliste.append(d)

        table = self.get_filtered_table (aufgabenliste)

        return table


    def post(self, request, *args, **kwargs):
        # print "post in CreateMeldungenView"
        # print request.POST

        self.processUpdate(request)

        # return redirect ("arbeitsplan-meldung")
        return redirect(self.request.get_full_path())


class MeldungVorstandView(isVorstandMixin, MeldungEdit):
    """Display a (filtered) list of all Meldungen from all Users,
    with all preferences.
    Allow Vorstand to update its fields and store them.
    """

    title = "Meldungen für Aufgaben bewerten"
    # filterform_class = forms.PersonAufgabengruppeFilterForm
    filterform_class = forms.PersonAufgGrpPraefernzFilterForm
    filtertitle = "Meldungen nach Person, Aufgabengruppen"
    " oder Präferenz filtern"
    tabletitle = "Meldungen bewerten"
    # tableform ?
    filterconfig = [('aufgabengruppe', 'aufgabe__gruppe__gruppe'),
                    ('first_name', 'melder__first_name__icontains'),
                    ('last_name', 'melder__last_name__icontains'),
                    ('praeferenz', 'prefMitglied__in')
                    ]
    tableClass = MeldungTableVorstand
    model = models.Meldung

    tableform = {'name': "eintragen",
                 'value': "Meldungen eintragen/ändern"}

    intro_text = """
    Bewerten Sie die Meldungen der Mitglieder nach Eignung für eine Aufgabe.
    <ul>
    <li> Nutzen Sie die Einstufung in der rechten Spalte </li>
    <li> Eine `Nein' entspricht einer Ablehnung der Meldung;
    eine solche Meldung wird später bei den Zuteilungen
    nicht angezeigt. </li>
    <li> Geben Sie ggf. eine zusätzliche Bemerkung ein </li>
    <li> Sie können die Liste filtern nach Name des Mitglieds,
    nach Aufgabengruppe, nach den Präferenzen die das Mitglied
     bei der Meldung angegeben hat (Kombinationen möglich). </li>
    </ul>
    """

    ## todo_text = """
    ## <li> Weitere Filter einbauen?Nach Verantwortlicher?
    ## Nach Vorstandsvorlieben?  </li>
    ## <li> </li>
    ## """

    def post(self, request, *args, **kwargs):
        print request.POST
        self.processUpdate(request)
        # return redirect ('arbeitsplan-meldungVorstand')
        return redirect(self.request.get_full_path())


class QuickMeldung(View):
    """From the AufgabenTable, call a quickmeldung to
    have a default entry for meldungen. No means to edit.

    This is not really nice since a get request results in changes
    to the database :-/ 
    """

    def get(self, request, aufgabeid, *args, **kwargs):
        print aufgabeid

        try:
            aufgabe = models.Aufgabe.objects.get(pk=int(aufgabeid))
            meldung, created = models.Meldung.objects.get_or_create(aufgabe=aufgabe,
                                                                    melder=self.request.user)

            if created | (meldung.bemerkung == ""):
                meldung.prefMitglied = models.Meldung.GERNE
                meldung.bemerkung = "QUICKMELDUNG"
                meldung.save()

                messages.success(self.request,
                                 "Sie haben sich für Aufgabe " +
                                 str(aufgabeid) + " gemeldet.")
            else:
                messages.warning(self.request,
                                 "Ihre Schnellmeldung wurde nicht eingetragen; vermutlich existiert bereits eine Meldung von Ihnen.")

        except models.Aufgabe.DoesNotExist:
            messages.error(self.request,
                           "Die genannate Aufgabe " + str(aufgabeid) + " existiert nicht!")


        return redirect('arbeitsplan-aufgaben')

########################################################################################
#########   ZUTEILUNG 
########################################################################################


class ListZuteilungenView(FilteredListView):
    title = "Alle Zuteilungen anzeigen"
    filterform_class = forms.PersonAufgabengruppeFilterForm
    tableClass = ZuteilungTable
    filtertitle = "Zuteilungen nach Personen oder Aufgabengruppen filtern"
    tabletitle = "Zuteilungen"
    filterconfig = [('aufgabengruppe', 'aufgabe__gruppe__gruppe'),
                    ('first_name', 'ausfuehrer__first_name__icontains'),
                    ('last_name', 'ausfuehrer__last_name__icontains'),
                    ]

    def get_queryset(self):
        if (("all" in self.request.path) and
            (isVorstand(self.request.user))):
            self.tableClass = ZuteilungTableVorstand

            qs = models.Zuteilung.objects.all()
            self.intro_text = """
            Welche Zuteilung sind für Nutzer eingetragen?
            <p>
            Filtern Sie nach Mitgliedernamen oder Aufgabengruppe.
            """
        else:
            qs = models.Zuteilung.objects.filter(ausfuehrer=self.request.user)
            self.template_name = "arbeitsplan_listzuteilungen.html"
            self.filterform_class = None
            self.filtertitle = ""
            self.intro_text = """
            Welche Zuteilung sind für mich eingetragen?
            """
            self.context['zuteilungSummary'] = sum([z.stunden() for z in qs])

        qs = self.apply_filter(qs)
        table = self.get_filtered_table(qs)
        print table 
        return table



class ManuelleZuteilungView (isVorstandMixin, FilteredListView):
    """Manuelles Eintragen von Zuteilungen
    """

    title = "Aufgaben an Mitglieder zuteilen"
    tableClassFactory = staticmethod(ZuteilungsTableFactory)
    tabletitle = "Zuteilung eintragen"
    tableform = {'name': "eintragen",
                 'value': "Zuteilung eintragen/ändern"}

    def MitgliedBusy_Filter(self, qs, busy):
        """applies a spare capacity available filter to a user Qs"""

        if busy == 'FR':
            # show users that can still accept more work
            qs = [q
                  for q in qs
                  if q.mitglied.zugeteilteStunden() < JAHRESSTUNDEN]
        elif busy == 'BU':
            # show users that are already busy
            qs = [q
                  for q in qs
                  if q.mitglied.zugeteilteStunden() >= JAHRESSTUNDEN]

        return qs

    def AktiveAufgaben_Filter(self, qs, aktive):
        """filter out jobs froms the past?"""

        # print qs

        if aktive:
            qs = qs.filter(datum__gte=datetime.date.today())

        return qs

    filtertitle = "Nach Aufgabengruppen oder Mitgliedern filtern"
    # filterform_class = forms.PersonAufgabengruppeFilterForm
    filterform_class = forms.ZuteilungMitglied
    filterconfigAufgabe = [('aufgabengruppe', 'gruppe__gruppe'),
                           ('aktive_aufgaben', AktiveAufgaben_Filter)]
    filterconfigUser = [('first_name', 'first_name__icontains'),
                        ('last_name', 'last_name__icontains'),
                        ('mitglied_ausgelastet', MitgliedBusy_Filter)
                        ]
    # TODO: filter by preferences? show preferences in table?

    intro_text = """
    In der Tabelle werden Boxen für die Meldungen der Mitglieder
    angezeigt. Wählen Sie die Box an (ankreuzen), wenn Sie ein Mitglied
     für eine Aufgabe einteilen wollen. Entfernen Sie ein Häkchen,
      wenn das Mitglied die Aufgabe nicht mehr ausführen soll.
    <p>
    Filtern Sie nach Mitgliedsnamen oder Aufgabengruppe.
    """

    discuss_text = """
    <li> mit -1 durch den Vorstand bewertete Meldungen ausfiltern!  </li>
    <li> Weitere Filter einbauen? Nach Mitglieds-
    oder Vorstandspräferenz?  </li>
    """

    def get_data(self):
        userQs = models.User.objects.all()
        aufgabeQs = models.Aufgabe.objects.all()

        return (userQs, aufgabeQs)


    def apply_filter(self, qs):

        userQs, aufgabeQs = qs
        self.aufgabengruppe = None

        # need to get our hands on the aufgabe as passed by the URL

        if 'aufgabe' in self.kwargs:
            aufgabeQs = (models.Aufgabe.objects.
                         filter(id=self.kwargs['aufgabe']))
        else:
            self.filterconfig = self.filterconfigAufgabe
            aufgabeQs = super(ManuelleZuteilungView,
                              self).apply_filter(aufgabeQs)

            if self.filterform.is_valid():
                self.aufgabengruppe = (self.filterform.
                                       cleaned_data['aufgabengruppe'])

        self.filterconfig = self.filterconfigUser
        userQs = super(ManuelleZuteilungView, self).apply_filter(userQs)

        return (userQs, aufgabeQs)


    def annotate_data (self, qs):

        userQs, aufgabenQs = qs

        # print "Aufgaben: ", [a.__unicode__() for a in aufgabenQs]

        ztlist = []
        statuslist = {}
        aufgaben = dict([(unicodedata.normalize('NFKD', a.aufgabe).encode('ASCII', 'ignore'),
                          (-1, 'x'))
                          for a in aufgabenQs])

        for u in userQs: 
            tmp = {'last_name': u.last_name,
                    'first_name': u.first_name,
                    'mitglied': u,
                    }
            # print 'user:', u.id 
            tmp.update(aufgaben)
            mQs =  models.Meldung.objects.filter(melder=u)
            ## if self.aufgabengruppe <> None:
            ##     mQs = mQs.filter(aufgabe__gruppe__gruppe = self.aufgabengruppe)
            mQs = mQs.filter(aufgabe__in = aufgabenQs)

            # filter out all veto'ed meldungen
            mQs = mQs.exclude(prefMitglied=models.Meldung.GARNICHT)

            for m in mQs:
                tag = unicodedata.normalize('NFKD',
                                            m.aufgabe.aufgabe).encode('ASCII', 'ignore')
                tmp[tag] = (0,
                            'box_'+  str(u.id)+"_"+str(m.aufgabe.id),
                            ' ({0} / {1})'.format(m.prefMitglied,
                                                  m.prefVorstand)
                            )
                statuslist[str(u.id)+"_"+str(m.aufgabe.id)]='0'

            zQs =  models.Zuteilung.objects.filter(ausfuehrer=u)
            ## if self.aufgabengruppe <> None:
            ##     zQs = zQs.filter(aufgabe__gruppe__gruppe =  self.aufgabengruppe)
            zQs = zQs.filter(aufgabe__in=aufgabenQs)

            for z in zQs: 
                tag = unicodedata.normalize('NFKD', z.aufgabe.aufgabe).encode('ASCII', 'ignore')
                meldung = z.aufgabe.meldung_set.get(melder=u)
                tmp[tag] = (1,
                            'box_'+ str(u.id)+"_"+str(z.aufgabe.id),
                            ' ({0} / {1})'.format(meldung.prefMitglied,
                                                  meldung.prefVorstand)
                            )
                statuslist[str(u.id)+"_"+str(z.aufgabe.id)]='1'

            # TODO: Add to tmp the amount of already zugeteilt work per user
            # This is wrong, have to take into account Stundenplanzuteilungen! 
            ## tmp['zugeteilt'] = (models.Zuteilung.objects
            ##                     .filter(ausfuehrer = u)
            ##                     .aggregate(Sum('aufgabe__stunden'))
            ##                     ['aufgabe__stunden__sum']
            ##                     )

            tmp['zugeteilt'] = u.mitglied.zugeteilteStunden()

            ztlist.append(tmp)

        # pp (ztlist)
        # store the statuslist in the hidden field, to be accessible to POST later on
        self.tableformHidden = [{'name': 'status',
                                 'value': ';'.join([k+'='+v
                                                    for k, v
                                                    in statuslist.iteritems()]),
                                 }]

        return (ztlist, aufgabenQs)

    def post (self,request, *args, **kwargs):

        previousStatus = dict([ tuple(s.split('=') )
                   for s in 
                    request.POST.get('status').split(';')
                  ])

        # print "prevState:"
        # print previousStatus

        newState = dict([ (item[0][4:], item[1])
                     for item in request.POST.iteritems()
                     if item[0][:4] == "box_"
                    ])

        # print "newState"
        # print newState

        # find all items in  newState  that have a zero in prevState
        # add that zuteilung
        for k,v in newState.iteritems():
            if previousStatus[k] == '0':
                # print "add ", k
                user, aufgabe = k.split('_')
                aufgabeObj = models.Aufgabe.objects.get(id=int(aufgabe))
                ausfuehrerObj = models.User.objects.get(id=int(user))
                ## z = models.Zuteilung(aufgabe=aufgabeObj,
                ##                      ausfuehrer=ausfuehrerObj,
                ##                      )
                ## z.save()

                z, created = models.Zuteilung.objects.get_or_create (aufgabe=aufgabeObj,
                                                                     ausfuehrer=ausfuehrerObj)
                if not created:
                    messages.debug (request,
                                    u"warnung: Aufgabe {0} war bereits an {1} {2} zugeteilt".format(aufgabeObj.aufgabe,
                                                                                 ausfuehrerObj.first_name,
                                                                                 ausfuehrerObj.last_name))
                messages.success(request,
                                 u"Aufgabe {0} wurde an {1} {2} zugeteilt".format(aufgabeObj.aufgabe,
                                                                                 ausfuehrerObj.first_name,
                                                                                 ausfuehrerObj.last_name))

                print "setting (cause of add)  zuteilung benachrichtigung noetig for ", ausfuehrerObj
                ausfuehrerObj.mitglied.zuteilungBenachrichtigungNoetig = True
                ausfuehrerObj.mitglied.save()

        # find all items in prevState with a 1 there that do no appear in newState
        # remove that zuteilung
        for k,v in previousStatus.iteritems():
            if v=='1' and k not in newState:
                # print "delete ", k
                user, aufgabe = k.split('_')
                aufgabeObj = models.Aufgabe.objects.get(id=int(aufgabe))
                ausfuehrerObj = models.User.objects.get(id=int(user))
                z = models.Zuteilung.objects.filter (aufgabe=aufgabeObj,
                                                  ausfuehrer=ausfuehrerObj,
                                                 )
                for zz in z:
                    zz.delete()

                messages.success(request,
                                 u"Aufgabe {0} wird nicht mehr"
                                 u" von  {1} {2} durchgeführt."
                                 .format(aufgabeObj.aufgabe,
                                         ausfuehrerObj.first_name,
                                         ausfuehrerObj.last_name))

                print "setting (cause of delete) zuteilung benachrichtigung noetig for ", ausfuehrerObj
                ausfuehrerObj.mitglied.zuteilungBenachrichtigungNoetig = True
                ausfuehrerObj.mitglied.save()


        # TODO: emails senden?

        return redirect(self.request.get_full_path())

class ZuteilungUebersichtView(isVorstandMixin, FilteredListView):
    title = "Übersicht der Aufgaben und Zuteilungen"
    tableClassFactory = staticmethod(StundenplanTableFactory)
    tabletitle = "Aufgaben mit benötigten/zugeteilten Personen"

    show_stundenplan = False

    model = models.Aufgabe

    def ungenuegend_zuteilungen_filter(self, qs, restrict):
        print qs, restrict
        if restrict == 'UN':
            # qs=qs.filter(anzahl__gt=zuteilung_set.count())
            qs = (qs.annotate(num_Zuteilung=Count('zuteilung')).
                  filter(anzahl__gt=F('num_Zuteilung')))
        elif restrict == 'ZU':
            qs = (qs.annotate(num_Zuteilung=Count('zuteilung')).
                  filter(anzahl__lte=F('num_Zuteilung')))
        return qs

    def stundenplan_anzeigen_filter(self, qs, show):
        self.show_stundenplan = show
        return qs

    filtertitle = "Aufgaben filtern"
    filterform_class = forms.ZuteilungManuellFilter
    filterconfig = [('aufgabengruppe', 'gruppe__gruppe'),
                    ('zuteilungen_ausreichend',
                     ungenuegend_zuteilungen_filter),
                    ('stundenplan', stundenplan_anzeigen_filter),
                    ]

    intro_text = """
    Die Tabelle fasst pro Aufgabe die benötigten/angeforderten,
    gemeldeten und bereits zugeteilten Mitglieder zusammen.
    <ul>
    <li>Aus den Spalten Aufgabe und Zuteilen kann man direkt
    die Aufgabe aufrufen bzw. Zuteilungen für diese Aufgabe
    anschauen und verändern. </li>
    <li> Sind für eine Aufgabe die Anforderungen nach einzelnen Stunden
    aufgegliedert (typischerweise bei Bewirtung der Fall), werden pro
    Stunden die angeforderten bzw. bereits zugeteilten Mitglieder
    in den rechten Spalten angezeigt. </li>
    <li> Bei solchen Aufgaben kann durch Klick in der Spalte `Stundenplan'
    direkt die Zuteilung zu einzelnen Stunden verändert werden. </li>
    </ul>
    """

    discuss_text = """
    <li> Teamleader Stundenplanzuteilungen erlauben? Oder auch
    allgemein Zuteilung von Mitgliedern? </li>
    """

    def get_filtered_table(self, qs):
        table = self.tableClassFactory(qs, self.show_stundenplan)
        django_tables2.RequestConfig(self.request).configure(table)

        return table

    def annotate_data(self, qs):

        data = []
        for aufgabe in qs:
            newEntry = defaultdict(int)
            newEntry['id'] = aufgabe.id
            newEntry['aufgabe'] = mark_safe(
                u'<a href="{1}">{0}</a>'.format(aufgabe.aufgabe,
                                                reverse('arbeitsplan-aufgabenEdit',
                                                        args=(aufgabe.id,))))

            newEntry['required'] = aufgabe.anzahl
            newEntry['gruppe'] = aufgabe.gruppe.gruppe
            newEntry['gemeldet'] = aufgabe.numMeldungen()
            newEntry['zugeteilt'] = aufgabe.zuteilung_set.count()
            newEntry['editlink'] = mark_safe(
                u'<a href="{0}">Zuteilung</a>'.format(
                    reverse('arbeitsplan-manuellezuteilungAufgabe',
                            args=(aufgabe.id,),
                            )))

            if aufgabe.has_Stundenplan():

                for s in aufgabe.stundenplan_set.filter(anzahl__gt=0):
                    # print s
                    newEntry['u'+str(s.uhrzeit)] = {
                        'required': s.anzahl,
                        'zugeteilt': 0
                        }

                # TODO: Die Schleifen auf aggregate processing umstellen
                for zs in aufgabe.zuteilung_set.all():
                    # print zs
                    for stdzut in zs.stundenzuteilung_set.all():
                        newEntry['u'+str(stdzut.uhrzeit)]['zugeteilt'] += 1


                # newEntry['zugeteilt'] = None
                newEntry['stundenplanlink'] = mark_safe(u'<a href="{0}">Stundenplan</a>'.format(
                    reverse ('arbeitsplan-stundenplaeneEdit',
                             args=(aufgabe.id,)),
                    ))
            else:
                # normale Aufgaben, kein Stundenplan
                newEntry['stundenplanlink'] = None

            data.append(newEntry)

        # pp( data)

        # TODO: allow filtering of those Aufgaben 
        # qs = self.apply_filter(qs)

        # for each remaining Aufgabe in qs, find the already assigned STunden 

        return data


class StundenplaeneEdit(FilteredListView):

    title = """Weisen Sie einer Aufgabe Personen
     zu den benötigten Zeitpunkten zu"""
    tableClassFactory = staticmethod(StundenplanEditFactory)
    tabletitle_template = u"Zuweisung für Stunden eintragen"
    tabletitle = u"Zuweisung für Stunden eintragen"
    tableform = {'name': "eintragen",
                 'value': "Stundenzuteilung eintragen/ändern"}

    intro_text = """Hinweis: Wenn hier keine Nutzer angezeigt werden,
    müssen Sie zunächst Nutzer dieser Aufgabe zuteilen. Das Zuweisen zu
    einzelnen Stunden ist erst der zweite Schritt.

    In der Tabelle werden Spalten pro Uhrzeit angezeigt.
    In den Spaltenüberschriften wird
    in Klammer jeweils (Anzahl benötigte Mitglieder / Anzahl
    schon zugeteilte Mitglieder) angezeigt.
    """

    todo_text = """Anzahl noch benötigte Uhrzeiten anders hervorheben?
    Nur Differenz anzeigen? Umstellen auf Kontakte statt
    Vornamen / Nachnamen """


    def get_filtered_table(self, qs, aufgabe):
        table = self.tableClassFactory(qs, aufgabe)
        django_tables2.RequestConfig(self.request).configure(table)

        return table

    def get_queryset(self):
        """For a given Aufgabe, find all users with a zuteiulung to that aufgabe.
        Construct, for each such users, two things:
        a) checkboxes, showing for each possible Stundenplan timeslot,
           whether it is currently occupiued or not
        b) an entry in the data: list of dictionaries with entries first_name,
           last_name, and the timeslots 0/1
        """

        try:
            aufgabeid = self.kwargs['aufgabeid']
        except KeyError:
            messages.error (self.request, "Die angegebene URL bezeichnet keine Aufgabe")
            return None

        aufgabe = get_object_or_404 (models.Aufgabe, pk=aufgabeid)

        self.tabletitle = self.tabletitle_template + u" - Aufgabe: " + aufgabe.aufgabe

        data = []
        checkedboxes = []

        stundenplan = aufgabe.stundenplan_set.filter(anzahl__gt=0)

        zugeteilteUser = [z.ausfuehrer for z in aufgabe.zuteilung_set.all()]

        print "Stundenplan fuer Auzfgabe: ", stundenplan
        print "zugeteilte User: ",  zugeteilteUser

        # construct the checkboxes string:
        # userid_uhrzeit, if that user works on that time

        # for each zuteilung, the following gives a separate queryset:
        stundenzuteilungenQuerysets = [z.stundenzuteilung_set.all()
                                       for z in aufgabe.zuteilung_set.all()]
        checkedboxes = [str(sz.zuteilung.ausfuehrer.id) + "_" + str(sz.uhrzeit)
                        for szQs in stundenzuteilungenQuerysets
                        for sz in szQs]
        print checkedboxes

        # construct the list of dicts for users:
        for u in zugeteilteUser:
            newEntry = {'last_name': u.last_name,
                        'first_name': u.first_name,
                        }
            zuteilungThisUser = aufgabe.zuteilung_set.filter(ausfuehrer=u)
            if zuteilungThisUser.count() != 1:
                messages.error('Error 13: ' + aufgabe.__unicode__()
                               + ' - ' + u.__unicode__())

            stundenzuteilung = (zuteilungThisUser[:1].get().
                                stundenzuteilung_set.values_list('uhrzeit',
                                                                 flat=True))
            print zuteilungThisUser
            for s in stundenplan:
                newEntry['u'+str(s.uhrzeit)] = ((1 if s.uhrzeit in stundenzuteilung
                                                 else 0),
                                                 ('uhrzeit_' +
                                                  str(u.id) + "_" +
                                                  str(s.uhrzeit)),
                                                 )
            data.append(newEntry)

        print data

        # print [(sz.zuteilung.ausfuehrer, sz.uhrzeit) for sz in stundenzuteilungen]

        ## # TODO: rewrite that to only iterate over users with zuteilung for this aufgabe
        ## # should be tremendously more efficient 
        ## for u in models.User.objects.all():
        ##     newEntry = {'last_name': u.last_name,
        ##                 'first_name': u.first_name,
        ##                 }

        ##     try: 
        ##         zuteilung = models.Zuteilung.objects.get(ausfuehrer=u,
        ##                                                  aufgabe=aufgabe)
        ##         stundenzuteilungen =  zuteilung.stundenzuteilung_set.values_list('uhrzeit',
        ##                                                                          flat=True )

        ##         # print "Zuteilung fuer User: ", u, stundenzuteilungen 

        ##         for s in stundenplaene:
        ##             tag = 'uhrzeit_' + str(u.id) + "_" + str(s.uhrzeit)
        ##             present = s.uhrzeit in stundenzuteilungen 
        ##             newEntry['u'+ str(s.uhrzeit)] = (1 if present else 0, tag)
        ##             if present: 
        ##                 checkedboxes.append(str(u.id) + "_" + str(s.uhrzeit))

        ##         data.append(newEntry)

        ##     except models.Zuteilung.DoesNotExist:  # keine Zuteilung gefunden 
        ##         pass

        ##     print "checkedboxes after user: ", u, " : ", checkedboxes

        ## # prepare user id list to be passed into the hidden field,
        ## # to ease processing later
        self.tableformHidden = [{'name': 'checkedboxes',
                                 'value': ','.join(checkedboxes)}]

        table = self.get_filtered_table(data, aufgabe)

        return table

    def post(self, request, aufgabeid, *args, **kwargs):

        print self.request.POST

        if self.request.POST.get('checkedboxes'):
            tmp = [x.split('_')
                   for x in
                   self.request.POST.get('checkedboxes').split(',')
                  ]
        else:
            tmp = []

        # pp(tmp)
        checkedboxes = [(int(x[0]), int(x[1])) for x in tmp ]
        print "checkboxes: ", checkedboxes

        # any values to add? 
        for v in self.request.POST:
            if v.startswith('uhrzeit_'):
                tag, uid, uhrzeit = v.split('_')

                # try to remove this checked box from the list of originally checked boxes,
                # not a problem if not there, then it is simply a new check
                try:
                    checkedboxes.remove ((int(uid), int(uhrzeit)))
                except ValueError:
                    pass

                # print aufgabeid, uid, uhrzeit
                zuteilung = models.Zuteilung.objects.get (ausfuehrer__id = uid,
                                                          aufgabe__id = aufgabeid)
                # print "Z: ", zuteilung
                stundenzuteilung, created  = models.StundenZuteilung.objects.get_or_create (
                    zuteilung = zuteilung,
                    uhrzeit = int(uhrzeit), 
                    )
                if created:
                    stundenzuteilung.save()

        # anything still in checkedboxes had been checked before, but was not in QueryDict
        # i.e., it has been uncheked by user and should be removed
        for uid, uhrzeit in checkedboxes:
            # print "remove: ", uid, uhrzeit

            zuteilung =  models.Zuteilung.objects.get (ausfuehrer__id = uid,
                                                          aufgabe__id = aufgabeid)

            stundenzuteilung = zuteilung.stundenzuteilung_set.get(uhrzeit=uhrzeit)

            # print stundenzuteilung

            stundenzuteilung.delete()

        return redirect (# "arbeitsplan-stundenplaeneEdit",
                         self.request.get_full_path(),
                         aufgabeid = aufgabeid, 
                         )

    
########################################################################################
#########   LEISTUNG
########################################################################################


class CreateLeistungView (CreateView):
    model = models.Leistung
    form_class = forms.CreateLeistungForm
    template_name = "arbeitsplan_createLeistung.html"

    def form_valid(self, form):
        print "in Create Leistung View form_valid"
        leistung = form.save(commit=False)
        leistung.melder = self.request.user
        leistung.save()

        print "saved leistung"

        return HttpResponseRedirect(self.success_url)

# class CreateLeistungDritteView (CreateView):
    
####################################


class ListLeistungView (FilteredListView):
    title = "Arbeitsleistung auflisten"
    template_name = "arbeitsplan_listLeistung.html"

    tableClass = LeistungTable
    tabletitle = "Eingetragene Leistungen"

    intro_text = """
    Es liegen die folgenden Leistungen vor.
    """

    discuss_text="""
    <li> links zum Editieren der Meldung machen - für alle, oder nur offene, rückfrage? akzeptierte oder abgelehnte sollten nicht mehr editiert werden können! </li>
    """

    model = models.Leistung

    def get_data(self):
        # TODO: enable arbitrary user to be shown, if called by vorstand 
        qsLeistungen = self.model.objects.filter(melder=self.request.user)

        res = []
        for s in models.Leistung.STATUS:
            qs = models.Leistung.objects.filter(status=s[0],
                                                melder=self.request.user,
                                                )
            sum = qs.aggregate(Sum('zeit'))
            res.append((s[0], s[1], qs, sum['zeit__sum']))

        self.context['leistungSummary'] = res

        return qsLeistungen


class LeistungBearbeitenView (isVorstandOrTeamleaderMixin, FilteredListView):
    """
    A view to show a table of non-accepted/rejected Leistungen to a Vorstand.
    Allows to accept, reject, or enquiry them. 
    """

    title = "Gemeldete Leistungen bearbeiten"
    tableClass = LeistungBearbeitenTable
    tabletitle = "Leistungen akzeptieren, ablehnen, oder rückfragen"
    tableform = {'name': "submit",
                 'value': "Leistungen ändern"}

    filtertitle = "Nach Mitglied, Aufgabe, Datum oder Status filtern"
    filterform_class = forms.LeistungFilter
    filterconfig = [('first_name', 'melder__first_name__icontains'),
                    ('last_name', 'melder__last_name__icontains'),
                    ('aufgabengruppe', 'aufgabe__gruppe__gruppe'),
                    ('von', 'datum__gte'),
                    ('bis', 'datum__lte'),
                    ('status', 'status__in')
                    ]
    intro_text = """
    Bitte akzeptieren, lehnen ab, oder rückfragen Sie die folgenden gemeldeten Leistungen. Wählen Sie einen neuen Status und tragen ggf. eine Bemerkung ein.
    """

    model = models.Leistung


    def get_data (self):
        """Vorstand can elect to see all or just some.
        Teamleaders are restricted to those tasks where they are
        indeed the teamleader.
        """

        if isVorstand(self.request.user):
            zustaendig = self.kwargs['zustaendig']

            if zustaendig=="me": 
                mainqs = models.Leistung.objects.filter(aufgabe__verantwortlich=
                                                        self.request.user)
            else:
                mainqs = models.Leistung.objects.all()
        elif isTeamlead(self.request.user):
            leadingTheseTasks = self.request.user.teamleader_set.all()

            mainqs = models.Leistung.objects.filter(aufgabe__in = leadingTheseTasks)
        else:
            return None

        return mainqs

    def post (self, request, zustaendig, *args, **kwargs):
        """need to carefully check:
        - vorstand may do everything
        - teamleaders only for those tasks they lead.
        They only see those tasks in regular operation, but
        hackers might try to inject wierd stuff here. 
        """

        if isVorstand(request.user):
            checkNeeded = False
        elif isTeamlead(request.user):
            checkNeeded = True
            leadingTheseTasks = self.request.user.teamleader_set.all()
        else:
            messages.error(request,
                           "Sie dürfen diese Funktion nicht benutzen!"
                           )

            redirect("home")


        data = {}
        for k, v in request.POST.iteritems():
            try:
                # TODO: shorten to startswith construction 
                # print 'post value: ', k, v 
                if "status" == k[:6]:
                    # print "status detected"
                    opt, num = k.split('_')
                    # print opt, num 
                    if not num in data.keys():
                        data[num] = {'status': "",
                                     'bemerkungVorstand': "",
                        }

                    data[num]['status'] = v

                if 'bemerkungVorstand' == k[:17]:
                    tag, num = k.split('_')
                    if not num in data.keys():
                        data[num] = {'status': "",
                                     'bemerkungVorstand': "",
                        }

                    data[num][tag] = v

            except:
                pass 

        # print data

        # and now save the updated values in the data
        for k,v in data.iteritems():
            # they should all exist!
            ## print "----------"
            ## print k, v
            ## print type(v['id_bemerkungVorstand'])

            l = models.Leistung.objects.get(id=int(k))
            if checkNeeded:
                if l.aufgabe not in leadingTheseTasks:
                    messages.error(request,
                                   "Sie dürfen Leistungsmeldungen"
                                   " für diese Aufgabe nicht bearbeiten!")
                    continue

            safeit = False
            if l.bemerkungVorstand != v['bemerkungVorstand']:
                l.bemerkungVorstand = v['bemerkungVorstand']
                safeit = True

            if l.status != v['status'] and v['status'] != "":
                l.status = v['status']
                safeit = True

            if safeit:
                l.save()
                messages.success(request,
                                 u"Leistungsmeldung von {0} {1} "
                                 u"für Aufgabe {2} aktualisiert.".format(
                                     l.melder.first_name,
                                     l.melder.last_name,
                                     l.aufgabe)
                                     )
            # print l

        # TODO: bei Rueckfrage koennte man eine email senden? oder immer?

        # return redirect ('/arbeitsplan/leistungenBearbeiten/z=all')
        return redirect(self.request.get_full_path())


##########################    


class Salden(isVorstandMixin, FilteredListView):

    filterFormClass = forms.NameFilterForm
    title = "Saldenüberblick über geleistete Arbeit"

    tableClassFactory = staticmethod(SaldenTableFactory)
    tabletitle = "Saldenübersicht"

    filtertitle = "Salden nach Vor- oder Nachnamen filtern"
    filterform_class = forms.SaldenFilter

    model = models.User

    intro_text = """
    Ein Überblick über die von den Mitgliedern geleistete Arbeit,
    basiered auf den vorliegenden Leistungsmeldungen und deren
    Bewertungen durch Vorstände. Zuteilungen werden separat aufgeführt.
    """

    # TODO: für einen anklickbaren User braucht es nur:
    # http://127.0.0.1:8000/arbeitsplan/leistungenBearbeiten/z=all/?last_name=Pan&first_name=Peter&status=OF&filter=Filter+anwenden

    def check_filter(self, userdata):
        """Apply a filter based on annotated data. HArd to do in the generic way
        of filterprocessing...
        """
        try:
            filterchoice = self.filterform.cleaned_data['saldenstatus']
        except AttributeError:
            filterchoice = '--'
        # see the Saldenstatus table for definition of these choices!

        return {
            '--': lambda u: True,
            'OK': lambda u: u['AK'][0] >= JAHRESSTUNDEN,
            'CH': lambda u: ((u['AK'][0] < JAHRESSTUNDEN) and
                             ((u['AK'][0] or 0) +
                              (u['OF'][0] or 0) +
                              u['future'] + u['nodate'] >=
                             JAHRESSTUNDEN)
                             ),
            'PR': lambda u: ((u['AK'][0] or 0) +
                             (u['OF'][0] or 0) +
                             u['future'] + u['nodate'] <
                             JAHRESSTUNDEN),
            }[filterchoice](userdata)

    def annotate_data(self, userQs):
        res = []

        rurl = reverse("arbeitsplan-leistungBearbeiten", args=('all',))

        for u in userQs:
            tmp = {}
            tmp['user'] = u
            tmp['box'] = ("box-" + str(u.id), True)
            qs = models.Leistung.objects.filter(melder=u)
            for s in models.Leistung.STATUS:
                zeit = qs.filter(status=s[0]
                                 ).aggregate(Sum('zeit'))['zeit__sum']

                if zeit: 
                    linktarget = rurl + "?" + urlencode({
                        'last_name': u.last_name,
                        'first_name': u.first_name,
                        'status': s[0],
                        'filter': 'Filter anwenden'})
                else:
                    linktarget = None 

                tmp[s[0]] = (zeit, linktarget)


            # TODO: add linked column here as well 
            ## zugeteilt = (models.Zuteilung.objects.
            ##              filter(ausfuehrer=u).aggregate(Sum('aufgabe__stunden'))['aufgabe__stunden__sum'])
            zugeteilt = u.mitglied.zugeteilteStunden()

            tmp['past'] = u.mitglied.zugeteilteStunden(-1)
            tmp['future'] = u.mitglied.zugeteilteStunden(+1)
            tmp['nodate'] = u.mitglied.zugeteilteStunden(0)
            linktarget = reverse("arbeitsplan-zuteilunglist",
                                 args=('all',)) + "?" + urlencode({
                                     'last_name': u.last_name,
                                     'first_name': u.first_name,
                                     'status': s[0],
                                     'filter': 'Filter anwenden'})

            tmp['zugeteilt'] = (zugeteilt, linktarget)

            if self.check_filter(tmp):
                res.append(tmp)

            # pp (tmp)
            # print reverse(ListLeistungView,args=("all",))

        return res



########################################################################################
### EXPERIMENTELL 
########################################################################################


class ErstelleZuteilungView(View):
    """Automatisches Berechnen von Zuteilungen"""

    def get (self,request, *args, **kwargs):
        # Vorgehen:
        # - alle automatisch erstellten Zuordnungen loecshen
        # - aus den Meldungen einen bipartiten Graph erstellen (networkx nutzen)
        # - aus dem Graphen die manuell erstellten Zuordnungen entfernen
        # - maximales Matching ausrechnen
        # - als Zuordnungen in Tabelle eintragen
        # - redirect zur Zuordnungsanzeigen machen

        ## qs = models.Zuteilung.objects.filter (automatisch__exact=True)
        ## for o in qs:
        ##     o.delete()

        ## #######
        ## # den Graph bauen
        ## G = nx.Graph()
        ## # alle Mitglieder einfuegen
        ## for m in models.User.objects.all():
        ##     G.add_node ('P' + str(m.id))

        ## for a in models.Aufgabe.objects.all():
        ##     for i in range(a.anzahl):
        ##         G.add_node ('A' + str(a.id) + ':' + str(i))

        ## for m in models.Meldung.objects.all():
        ##     G.add_edge ('')

        messages.error(request,
                        "Diese Funktion ist noch nicht implementiert!")
        return redirect ('home')


########################
## BENACHRICHTIGUNGEN
########################

class FilteredEmailCreateView (FilteredListView):

    tableform = {'name': "eintragen",
                 'value':
                 "Benachrichtigungen eintragen"}

    intro_text = """Versenden von Benachrichtungen:
    Wählen Sie die zu benachrichtigenden Zeilen durch die
    Checkbox in der letzten Spalte aus (default: alle).
    Sie können pro Ziele einen Kommentar eintippen,
    der an die jeweilige email angefügt wird.
    Zusätzlich können Sie (in dem Eingabefeld unterhalb der Tabelle)
    einen Text eingeben, der an ALLE ausgesendeten emails angefügt wird.
    """

    def get_context_data(self, **kwargs):
        context = super(FilteredEmailCreateView,
                        self).get_context_data(**kwargs)
        context['furtherfields'] = forms.EmailAddendumForm()
        return context

    def annotate_data(self, qs):
        """ we add a status and a anmerkung field to the queryset
        """

        for q in qs:
            q.sendit = False
            q.anmerkung = ""

        return qs

    def constructTemplateDict(self, instance):
        return {}

    def getUser(self, instance):
        return None

    def saveUpdate(self, instance, thisuser):
        return None

    def post(self, request, *args, **kwargs):

        users_no_email = []

        # extarct all the ids that are to be sent out
        idlist = []
        for k in request.POST.keys():
            if k.startswith('sendit_'):
                __, sendid = k.split('_')
                idlist.append(int(sendid))

        ergaenzung = request.POST['ergaenzung']

        # do the actual sending:
        # pull out the leistungs object and send it out
        for i in idlist:
            instance = self.model.objects.get(pk=i)
            thisuser = self.getUser (instance)

            if thisuser.email:
                anmerkung = request.POST['anmerkung_'+str(i)]

                ## construct the dict manually; model_to_dict or similar not plausible;
                ## sadly, not possible to pass a model instance AND a dict into send_mail

                d = self.constructTemplateDict(instance)
                d['anmerkung'] = anmerkung
                d['ergaenzung'] = ergaenzung 

                mail.send(
                    [thisuser.email],
                    template = self.emailTemplate,
                    context = d
                    )

                self.saveUpdate(instance, thisuser)

                messages.success(request,
                                 u"Benachrichtigung an "
                                 u"Mitglied {0} {1} eingetragen".format(thisuser.first_name,
                                                                        thisuser.last_name,))
            else:
                if not thisuser in users_no_email:
                    messages.error(request,
                                   u"Für Nutzer {0} {1} liegt keine email-Adresse vor,"
                                   u" keine Benachrichtigung gesendet".format(thisuser.first_name,
                                                                              thisuser.last_name,)
                                                                              )
                    users_no_email.append(thisuser)

        if idlist:
            messages.warning(request,
                             "Vergessen Sie nicht, die Benachrichtigungen explizit abzuschicken!")

        ## TODO: better redirect home 
        return redirect(request.get_full_path())


class LeistungEmailView (isVorstandMixin, FilteredEmailCreateView):

    title = "Benachrichtigungen für bearbeitete Leistungen"
    model = models.Leistung

    tableClass = LeistungEmailTable

    filterform_class = forms.LeistungEmailFilter

    def benachrichtigt_filter (self, qs, includeSchonBenachrichtigt):
        ## print "benachrichtigt filter: ", self, qs, includeSchonBenachrichtigt
        ## for q in qs:
        ##     print q.__unicode__()
        ##     print 'veraendert: ', q.veraendert
        ##     print 'benachrich: ', q.benachrichtigt
        ##     print 'schon benachrichtigt: ', q.veraendert <= q.benachrichtigt
        # filter out those were the "benachrichtigt" is later than the last change
        if includeSchonBenachrichtigt:
            pass
        else:
            # if veraendert <= benachrichtigt,
            # then an instance has alredy been notified
            # so we leave only those in the queryset
            # where the opposite  is true
            # (filter keeps those where the
            # attribute is TRUE!!!

            qs = qs.filter(veraendert__gt=F('benachrichtigt'))
        return qs

    filterconfig = [('aufgabengruppe', 'aufgabe__gruppe__gruppe'),
                    ('status', 'status__in'),
                    ('benachrichtigt', benachrichtigt_filter), 
                    ]
    # specific data about the email handling:
    emailTemplate = "leistungEmail"

    def getUser(self, instance):
        return instance.melder

    def saveUpdate(self, instance, thisuser):
        instance.benachrichtigt = datetime.datetime.utcnow().replace(tzinfo=utc)
        # print instance.benachrichtigt
        instance.save(veraendert=False)

    def annotate_data(self, qs):
        qs = super(LeistungEmailView, self).annotate_data(qs)
        for q in qs:
            q.sendit = True if q.veraendert > q.benachrichtigt else False    

        return qs

    def constructTemplateDict (self, instance):
        d = {'first_name': instance.melder.first_name,
             'last_name': instance.melder.last_name,
             'aufgabe': instance.aufgabe.aufgabe,
             'wann': instance.wann,
             'stunden': instance.zeit,
             'bemerkung': instance.bemerkung,
             'bemerkungVorstand': instance.bemerkungVorstand,
             'status': instance.get_status_display(),
             'schonbenachrichtigt': instance.veraendert < instance.benachrichtigt,             
             }
        return d


class ZuteilungEmailView(isVorstandMixin, FilteredEmailCreateView):
    """Display a list of all users where the zuteilung has changed since last
    notification. Send them out.
    """

    title = "Benachrichtigungen für neue oder veränderte Zuteilungen"

    model = models.Mitglied

    tableClass = ZuteilungEmailTable
    filterform_class = forms.ZuteilungEmailFilter

    def noetig_filter(self, qs, includeSchonBenachrichtigt):
        if includeSchonBenachrichtigt:
            pass
        else:
            # if veraendert <= benachrichtigt, then an instance
            # has alredy been notified
            # so we leave only those in the queryset where
            # the opposite  is true
            # (filter keeps those where the attribute is TRUE!!!

            qs = qs.filter(zuteilungBenachrichtigungNoetig=True)
        return qs


    filterconfig = [('last_name', 'user__last_name__icontains'),
                    ('first_name', 'user__first_name__icontains'), 
                    ('benachrichtigt', noetig_filter), 
                    ]

    emailTemplate = "zuteilungEmail"

    def getUser(self, instance):
        return instance.user

    def saveUpdate(self, instance, thisuser):
        """ tell the instance (of Mitglied) that it has been notified"""

        instance.zuteilungsbenachrichtigung = datetime.datetime.utcnow().replace(tzinfo=utc)
        instance.zuteilungBenachrichtigungNoetig = False

        # print instance.benachrichtigt
        instance.save()

    def annotate_data(self, qs):
        qs = super(ZuteilungEmailView, self).annotate_data(qs)
        for q in qs:
            q.sendit = q.zuteilungBenachrichtigungNoetig
        return qs 

    def constructTemplateDict(self, instance):
        """this view operates on models.User, so instance is a user object.
        We have to find all zuteilungen for this user and stuff this data into
        the construct Tempalte Dict for the email to render
        """

        d = {'first_name': instance.user.first_name,
             'last_name': instance.user.last_name,
             'zuteilungen': models.Zuteilung.objects.filter(ausfuehrer=instance.user)
            }

        # print d 
        return d 


class EmailSendenView(isVorstandMixin, View):
    """Trigger sending emails via the post_office command line managemenet command
    """

    def get(self, request, *args, **kwargs):

        import post_office.models as pom

        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        # print now

        call_command('send_queued_mail')

        # count how many newly genereated log entries have relevant status values:
        newEmailLogs = pom.Log.objects.filter(date__gt = now)

        ## for el in newEmailLogs:
        ##     print el

        if newEmailLogs.count() == 0:
            messages.success(request,
                             "Es waren keine emails zu versenden."
                             )
        else:
            failed = newEmailLogs.filter(status=pom.STATUS.failed).count()
            sent = newEmailLogs.filter(status=pom.STATUS.sent).count()

            print sent, failed

            if sent > 0:
                messages.success(request,
                                 "Es wurden {0} Nachrichten versandt"
                                 .format(sent))
            if failed > 0:
                messages.error(request,
                               "Es konnten {0} Nachrichten nicht versendet"
                               "werden! Sysadmin kontaktieren!".
                               format(failed))

        return redirect('home')


################################
## Impersonateion

class ImpersonateListe(isVorstandMixin, FilteredListView):
    """Show a table with all Mitglieder,
    pick one to impersonate.
    Needs a suitable linked Column to point
    to impersonate/user-id
    """
    title = "Darzustellenden Nutzer auswählen"
    tableClass = MitgliederTable
    tabletitle = "Mitglieder"
    model = User

    filterform_class = forms.NameFilterForm
    filterconfig = [('first_name', 'first_name__icontains'),
                    ('last_name', 'last_name__icontains'),
                    ]


    intro_text = """Sie können die Identität eines
    anderen Nutzers annehmen,
    beispielsweise um Meldungen oder Leistungen für diesen einzutragen.
    <p>
    Bitte gehen Sie verantwortlich mit dieser Möglichkeit um!
    <p>
    Beachten Sie: Diese Funktion funktioniert nicht bei Mitgliedern
    mit Sonderstatus (z.B. Adminstratoren dieser Webseite).
    """

    def get_data(self):
        return (self.model.objects
                .filter(is_staff=False)
                .filter(is_superuser=False)
                .exclude(id=self.request.user.id))
    pass


class PasswordChange(FormView):
    template_name = "password_change.html"
    form_class = forms.PasswordChange
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        try:
            u = self.request.user
            u.set_password(form.cleaned_data['pw1'])
            u.save()
            messages.success(self.request,
                             u'Ihr Passwort wurde erfolgreich geändert'
                             )
        except Exception as e:
            messages.error(self.request,
                           u'Ihre Passwortänderung ist fehlgeschlagen: ' +
                           str(e),
                           )
        return super(PasswordChange, self).form_valid(form)

##############


class MediaChecks(View):
    def get(self, request):
        """Figure out:
        active user with raw access: Entwickler
        vorstand, teamleader, ordinary member
        """

        basepath = SENDFILE_ROOT
	
	# print "in Meia checks: ", basepath

        if request.user.is_staff:
            filename = "SVPB-entwickler.pdf"
        elif isVorstand(request.user):
            filename = "SVPB-vorstand.pdf"
        elif isTeamlead(request.user):
            filename = "SVPB-teamleader.pdf"
        else:
            filename = "SVPB.pdf"

        return sendfile(request,
                        os.path.join(basepath, filename))
