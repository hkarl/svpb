# -*- coding: utf-8 -*-

# Create your views here.

import collections
import datetime
import os
import types
from collections import defaultdict

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.management import call_command
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.db.models import Sum, F, Count
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.utils.http import urlencode
from django.utils.timezone import utc
from django.views.generic import UpdateView, DeleteView, TemplateView
from django.views.generic import View, ListView, CreateView
from post_office import mail

# Arbeitsplan-Importe:
import forms
from tables import *  # TODO: change import not to polute name space
from svpb.settings import JAHRESSTUNDEN, SENDFILE_ROOT

from sendfile import sendfile


from svpb.views import isTeamlead, isVorstand, isVorstandMixin, isVorstandOrTeamleaderMixin
#################




def notifyVorstand(meldung, mailcomment):
    """IF a meldung has been created or updated by the Mitglied,
    then send an email to the corresponding Vorstand.
    """
    # sanity check: does the verantwortlicher of the aufgabe of the meldung have an email=
    try:
        em = meldung.aufgabe.verantwortlich.email
    except:
        # try to inform some other way?
        return

    mail.send(em,
              template="meldungNotify",
              context={'comment': ', '.join(mailcomment),
                       'meldung': meldung,
                       'melder': meldung.melder,
                   }

    )
    # and finally send out all queued mails:
    # call_command('send_queued_mail')
    # do that as a cronjob?

    pass

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
                            # print filterexp
            else:
                print "filterform not valid"

        return qs

    def get_filtered_table(self, qs):
        if self.tableClassFactory:
            f = self.tableClassFactory
            table = f(qs)
        else:
            table = self.tableClass(qs)
        django_tables2.RequestConfig(self.request, paginate=False).configure(table)

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


class AufgabenUpdate (SuccessMessageMixin, isVorstandMixin, UpdateView):
    model = models.Aufgabe
    form_class = forms.AufgabeForm
    template_name = "arbeitsplan_aufgabenCreate.html"
    # success_url = "home.html"
    success_url = reverse_lazy("arbeitsplan-aufgabenVorstand")
    success_message = u'Die  <a href="%(url)s">Aufgabe %(id)s</a> wurde erfolgreich verändert.'
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

    def get_initial(self):
        """fill in the schnellzuweisung field if zuteilung exists"""

        initial = super(AufgabenUpdate, self).get_initial()

        initial = initial.copy()

        if self.object.zuteilung_set.count() > 0:
            initial['schnellzuweisung'] = [z.ausfuehrer for
                                           z in self.object.zuteilung_set.all()]

        # pp(initial)
        return initial

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
            # print "redirecting to delete", self.object.id
            return redirect('arbeitsplan-aufgabenDelete',
                            pk=self.object.id)

        # store the aufgabe
        super(AufgabenUpdate, self).form_valid(form)

        # manipulate the stundenplan
        stundenplan = collections.defaultdict(int,
                                              form.cleaned_data['stundenplan'])
        # print "stundenplan: ", stundenplan
        for u in range(models.Stundenplan.startZeit,
                       models.Stundenplan.stopZeit+1):
            anzahl = stundenplan[u]
            sobj, created = models.Stundenplan.objects.update_or_create(
                aufgabe=self.object,
                uhrzeit=u,
                defaults={'anzahl': anzahl})

        # check whether there are fast assignments
        if form.cleaned_data['schnellzuweisung']:
            try:
                mm = form.cleaned_data['schnellzuweisung']
                # pp(mm)
                for m in mm:
                    z, zcreated = models.Zuteilung.objects.get_or_create(
                        aufgabe=self.object,
                        ausfuehrer=m)
                    if created:
                        messages.success(self.request,
                                         u"Die Aufgabe wurde direkt an Mitglied {} zugeteilt!".format(
                                            m.__unicode__()))
                        m.mitglied.zuteilungBenachrichtigungNoetig = True
                        m.mitglied.save()
                    else:
                        messages.success(self.request,
                                         u"Die Aufgabe war bereits an Mitglied {} zugeteilt.".format(
                                             m.__unicode__()))

                        # TODO: das abschalten, nur für Testzwekce!
                        # m.mitglied.zuteilungBenachrichtigungNoetig = True
                        # m.mitglied.save()
            except Exception as e:
                # print e, form.cleaned_data['schnellzuweisung'], self.object
                messages.error(self.request,
                               u"Die Aufgabe konnte nicht unmittelbar an ein Mitglied zugeteilt werden")

        return redirect(self.request.get_full_path())


class AufgabeLoeschen(isVorstandMixin, DeleteView):
    model = models.Aufgabe
    success_url = reverse_lazy('arbeitsplan-aufgabenVorstand')
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
            return redirect('arbeitsplan-aufgabenVorstand')


###############################

class ListAufgabenVorstandView (isVorstandMixin, FilteredListView):
    filterform_class = forms.AufgabenDatumFilter
    title = "Alle Aufgaben anzeigen"
    filtertitle = "Filter nach Aufgabengruppe oder Zeitintervall"
    tabletitle = "Aufgabenliste"
    filterconfig = [('aufgabengruppe', 'gruppe__gruppe'),
                    ('von', 'datum__gte'),
                    ('bis', 'datum__lte'),
                    ]
    model = models.Aufgabe
    tableClass = AufgabenTableVorstand

    intro_text = """
    Die Tabelle zeigt die existierenden Aufgaben an.
    Diese Vorstandssicht zeigt mehr Informationen
    als die Sicht der normalen Mitglieder.
    """


class ListAufgabenView (FilteredListView):

    # filterform_class = forms.AufgabengruppeFilterForm
    filterform_class = forms.AufgabenDatumFilter
    title = "Aufgaben mit Arbeitsbedarf anzeigen"
    filtertitle = "Filter nach Aufgabengruppe oder Zeitintervall"
    tabletitle = "Aufgabenliste"
    tableClass = AufgabenTable

    filterconfig = [('aufgabengruppe', 'gruppe__gruppe'),
                    ('von', 'datum__gte'),
                    ('bis', 'datum__lte'),
                    ]
    model = models.Aufgabe
    intro_text = """
    Die Tabelle zeigt die anstehenden Aufgaben an.
    <ul>
    <li> Aufgaben ohne Datum sind an flexiblen Terminen zu erledigen. </li>
    <li> Bei Aufgaben mit Datum erfolgt die Zeitabsprachen individuell oder nach Einteilung. </li>
    <li> Die Spalte Verantwortlicher benennt den Koordinator der Aufgabe. </li>
    <li> Die Spalte Quickmeldung erlaubt eine vereinfachte Meldung für eine Aufgabe. Klicken Sie auf das Handsymbol; ein Haken in der Zeile markiert Aufgaben, für die Sie sich gemeldet haben.</li>
    </ul>
    <p>
    Sie können die angezeigten Aufgaben nach Aufgabengruppe filtern (--- entfernt den Filter). Zusätzlich können Sie nach dem Datum der Aufgabe filtern (Aufgaben mit Datum in der Vergangenheit werden aber grundsätzlich nicht angezeigt). Wählen Sie die Filter aus und klicken auf "Filter anwenden".
    """
    ## todo_text = """
    ## <li> Spalten klickbar machen: Aufgabe, Verantowrtlicher (direkt email senden?)  </li>
    ## <li> Bemerkung als Popover umbauen?  </li>
    ## """

    def apply_filter(self, qs=None):
        """
        Filter out, in addition to the standard filters, all Aufgaben
        that are already satisfied.
        """

        qs = super(ListAufgabenView, self).apply_filter()

        qs = qs.filter(Q(datum__gte=datetime.date.today())|Q(datum=None))
        qs = [q for q in qs if q.is_open()]

        return qs


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
    success_url = reverse_lazy("homeArbeitsplan")
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
            # print k, v
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
    success_url = reverse_lazy("homeArbeitsplan")
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


class ListAufgabenTeamleader(FilteredListView):
    title = "Aufgaben, für die ich Team-Leiter bin"
    tabletitle = 'Aufgabenliste'
    model = models.Aufgabe
    tableClass = AufgabenTableTeamlead

    intro_text = """
    Diese Tabelle zeigt alle Aufgaben an, für die Sie Team-Leiter sind.
    """

    def get_data(self):
        qs = self.request.user.teamleader_set.all()
        return qs


########################################################################################
#########   MELDUNG
########################################################################################


class MeldungEdit (FilteredListView):


    def processUpdate(self, request):
        for k, value in request.POST.iteritems():
            if (k.startswith('bemerkung') or
                k.startswith('prefMitglied') or
                k.startswith('prefVorstand')):

                key, id = k.split('_', 1)

                id = int(id)

                safeit = False
                mailcomment = []

                try:
                    m = models.Meldung.objects.get(id=id)
                except models.Meldung.DoesNotExist:
                    print "consistency of database destroyed"
                    # TODO: display error
                    continue

                if ((not m.aufgabe.datum ==  None) and
                    (m.aufgabe.datum < datetime.date.today())):
                    messages.error(request,
                                   u"""Die Aufgabe {0} liegt in der Vergangenheit.
                                   Solche Meldungen können nicht verändert werden.""".
                                   format(m.aufgabe.aufgabe))
                    continue

                if key == 'bemerkung':
                    if m.bemerkung <> value:
                        m.bemerkung = value
                        safeit = True
                        mailcomment.append("Neue Bemerkung")
                        messages.success(request,
                                         u"Bei Aufgabe {0} wurde die Bemerkung aktualisiert".
                                         format(m.aufgabe.aufgabe))

                if (key == 'bemerkungVorstand'
                    and isVorstand(self.request.user)):

                    if m.bemerkungVorstand != value:
                        m.bemerkungVorstand = value
                        safeit = True
                        messages.success(request,
                                         u"Bei Aufgabe {0} wurde die Bemerkung des Vorstandes aktualisiert".
                                         format(m.aufgabe.aufgabe))

                if key == 'prefMitglied':
                    # print value, m.prefMitglied, models.Meldung.MODELDEFAULTS['prefMitglied']
                    # print type(value), type(m.prefMitglied), type(models.Meldung.MODELDEFAULTS['prefMitglied'])

                    if m.prefMitglied != value:
                        safeit = True

                        if (m.prefMitglied ==
                            models.Meldung.MODELDEFAULTS['prefMitglied']):
                            mailcomment.append("Neue Meldung")
                            messages.success(request,
                                             u"Sie haben sich für  Aufgabe {0} gemeldet. "
                                             u"Der Vorstand wird dies  "
                                             u"prüfen und ggf. einen Termin zusagen. "
                                             u"WICHITG: Sie können NICHT davon ausgehen, "
                                             u"dass Sie diese Aufgaben zugeteilt bekommen!".
                                             format(m.aufgabe.aufgabe))
                        elif (int(value) ==
                              models.Meldung.MODELDEFAULTS['prefMitglied']):
                            # print "zurueckgezogen"
                            # TODO: CHECK
                            # TODO: das muss man am besten direkt verbieten, wenn es schon eine Zuteilung gibt!
                            # first: check whether such a Zuteilung already exsts
                            try:
                                zu = models.Zuteilung.objects.get(aufgabe=m.aufgabe,
                                                                  ausfuehrer=m.melder)

                                # it exists! we have to recheck this and inform user
                                mailcomment.append(u"Versuch eine Meldung zurückzuziehen, für die schon Zuteilung bestand. Versuch abgewiesen.")
                                safeit = False # this is important! Reason to initialize safeit up front
                                messages.error(request,
                                               u"Sie haben versucht, die Meldung für Aufgabe {0} zurückzuziehen."
                                               u"Allerdings wurde diese Aufgaben Ihnen bereits zugeteilt. "
                                               u"Leider können Sie daher die Meldung nicht mehr zurückziehen."
                                               u"Setzen Sie sich bitte mit dem Aufgabenverantwortlichen in Verbindung.".format(m.aufgabe.aufgabe)
                                )
                            except models.Zuteilung.DoesNotExist:
                                mailcomment.append("Meldung zurueckgezogen")
                                messages.success(request,
                                                 u"Sie haben die Meldung für  Aufgabe {0} zurückgezogen. ".
                                                 format(m.aufgabe.aufgabe))
                                safeit = True
                        else:
                            mailcomment.append("Praeferenz aktualisiert.")
                            messages.success(request,
                                             u"Bei Aufgabe {0} wurde die Präferenz aktualisiert".
                                             format(m.aufgabe.aufgabe))

                        m.prefMitglied = value

                if key == 'prefVorstand' and isVorstand(self.request.user):
                    if m.prefVorstand <> value:
                        m.prefVorstand  = value
                        safeit = True
                        messages.success(request,
                                         u"Bei Aufgabe {0} wurde die Präferenz des Vorstandes aktualisiert".
                                         format(m.aufgabe.aufgabe))

                if safeit:
                    m.save()

                if mailcomment:
                    notifyVorstand (m, mailcomment)

            else:
                # not interested in those keys
                pass


class MeldungenListeView (FilteredListView):
    title = "Alle Meldungen anzeigen"
    tableClass = MeldungListeTable
    tabletitle = "Meine Meldungen"

    # TODO: understand how to use reverse / reverse_lazy here
    # This is odd, why does reverse_lazy only return the object?

    intro_text = format_html(("Ein Übersicht über alle von Ihnen eingegeben Meldungen. "
                              'Editieren Sie bitte über die Funktion <a href="/arbeitsplan/meldung/">Melden</a> im Menü Meldung.'))

    def get_data(self):
        qs = (models.Meldung.objects.
              filter(melder=self.request.user).
              exclude(prefMitglied=models.Meldung.GARNICHT))
        return qs



class CreateMeldungenView (MeldungEdit):
    """
    Display a table with all Aufgaben and fields
    to set preferences and add remarks.
    Accept updates and enter them into the Meldung table.
    Intended for the non-Vorstand user.
    """

    title = "Meldungen für Aufgaben eintragen oder ändern"
    # filterform_class = forms.AufgabengruppeFilterForm
    filterform_class = forms.GemeldeteFilter
    filtertitle = "Meldungen filtern"
    tabletitle = "Meldungen für Aufgaben eintragen oder ändern"
    tableform = {'name': "eintragen",
                 'value': "Meldungen eintragen/ändern"}


    def gemeldeteAufgaben(self, qs, gemeldet):
        """
        Filter out Aufgaben for which the user has created a Meldung,
        or not, all all Aufgaben.

        See forms.GemeldeteAufgabenFilterForm for the definition of the tags
        """

        if gemeldet == "GA" or gemeldet == "NG":
            # first, find out the Meldung this user has made:
            meld = models.Meldung.objects.filter(melder=self.request.user)

            if gemeldet == "GA":
              meld = meld.exclude(prefMitglied=models.Meldung.GARNICHT)
            else:
                meld = meld.filter(prefMitglied=models.Meldung.GARNICHT)

            # turn this into aufgaben IDs
            aufIDs = [m.aufgabe.id for m in meld]
            # and get an Aufgaben queryset out of these ids
            aufgQs = models.Aufgabe.objects.filter(id__in=aufIDs)
            # interset this with what we already have as queryset:
            qs = qs & aufgQs

        return qs

    filterconfig = [('aufgabengruppe', 'gruppe__gruppe'),
                    ('von', 'datum__gte'),
                    ('bis', 'datum__lte'),
                    ('gemeldet', gemeldeteAufgaben),
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
    Aufgaben aus der Vergangenheit werden nicht angezeigt!
    Wenn Sie sich im Laufe des Jahres für Aufgaben ohne Datum
    eintragen wollen, sprechen Sie dies bitte mit dem zuständigen
    Vorstand/Teamleiter ab.
    <p>
    Sie können die Aufgabenliste eingrenzen, in dem Sie nach
    Aufgabengruppen filtern (--- entfernt den Filter).
    Zusätzlich können Sie (mit dem zweiten Filter)
    die Liste der Aufgaben weiter einschränken auf Aufgaben,
    für die Sie bereits eine Meldung abgegeben haben
    (nützlich, um Quickmeldungen zu verfeinern)
    oder keine Meldung (nützlich, um sich für weitere Aufgaben zu melden).
    Die dritte und vierte Filtermöglichkeit grenzt das Datum der Aufgaben ein.
    <p>
    Wählen Sie aus der jeweiligen  Liste aus und drücken
    dann auf `Filter anwenden'.
    <p>
    Zeigen Sie auf den Aufgabennamen um ggf. weitere Information
    über die Aufgabe zu sehen.
    <p>
    <b> WICHTIG: Eine Meldung hier ist nur ein WUNSCH; es ist
    nicht die automatische Zusgae, für die Aufgabe auch
    eingeteilt zu werden.
    </b>
    """

    ## todo_text = """
    ## <li> Über Button-Farben nachdenken </li>
    ## <li> Über das Nutzen von Tooltips nachdenken - zweischneidig </li>
    ## """


    def apply_filter(self, qs=None):
        """
        Filter out, in addition to the standard filters, all Aufgaben
        that are already satisfied.
        """

        qs = super(CreateMeldungenView, self).apply_filter()
        qs = qs.filter(Q(datum__gte=datetime.date.today())|Q(datum=None))

        qs = [q for q in qs if q.is_open()]

        return qs

    def get_queryset(self):

        qsAufgaben = self.apply_filter()

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
            try:
                m, newcreateFlag = models.Meldung.objects.get_or_create(
                    aufgabe=a,
                    melder=self.request.user,
                    defaults = models.Meldung.MODELDEFAULTS,
                )
            except models.Meldung.MultipleObjectsReturned:
                messages.error(self.request,
                               format_html(
                                   u"Ein Datenbankfehler trat auf! "
                                   u'Bitte schicken Sie '
                                   u'<a href="mailto:hkarl@ieee.org?subject=SVPB: QAWX&body=A: {}, U: {}">'
                                   u'diese email</a> ab. Es wäre schön wenn Sie schildern '
                                   u'könnten, welche Handlungen Sie kurz zuvor durchführten.'
                                   ,
                                   a.id,
                                   self.request.user.id,
                                   ))
                return self.get_filtered_table([])

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
                    ('praeferenz', 'prefMitglied__in'),
                    ('praeferenzVorstand', 'prefVorstand__in'),
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
        # print request.POST
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
        # print aufgabeid

        try:
            aufgabe = models.Aufgabe.objects.get(pk=int(aufgabeid))
            meldung, created = models.Meldung.objects.get_or_create(aufgabe=aufgabe,
                                                                    melder=self.request.user)

            if created | (meldung.bemerkung == ""):
                meldung.prefMitglied = models.Meldung.GERNE
                meldung.bemerkung = "QUICKMELDUNG"
                meldung.save()

                messages.success(self.request,
                                 u"Danke! Sie haben sich für Aufgabe " +
                                 aufgabe.aufgabe + u" gemeldet. Der Vorstand wird dies prüfen und ggf. einen Termin zusagen.")
                notifyVorstand(meldung, ["QUICKMELDUNG"])
            else:
                messages.warning(self.request,
                                 u"Ihre Schnellmeldung wurde nicht eingetragen; vermutlich existiert bereits eine Meldung von Ihnen.")

        except models.Aufgabe.DoesNotExist:
            messages.error(self.request,
                           u"Die genannate Aufgabe " + str(aufgabeid) + u" existiert nicht!")


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
        # print table
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

        # print self, self.aufgabeQs

        if ("AM" in busy):
            if self.aufgabengruppe:
                """Only keep those users who have a meldung for an aufagebn in this gruppe"""
                ## for q in qs:
                ##     print (q.meldung_set
                ##            .exclude(prefMitglied=models.Meldung.GARNICHT)
                ##            .filter(aufgabe__gruppe__gruppe=self.aufgabengruppe)
                ##            .count())
                qs = [q for q in qs
                      if q.meldung_set
                           .exclude(prefMitglied=models.Meldung.GARNICHT)
                           .filter(aufgabe__gruppe__gruppe=self.aufgabengruppe)
                           .count()]

            # are we looking at a SINGLE Aufgabe?
            # then filter down further to only those users
            # who have a meldung for this Aufgabe

            try:
                if self.aufgabeQs.count() == 1:
                    # print "just a single one"
                    aufgabe = self.aufgabeQs[0]
                    # print aufgabe

                    qs = [q for q in qs
                          if q.meldung_set
                               .exclude(prefMitglied=models.Meldung.GARNICHT)
                               .filter(aufgabe=aufgabe)
                               .count()]
            except:
                pass

        if "FR" in busy:
            # show users that can still accept more work
            qs = [q
                  for q in qs
                  if q.mitglied.zugeteilteStunden() < JAHRESSTUNDEN]
        elif "BU" in busy:
            # show users that are already busy
            qs = [q
                  for q in qs
                  if q.mitglied.zugeteilteStunden() >= JAHRESSTUNDEN]

        return qs

    def AktiveAufgaben_Filter(self, qs, aktive):
        """filter out jobs froms the past?"""

        # print qs

        if aktive:
            qs = qs.exclude(datum__lte=datetime.date.today())

        return qs

    def ungenuegend_zuteilungen_filter(self, qs, restrict):
        # print qs, restrict
        if restrict == 'UN':
            # qs=qs.filter(anzahl__gt=zuteilung_set.count())
            qs = (qs.annotate(num_Zuteilung=Count('zuteilung')).
                  filter(anzahl__gt=F('num_Zuteilung')))
        elif restrict == 'ZU':
            qs = (qs.annotate(num_Zuteilung=Count('zuteilung')).
                  filter(anzahl__lte=F('num_Zuteilung')))
        return qs

    filtertitle = "Nach Aufgabengruppen oder Mitgliedern filtern"
    # filterform_class = forms.PersonAufgabengruppeFilterForm
    filterform_class = forms.ZuteilungMitglied
    filterconfigAufgabe = [('aufgabengruppe', 'gruppe__gruppe'),
                           ('zuteilungen_ausreichend',
                            ungenuegend_zuteilungen_filter),
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
    Filtern Sie nach Mitgliedsnamen oder Aufgabengruppe. Zusätzlich können Sie nach Auslastung und Meldung der Mitglieder filtern: nur solche mit Meldungen für diese Aufgabengruppe (genauer: für irgendeine Aufgabe in der gewählten Gruppe), Mitglieder mit noch freier Arbeitskapazität, oder ausgelastete Mitglieder.
    <p>
    Hinweise:
    <ul>
    <li> In den Feldern der Tabelle wird (neben dem Auswahlkreuzchen) in Klammern die Präferenz bzw. des Vorstands für diese Aufgabe angezeigt. </li>
    </ul>
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

        # we need that in the user filter:
        self.aufgabeQs = aufgabeQs
        self.filterconfig = self.filterconfigUser
        userQs = super(ManuelleZuteilungView, self).apply_filter(userQs)

        # print "apply filter done"
        # print userQs
        # print aufgabeQs
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
                            (' ({0} / {1})'.format(m.prefMitglied,
                                                  m.prefVorstand) +
                             (("<br><small>" + m.bemerkung + "</small>") if m.bemerkung else "")
                             ),

                            )
                statuslist[str(u.id)+"_"+str(m.aufgabe.id)]='0'

            zQs =  models.Zuteilung.objects.filter(ausfuehrer=u)
            ## if self.aufgabengruppe <> None:
            ##     zQs = zQs.filter(aufgabe__gruppe__gruppe =  self.aufgabengruppe)
            zQs = zQs.filter(aufgabe__in=aufgabenQs)

            for z in zQs:
                tag = unicodedata.normalize('NFKD', z.aufgabe.aufgabe).encode('ASCII', 'ignore')
                meldung, meldungCreated = z.aufgabe.meldung_set.get_or_create(
                    melder=u,
                    aufgabe=z.aufgabe,
                    defaults= models.Meldung.MODELDEFAULTS,
                    )
                tmp[tag] = (1,
                            'box_'+ str(u.id)+"_"+str(z.aufgabe.id),
                            (' ({0} / {1})'.format(meldung.prefMitglied,
                                                  meldung.prefVorstand)  +
                             ((" <br><small>" + meldung.bemerkung + "</small>") if meldung.bemerkung else ""))
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
            tmp['offen'] = u.mitglied.arbeitslast - tmp['zugeteilt']

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

                z, created = models.Zuteilung.objects.get_or_create(
                    aufgabe=aufgabeObj,
                    ausfuehrer=ausfuehrerObj)

                if not created:
                    messages.debug(request,
                                   u"warnung: Aufgabe {0} war bereits an {1} {2} zugeteilt"
                                   .format(
                                       aufgabeObj.aufgabe,
                                       ausfuehrerObj.first_name,
                                       ausfuehrerObj.last_name))

                messages.success(request,
                                 u"Aufgabe {0} wurde an {1} {2} zugeteilt"
                                 .format(
                                     aufgabeObj.aufgabe,
                                     ausfuehrerObj.first_name,
                                     ausfuehrerObj.last_name))

                # print "setting (cause of add)  zuteilung benachrichtigung noetig for ", ausfuehrerObj
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

                # print "setting (cause of delete) zuteilung benachrichtigung noetig for ", ausfuehrerObj
                ausfuehrerObj.mitglied.zuteilungBenachrichtigungNoetig = True
                ausfuehrerObj.mitglied.save()


        # TODO: emails senden?

        return redirect(self.request.get_full_path())


class ZuteilungLoeschenView(isVorstandMixin, DeleteView):
    # TODO: Merge this with AufgabeLoeschen
    model = models.Zuteilung
    success_url = "/arbeitsplan/zuteilungAnzeige/all/"
    template_name = "zuteilung_confirm_delete.html"

    def get(self, request, *args, **kwargs):
        try:
            r = super(ZuteilungLoeschenView, self).get(request, *args, **kwargs)
            return r
        except Exception as e:
            # print e
            messages.error(self.request,
                           'Die Zuteilung konnte nicht gelöscht werden')

            return redirect('/arbeitsplan/zuteilungAnzeige/all/')
        
    def get_success_url(self):
        messages.success(self.request,
                 "Die Zuteilung wurde erfolgreich gelöscht.")

        return super(ZuteilungLoeschenView, self).get_success_url()

class ZuteilungUebersichtView(isVorstandMixin, FilteredListView):
    title = "Übersicht der Aufgaben und Zuteilungen"
    tableClassFactory = staticmethod(StundenplanTableFactory)
    tabletitle = "Aufgaben mit benötigten/zugeteilten Personen"

    show_stundenplan = False

    model = models.Aufgabe

    def ungenuegend_zuteilungen_filter(self, qs, restrict):
        # print qs, restrict
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
        django_tables2.RequestConfig(self.request, paginate=False).configure(table)

        return table

    def annotate_data(self, qs):

        data = []
        for aufgabe in qs:
            newEntry = defaultdict(int)
            newEntry['id'] = aufgabe.id
            newEntry['aufgabe'] = mark_safe(
                u'<a href="{1}">{0}</a>'
                .format(aufgabe.aufgabe,
                        reverse('arbeitsplan-aufgabenEdit',
                                args=(aufgabe.id,))))

            newEntry['required'] = aufgabe.anzahl
            newEntry['gruppe'] = aufgabe.gruppe.gruppe
            newEntry['gemeldet'] = aufgabe.numMeldungen()
            newEntry['zugeteilt'] = aufgabe.zuteilung_set.count()
            newEntry['editlink'] = mark_safe(
                u'<a href="{0}?mitglied_ausgelastet=AM&filter=Filter+anwenden">'
                'Zuteilung</a>'.format(
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


class StundenplaeneEdit(isVorstandMixin, FilteredListView):

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

    In der Tabelle werden Spalten pro Uhrzeit angezeigt.<br>
    In den Spaltenüberschriften wird<br>
    in Klammer wird jeweils (Anzahl benötigte Mitglieder / Anzahl
    schon zugeteilte Mitglieder) angezeigt.
    """

    todo_text = """Anzahl noch benötigte Uhrzeiten anders hervorheben?
    Nur Differenz anzeigen? Umstellen auf Kontakte statt
    Vornamen / Nachnamen """


    def get_filtered_table(self, qs, aufgabe):
        table = self.tableClassFactory(qs, aufgabe)
        django_tables2.RequestConfig(self.request, paginate=False).configure(table)

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

        self.tabletitle = (self.tabletitle_template
                           + u" - Aufgabe: " + aufgabe.aufgabe
                           + " " + aufgabe.datum.isoformat())

        data = []
        checkedboxes = []

        stundenplan = aufgabe.stundenplan_set.filter(anzahl__gt=0)

        zugeteilteUser = [z.ausfuehrer for z in aufgabe.zuteilung_set.all()]

        # print "Stundenplan fuer Auzfgabe: ", stundenplan
        # print "zugeteilte User: ",  zugeteilteUser

        # construct the checkboxes string:
        # userid_uhrzeit, if that user works on that time

        # for each zuteilung, the following gives a separate queryset:
        stundenzuteilungenQuerysets = [z.stundenzuteilung_set.all()
                                       for z in aufgabe.zuteilung_set.all()]
        checkedboxes = [str(sz.zuteilung.ausfuehrer.id) + "_" + str(sz.uhrzeit)
                        for szQs in stundenzuteilungenQuerysets
                        for sz in szQs]
        # print checkedboxes

        # construct the list of dicts for users:
        for u in zugeteilteUser:
            newEntry = {'last_name': u.last_name,
                        'first_name': u.first_name,
                        }
            zuteilungThisUser = aufgabe.zuteilung_set.filter(ausfuehrer=u)
            if zuteilungThisUser.count() != 1:
                messages.error(u'Error 13: ' + aufgabe.__unicode__()
                               + u' - ' + u.__unicode__())

            newEntry['anzahl'] = (zuteilungThisUser[:1].get().zusatzhelfer,
                                  'anzahl_{}'.format(str(u.id)))

            stundenzuteilung = (zuteilungThisUser[:1].get().
                                stundenzuteilung_set.values_list('uhrzeit',
                                                                 flat=True))
            # print zuteilungThisUser
            for s in stundenplan:
                newEntry['u'+str(s.uhrzeit)] = ((1 if s.uhrzeit in stundenzuteilung
                                                 else 0),
                                                 ('uhrzeit_' +
                                                  str(u.id) + "_" +
                                                  str(s.uhrzeit)),
                                                 )
            data.append(newEntry)

        # print data

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

        # print self.request.POST

        if self.request.POST.get('checkedboxes'):
            tmp = [x.split('_')
                   for x in
                   self.request.POST.get('checkedboxes').split(',')
                  ]
        else:
            tmp = []

        # pp(tmp)
        checkedboxes = [(int(x[0]), int(x[1])) for x in tmp ]
        # print "checkboxes: ", checkedboxes

        # any values to add?
        for v in self.request.POST:

            if v.startswith('anzahl'):
                # what is the anzahl value?
                anzahl = int(self.request.POST.get(v))
                # print("anzahl: ", anzahl)

                _tmp, uid = v.split('_')
                zuteilung = models.Zuteilung.objects.get (ausfuehrer__id = uid,
                                                          aufgabe__id = aufgabeid)

                if zuteilung.zusatzhelfer <> anzahl:
                    zuteilung.zusatzhelfer = anzahl
                    zuteilung.save()

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
    success_url = reverse_lazy("homeArbeitsplan")

    def get_form_kwargs(self):

        kwargs = super(CreateLeistungView, self).get_form_kwargs()

        if "Alle" in self.request.path:
            kwargs['user'] = None
        else:
            kwargs['user'] = self.request.user

        return kwargs

    def form_valid(self, form):
        # print "in Create Leistung View form_valid"
        leistung = form.save(commit=False)
        leistung.melder = self.request.user
        leistung.save()

        # print "saved leistung"

        return HttpResponseRedirect(CreateLeistungView.success_url)

# class CreateLeistungDritteView (CreateView):

####################################

class DeleteLeistungView(DeleteView):
    model = models.Leistung
    success_url = reverse_lazy("homeArbeitsplan")
    template_name = "leistung_confirm_delete.html"

    def get_object(self):
        obj = super(DeleteLeistungView, self).get_object()
        print obj

        if (not (self.request.user == obj.melder) or
            (obj.status == models.Leistung.ACK) or
            (obj.status == models.Leistung.NEG)):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        return obj

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

        res = [(-1, 'Arbeitssoll', -1, self.request.user.mitglied.arbeitslast,)]
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
                           u"Sie dürfen diese Funktion nicht benutzen!"
                           )

            redirect("homeArbeitsplan")


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
                                   u"Sie dürfen Leistungsmeldungen"
                                   u" für diese Aufgabe nicht bearbeiten!")
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
                                     l.aufgabe.aufgabe)
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

    filterconfig = [('first_name', 'first_name__icontains'),
                    ('last_name', 'last_name__icontains'),
                    ]


    model = models.User

    intro_text = """
    Ein Überblick über die von den Mitgliedern geleistete Arbeit,
    basiered auf den vorliegenden Leistungsmeldungen und deren
    Bewertungen durch Vorstände. Zuteilungen werden separat aufgeführt. <p>
    Die Filter bezeichnen:
    <ul>
    <li><b>Kein Statusfilter</b>: Keine Filterung anhand der
    geleisteten Stunden </li>
    <li><b>Pensum erfüllt</b>: Nur Nutzer anzeigen, deren akzeptiere
    Leistungsmeldungen
    größer oder gleich der individuellen Arbeitslast liegen</li>
    <li><b>Chance zu erfüllen</b>: Nur Nutzer anzeigen, deren akzeptiere
    Leistungsmeldungen noch nicht die Arbeitslast erfüllt, aber deren bereits
    akzeptierte Leistungen, deren offene Leistungsmeldungen, sowie die Stunden
    der zugeteilten Aufagebn (die in der Zukunft liegen oder kein Datum haben)
    die Arbeitslast übersteigt. <br>
    Dieser Filter zeigt nur dann das erwartete Resultat an, wenn alle Stunden
    aus vergangen Arbeitszuteilungen auch schon als Leistungsmeldung vorliegen.
    Nicht gemeldete Stunden vergangenen Aufgaben werden hier nicht
    berücksichtigt,
    so dass ggf. zu viele Personen hier angezeigt werden.
    </li>
    <li><b> Pensum kann nicht erfüllt werden</b>:
    Dieser Filter zeigt Personen an, bei denen die akzeptieren Leistungen,
    die offenen Leistungen, sowie die Stunden aus zugeteilten Aufgaben in der
    Zukunft und zugeteilte Aufgaben ohne Datum insgesamt nicht ausreichen, die
    invdividuelle Arbeitslast zu erfüllen.
    <p>
    Auch hier werden Aufgaben in der Vergangenheit, für die noch keine Leistungen
    eingetragen worden, nicht brücksichtigt. Entsprechend werden auch hier
    ggf. zu viele Personen angezeigt.
    </li>
    </ul>
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
            'OK': lambda u: u['AK'][0] >= u['user'].mitglied.arbeitslast,
            'CH': lambda u: ((u['AK'][0] < u['user'].mitglied.arbeitslast) and
                             ((u['AK'][0] or 0) +
                              (u['OF'][0] or 0) +
                              u['future'] + u['nodate'] >=
                             u['user'].mitglied.arbeitslast)
                             ),
            'PR': lambda u: ((u['AK'][0] or 0) +
                             (u['OF'][0] or 0) +
                             u['future'] + u['nodate'] <
                             u['user'].mitglied.arbeitslast),
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
        return redirect ('homeArbeitsplan')


########################
## BENACHRICHTIGUNGEN
########################

class ListEmailTemplate(isVorstandMixin, ListView):
    from post_office.models import EmailTemplate
    model = EmailTemplate
    template_name = "listEmail.html"

class FilteredEmailCreateView (isVorstandOrTeamleaderMixin, FilteredListView):

    tableform = {'name': "eintragen",
                 'value':
                 "Benachrichtigungen eintragen"}

    intro_text = """Versenden von Benachrichtungen:
    Wählen Sie die zu benachrichtigenden Zeilen durch die
    Checkbox in der letzten Spalte aus (default: alle).
    Sie können pro Zeile einen Kommentar eintippen,
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
                             u"Vergessen Sie nicht, die Benachrichtigungen explizit abzuschicken!")

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
             'vorstand': instance.aufgabe.verantwortlich,
             'teamleader': instance.aufgabe.teamleader,
             }
        return d

class MeldungNoetigEmailView(isVorstandMixin, FilteredEmailCreateView):
    """Display a list of all users where not enough Zuteilungen have happened so far.
    """

    title = "Benachrichtigung für Mitglieder mit ungenügenden Meldungen/Zuteilungen"

    model = models.Mitglied

    tableClass = MeldungsAufforderungsEmailTable
    filterform_class = None
    filterconfig = []
    emailTemplate = "meldungsAufforderung"

    def getUser(self, instance):
        return instance.user

    def annotate_data(self, qs):
        qs = super(MeldungNoetigEmailView, self).annotate_data(qs)
        qs = [q for q in qs if q.zugeteilteStunden() < q.arbeitslast]

        for q in qs:
            q.sendit = True

        return qs

    def constructTemplateDict(self, instance):
        """this view operates on models.User, so instance is a user object.
        We have to find all zuteilungen for this user and stuff this data into
        the construct Tempalte Dict for the email to render
        """

        d = {'u': instance.user,
             'numZuteilungen': instance.zugeteilteAufgaben(),
             'stundenZuteilungen': instance.zugeteilteStunden(),
             'numMeldungen': instance.gemeldeteAnzahlAufgaben(),
            }

        # print d
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

        TODO: perhgaps filter here for zuteilung in the future?
        """

        d = {'first_name': instance.user.first_name,
             'last_name': instance.user.last_name,
             'u': instance.user,
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

            # print sent, failed

            if sent > 0:
                messages.success(request,
                                 "Es wurden {0} Nachrichten versandt"
                                 .format(sent))
            if failed > 0:
                messages.error(request,
                               "Es konnten {0} Nachrichten nicht versendet"
                               "werden! Sysadmin kontaktieren!".
                               format(failed))

        return redirect('homeArbeitsplan')


################################
## Impersonateion

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



##############


# TODO: This really should go into the svpb.views, but that would
# create cricular imports because of the FilteredListView :-(
# this will need serious code refactoring some time

##########

# A siomple home-view to provide aufgabengruppe to the template
# seems heavy-handed, but no other option seems handy to push data into a TemplateView

class HomeView(TemplateView):

    def get_context_data(self, *args, **kwargs):
        c = super(HomeView, self).get_context_data()
        c.update({'aufgabengruppen': [
            {'name': a.gruppe,
             'id': a.id}
            for a in models.Aufgabengruppe.objects.all()],
                  'bla': 'blub', })
        return c
