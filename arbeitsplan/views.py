# -*- coding: utf-8 -*-

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import View, ListView, CreateView, FormView, UpdateView 
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.contrib.auth import logout
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from collections import defaultdict
from pprint import pprint as pp


import django_tables2
import unicodedata

# Arbeitsplan-Importe: 
import models
import forms
from tables import *  # TODO: change import not to polute name space


#################

def isVorstand(user):
    return user.groups.filter(name='Vorstand')


class isVorstandMixin(object):
    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def dispatch(self, *args, **kwargs):
        return super(isVorstandMixin, self).dispatch(*args, **kwargs)

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
    # filterconfig: a list of tuples, with (fieldnmae in form, filter keyword to apply)     
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

        return context

    def apply_filter(self, qs=None):

        if qs is None:
            qs = self.model.objects.all()

        if 'filter' not in self.request.GET:
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
                qs = qs.filter(**{filterexp: initialValues})
        else:
            self.filterform = self.filterform_class(self.request.GET)
            filterconfig = self.filterconfig

            if self.filterform.is_valid():
                # apply filters
                print "filter: ", self.filterform.cleaned_data
                for fieldname, filterexp in filterconfig:
                    print fieldname, filterexp
                    if ((self.filterform.cleaned_data[fieldname] is not None) and
                        (self.filterform.cleaned_data[fieldname] != "")):
                        qs = qs.filter(**{filterexp: self.filterform.cleaned_data[fieldname]})
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


class NameFilterView(View):

    def applyFilter(self, request):

        qs = models.User.objects.all()

        form = self.filterFormClass(request.GET)
        if form.is_valid():
            if 'filter' in request.GET:
                last_name = form.cleaned_data['last_name']

                if last_name != "":
                    qs = qs.filter(last_name__icontains=last_name)

                first_name = form.cleaned_data['first_name']
                if first_name != "":
                    qs = qs.filter(first_name__icontains=first_name)

        else:
            print "filter not valid"

        return (qs, form)

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

        return context

    def get_form_kwargs(self):
        kwargs = super(AufgabenUpdate, self).get_form_kwargs()
        kwargs.update({
            'request': self.request
            })
        return kwargs

    def form_valid(self, form):

        # store the aufgabe
        super(AufgabenUpdate, self).form_valid(form)

        # manipulate the stundenplan
        stundenplan = form.cleaned_data['stundenplan']
        for sDB in models.Stundenplan.objects.filter(aufgabe=self.object):
            print sDB
            if sDB.uhrzeit in stundenplan:
                if stundenplan[sDB.uhrzeit] != sDB.anzahl:
                    sDB.anzahl = stundenplan[sDB.uhrzeit]
                    sDB.save()
                    del stundenplan[sDB.uhrzeit]
            else:
                sDB.delete()

        # all the keys remaining in stundenplan have to be added
        for uhrzeit, anzahl in stundenplan.iteritems():
            sobj = models.Stundenplan(aufgabe = self.object,
                                      uhrzeit = uhrzeit,
                                      anzahl = anzahl)
            sobj.save()

        return redirect ("arbeitsplan-aufgaben")

###############################

class ListAufgabenView (FilteredListView):

    filterform_class = forms.AufgabengruppeFilterForm
    title = "Alle Aufgaben anzeigen"
    filterconfig = [('aufgabengruppe', 'gruppe__gruppe')]
    model = models.Aufgabe
    
    def get_queryset (self):

        if isVorstand (self.request.user):
            self.tableClass = AufgabenTableVorstand
        else:
            self.tableClass = AufgabenTable
            
        return self.get_filtered_table (self.model.objects.all())
    

#####################


class AufgabenCreate (CreateView):
    model = models.Aufgabe
    form_class = forms.AufgabeForm
    template_name = "arbeitsplan_aufgabenCreate.html"
    success_url = "home.html"
    title = "Neue Aufgabe anlegen"
    buttontext = "Aufgabe anlegen"

    def get_context_data (self, **kwargs):
        context = super (AufgabenCreate, self).get_context_data (**kwargs)
        context['title'] = self.title
        context['buttontext'] = self.buttontext
        context['stundenplan'] = [(u, 0) for u in range(8,24)]

        return context 
            
    def get_form_kwargs (self):
        kwargs = super(AufgabenCreate, self).get_form_kwargs()
        kwargs.update({
            'request' : self.request
            })
        return kwargs
            
    def form_valid (self, form):

        # store the aufgabe
        super (AufgabenCreate, self).form_valid(form)

        # and now store the STundenplan entries
        for uhrzeit, anzahl  in form.cleaned_data['stundenplan'].iteritems():
            sobj = models.Stundenplan (aufgabe = self.object,
                                       uhrzeit = uhrzeit,
                                       anzahl = anzahl)
            sobj.save()
            
        
        return render (self.request,
                       self.get_success_url(),
                       {'msg': 'Die Aufgabe wurde erfolgreich angelegt.',
                        'msgclass': 'success'} )
    
                          

########################################################################################
#########   MELDUNG 
########################################################################################

class MeldungEdit  (FilteredListView):

    def processUpdate (self, request):
        for k, value in request.POST.iteritems():
            if (k.startswith('bemerkung') or
                k.startswith('prefMitglied') or
                k.startswith('prefVorstand') 
                ):
                key, tmp = k.split('_', 1)
                try:
                    id, choice = tmp.split('_', 1)
                except ValueError:
                    id = tmp
                    choice = None
                id = int(id)
                
                ## aufgabe = models.Aufgabe.objects.get(id=id)
                ## print key, id, choice, value, aufgabe 
                safeit = False
                
                ## m, newcreated = models.Meldung.objects.get_or_create(
                ##     aufgabe=aufgabe,
                ##     melder=self.request.user,
                ##     defaults = models.Meldung.MODELDEFAULTS, 
                ## )

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

                if key == 'bemerkungVorstand' and isVorstand(self.request.user):
                    if m.bemerkungVorstand <> value: 
                        m.bemerkungVorstand = value
                        safeit = True
                                        
                if key == 'prefMitglied':
                    if m.prefMitglied <> choice:
                        m.prefMitglied  = choice
                        safeit = True

                if key == 'prefVorstand' and isVorstand(self.request.user):
                    if m.prefVorstand <> choice:
                        m.prefVorstand  = choice
                        safeit = True

                if safeit: 
                    m.save()
            else:
                pass # not interested in those keys
        
    
class CreateMeldungenView (MeldungEdit):
    """
    Display a table with all Aufgaben and fields to set preferences and add remarks.
    Accept updates and enter them into the Meldung table. 
    Intended for the non-Vorstand user. 
    """

    title = "Meldungen für Aufgaben eintragen oder ändern"
    filterform_class = forms.AufgabengruppeFilterForm
    filtertitle = "Meldungen nach Aufgabengruppen filtern"
    tabletitle = "Meldungen für Aufgaben eintragen oder ändern"
    tableform = {'name': "eintragen",
                 'value': "Meldungen eintragen/ändern"}
    filterconfig = [('aufgabengruppe', 'gruppe__gruppe')]
    model = models.Aufgabe
    tableClass = MeldungTable 
        
    def get_queryset (self):

        qsAufgaben = self.apply_filter ()
        
        # fill the table with all aufgaben
        # overwrite preferences and bemerkung if for them, a value exists
        aufgabenliste = []
        for a in qsAufgaben:
            # initialize with values from Aufgabe
            d = {'aufgabe': a.aufgabe,
                 'gruppe': a.gruppe,
                 'datum' : a.datum,
                 'stunden': a.stunden,
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
        print "post in CreateMeldungenView"
        print request.POST

        self.processUpdate(request)

        return redirect ("arbeitsplan-meldung")
        
    
class MeldungVorstandView (isVorstandMixin, MeldungEdit):
    """Display a (filtered) list of all Meldungen from all Users,
    with all preferences.
    Allow Vorstand to update its fields and store them.
    """

    title = "Meldungen für Aufgaben bewerten"
    # filterform_class = forms.PersonAufgabengruppeFilterForm
    filterform_class = forms.PersonAufgGrpPraefernzFilterForm
    filtertitle = "Meldungen nach Person, Aufgabengruppen oder Präferenz filtern"
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


    def post (self,request, *args, **kwargs):
        print request.POST
        self.processUpdate(request)
        return redirect ('arbeitsplan-meldungVorstand')        

        
    ##     myForm = forms.MeldungForm (request.POST)
    ##     if myForm.is_valid():
    ##         # print "processing valid form"
    ##         # print myForm.cleaned_data

    ##         for k, userInput in myForm.cleaned_data.iteritems():
    ##             aid = int(k.split('a')[1])
    ##             # print aid, userInput

    ##             # try to find a meldung with that aid and for this user
    ##             try: 
    ##                 meldungStatus = models.Meldung.objects.get (aufgabe_id=aid,
    ##                                                             melder_id=request.user.id)
    ##             except:
    ##                 # print "get failed"
    ##                 meldungStatus = False

    ##             # print "mledung status",  meldungStatus
                    
    ##             if userInput:
    ##                 # we have to add or update the corresponding meldung
    ##                 if meldungStatus:
    ##                     # update existing object 
    ##                     newMeld = models.Meldung (aufgabe = models.Aufgabe.objects.get(id=aid),
    ##                                               erstellt = meldungStatus.erstellt, 
    ##                                               melder = request.user, 
    ##                                               id = meldungStatus.id)
    ##                 else:
    ##                     #create a new one:
    ##                     newMeld = models.Meldung (aufgabe = models.Aufgabe.objects.get(id=aid),
    ##                                               melder = request.user, 
    ##                                               )
                        
    ##                 # print newMeld
    ##                 newMeld.save()
    ##             else:
    ##                 # user does not work on a particular job;
    ##                 # if meldung exists, delete it

    ##                 if meldungStatus:
    ##                     meldungStatus.delete()
                        
                    
            
    ##         return redirect ('arbeitsplan-meldung')

    ##     # print "processing INvalid form"
    ##     return HttpResponse ("Form was invalid - what to do?")

    
########################################################################################
#########   ZUTEILUNG 
########################################################################################


        
    
        
class ListZuteilungenView (FilteredListView):
    title = "Alle Zuteilungen anzeigen"
    filterform_class = forms.PersonAufgabengruppeFilterForm
    tableClass = ZuteilungTable
    filtertitle = "Zuteilungen nach Personen oder Aufgabengruppen filtern"
    tabletitle = "Zuteilungen"
    filterconfig = [('aufgabengruppe', 'aufgabe__gruppe__gruppe'),
                    ('first_name', 'ausfuehrer__first_name__icontains'), 
                    ('last_name', 'ausfuehrer__last_name__icontains'),
                    ]
    
    def get_queryset (self):
        if (("all" in  self.request.path) and
            (isVorstand(self.request.user))): 
            qs = models.Zuteilung.objects.all()
        else:
            qs = models.Zuteilung.objects.filter (ausfuehrer =self.request.user)
            
        qs = self.apply_filter (qs)
        table =  self.get_filtered_table (qs)
        return table 



class ManuelleZuteilungView (isVorstandMixin, NameFilterView):
    """Manuelles Eintragen von Zuteilungen
    """

    # TODO: filter by preferences? show preferences in table?

    filterFormClass = forms.PersonAufgabengruppeFilterForm

    def get (self, request, aufgabe=None, *args, **kwargs):
        """Baue eine Tabelle zusammen, die den Zuteilungen aus der DAtenbank
        entspricht."""

        print self.request.get_full_path()        
        
        userQs, filterForm = self.applyFilter (request)

        if aufgabe:
            aufgabenQs = models.Aufgabe.objects.filter (id=aufgabe)
        else: 
            if filterForm.cleaned_data['aufgabengruppe'] <> None:
                print filterForm.cleaned_data['aufgabengruppe']
                aufgabenQs = models.Aufgabe.objects.filter (gruppe__gruppe = filterForm.cleaned_data['aufgabengruppe'])
            else:
                aufgabenQs = models.Aufgabe.objects.all()
                
        ztlist = []
        statuslist = {}
        aufgaben = dict([(unicodedata.normalize('NFKD', a.aufgabe).encode('ASCII', 'ignore'),
                          (-1, 'x'))
                          for a in aufgabenQs])

        for u in userQs: 
            tmp = {'last_name': u.last_name,
                    'first_name': u.first_name,
                    }
            # print 'user:', u.id 
            tmp.update(aufgaben)
            mQs =  models.Meldung.objects.filter(melder=u)
            if filterForm.cleaned_data['aufgabengruppe'] <> None:
                mQs = mQs.filter(aufgabe__gruppe__gruppe =  filterForm.cleaned_data['aufgabengruppe'])

            # filter out all veto'ed meldungen
            mQs = mQs.exclude (prefMitglied=models.Meldung.GARNICHT)
            
            for m in mQs: 
                tag = unicodedata.normalize('NFKD', m.aufgabe.aufgabe).encode('ASCII', 'ignore')
                tmp[tag] = (0,
                            'box_'+  str(u.id)+"_"+str(m.aufgabe.id),
                            ' ({0} / {1})'.format(m.prefMitglied,
                                                 m.prefVorstand)
                            )
                statuslist[str(u.id)+"_"+str(m.aufgabe.id)]='0'

            zQs =  models.Zuteilung.objects.filter(ausfuehrer=u)
            if filterForm.cleaned_data['aufgabengruppe'] <> None:
                zQs = zQs.filter(aufgabe__gruppe__gruppe =  filterForm.cleaned_data['aufgabengruppe'])
            
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
            
            ztlist.append(tmp)

        ## print ztlist
        ## print statuslist
        zt = ZuteilungsTableFactory(ztlist, aufgabenQs)
        django_tables2.RequestConfig (request, paginate={"per_page": 25}).configure(zt)

        return render (request,
                       'arbeitsplan_manuelleZuteilung.html',
                       {'table': zt,
                        'status': ';'.join([k+'='+v for k, v in statuslist.iteritems()]),
                        'filter': filterForm, 
                        })
    
    def post (self,request, *args, **kwargs):
        # print request.body 
        ## print (request.POST )
        ## print (request.POST.get('status') )
        ## print (request.POST.getlist('box') )

        ## filterForm = self.filterFormClass (request.POST)

        print self.request.get_full_path()
                
        previousStatus = dict([ tuple(s.split('=') )
                   for s in 
                    request.POST.get('status').split(';')
                  ])

        print "prevState:"
        print previousStatus

        ## for item in request.POST.iteritems():
        ##     # containts tuple: name, value
        ##     # print item
        ##     if item[0][:4] == "box_":
        ##         print "item: ", item

        newState = dict([ (item[0][4:], item[1])
                     for item in request.POST.iteritems()
                     if item[0][:4] == "box_"
                    ])

        print "newState"
        print newState

        # find all items in  newState  that have a zero in prevState
        # add that zuteilung
        for k,v in newState.iteritems():
            if previousStatus[k] == '0':
                print "add ", k
                user, aufgabe = k.split('_')
                z = models.Zuteilung(aufgabe = models.Aufgabe.objects.get(id=int(aufgabe)),
                                     ausfuehrer = models.User.objects.get(id=int(user)),
                                     )
                z.save()


        # find all items in prevState with a 1 there that do no appear in newState
        # remove that zuteilung
        for k,v in previousStatus.iteritems():
            if v=='1' and k not in newState:
                print "delete ", k
                user, aufgabe = k.split('_')
                z = models.Zuteilung.objects.get (aufgabe = models.Aufgabe.objects.get(id=int(aufgabe)),
                                                  ausfuehrer = models.User.objects.get(id=int(user)),
                                                 )
                z.delete()

        # TODO: emails senden? 
        return redirect("arbeitsplan-manuellezuteilung")


class ZuteilungUebersichtView (FilteredListView):
    title = "Übersicht der Aufgaben und Zuteilungen"
    tableClassFactory = staticmethod(StundenplanTableFactory)
    tabletitle = "Aufgaben mit benötigten/zugeteilten Personen"
    
    def get_queryset (self):

        # which Aufgaben have a Stundenplan in the first place?
        aufgabenWithStunden = [ x[0]
                                for x in models.Stundenplan.objects.values_list('aufgabe').distinct()
                               ]

        # qs = models.Aufgabe.objects.filter(id__in = aufgabenWithStunden).values('id', 'aufgabe', 'gruppe__gruppe')
        qs = models.Aufgabe.objects.all()


        data = []
        for aufgabe in qs:
            newEntry = defaultdict(int)
            newEntry['id'] = aufgabe.id
            newEntry['aufgabe'] = mark_safe (u'<a href="{1}">{0}</a>'.format(aufgabe.aufgabe,
                                                        reverse('arbeitsplan-aufgabenEdit',
                                                                args=(aufgabe.id,))))

            newEntry['gruppe'] = aufgabe.gruppe.gruppe
            newEntry['gemeldet'] = aufgabe.meldung_set.count()
            newEntry['editlink'] = mark_safe('<a href="{0}">Zuteilung</a>'.format(reverse
                                                                                  ('arbeitsplan-manuellezuteilungAufgabe',
                                                                                  args=(aufgabe.id,), 
                                                                                    )))

            
            if aufgabe.id in aufgabenWithStunden:

                # for s in models.Stundenplan.objects.filter (aufgabe__id=q['id']):
                for s in aufgabe.stundenplan_set.all():
                    # print s
                    newEntry['u'+str(s.uhrzeit)] = {'required': s.anzahl, 'zugeteilt': 0}

                # TODO: Die Schleifen auf aggregate processing umstellen 
                for zs in aufgabe.zuteilung_set.all():
                    print zs
                    for stdzut in zs.stundenzuteilung_set.all():
                        newEntry['u'+str(stdzut.uhrzeit)]['zugeteilt'] += 1


                newEntry['zugeteilt'] = None 
                newEntry['stundenplanlink'] = mark_safe('<a href="{0}">Stundenplan</a>'.format(
                    reverse ('arbeitsplan-stundenplaeneEdit',
                             args=(aufgabe.id,)),
                    ))
            else:
                # normale Aufgaben, kein Stundenplan
                newEntry['required'] = aufgabe.anzahl
                newEntry['zugeteilt'] = aufgabe.zuteilung_set.count()
                newEntry['stundenplanlink'] = None 
                        
            data.append(newEntry)

        # pp( data)
        
        # TODO: allow filtering of those Aufgaben 
        # qs = self.apply_filter(qs)

    
        # for each remaining Aufgabe in qs, find the already assigned STunden 
        
        
        table = self.get_filtered_table(data)

        return table 


class  StundenplaeneEdit (FilteredListView):

    title = "Weisen Sie einer Aufgabe Personen zu den benötigten Zeitpunkten zu"
    tableClassFactory = staticmethod(StundenplanEditFactory)
    tabletilte = "Zuweisung eintragen"
    tableform = {'name': "eintragen",
                 'value': "Stundenzuteilung eintragen/ändern"}

    def get_queryset (self):

        # find out which aufgabe we are talking about?

        # print self.request.GET

        try: 
            aufgabeid = self.kwargs['aufgabeid']
        except:
            messages.error (self.request, "Die angegebene URL bezeichnet keine Aufgabe")
            return None

        aufgabe = get_object_or_404 (models.Aufgabe, pk=aufgabeid)
        
        data = []

        stundenplaene = aufgabe.stundenplan_set.all()

        # print "Stundenplan fuer Auzfgabe: ", stundenplaene

        checkedboxes = []
        for u in models.User.objects.all():
            newEntry = {'last_name': u.last_name,
                        'first_name': u.first_name,
                        }

            try: 
                zuteilung = models.Zuteilung.objects.get(ausfuehrer=u,
                                                         aufgabe=aufgabe)
                stundenzuteilungen =  zuteilung.stundenzuteilung_set.values_list('uhrzeit',
                                                                                 flat=True )
                
                # print "Zuteilung fuer User: ", u, stundenzuteilungen 

                for s in stundenplaene:
                    tag = 'uhrzeit_' + str(u.id) + "_" + str(s.uhrzeit)
                    present = s.uhrzeit in stundenzuteilungen 
                    newEntry['u'+ str(s.uhrzeit)] = (1 if present else 0, tag)
                    if present: 
                        checkedboxes.append(str(u.id) + "_" + str(s.uhrzeit))

                data.append(newEntry)

            except models.Zuteilung.DoesNotExist:  # keine Zuteilung gefunden 
                pass 

        # prepare user id list to be passed into the hidden field, to ease processing later
        self.tableformHidden = [{'name': 'checkedboxes',
                                  'value': ','.join(checkedboxes)}]

        table = self.get_filtered_table (data)

        return table

    def post (self, request, aufgabeid, *args, **kwargs):

        print self.request.POST

        if len(self.request.POST.get('checkedboxes')) > 0:
            tmp = [  x.split('_')
                    for x in
                    self.request.POST.get('checkedboxes').split(',')
                    ]
        else:
            tmp = []

        pp(tmp) 
        checkedboxes = [ (int(x[0]), int(x[1])) for x in tmp ]
        # print checkedboxes

        # any values to delete?
        ## find all zuteilungen that pertain to this aufgabe
        
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
        for uid, uhrzeit  in checkedboxes:
            # print "remove: ", uid, uhrzeit

            zuteilung =  models.Zuteilung.objects.get (ausfuehrer__id = uid,
                                                          aufgabe__id = aufgabeid)

            stundenzuteilung = zuteilung.stundenzuteilung_set.get(uhrzeit=uhrzeit)

            # print stundenzuteilung

            stundenzuteilung.delete()
            
        
        return redirect ("arbeitsplan-stundenplaeneEdit",
                         aufgabeid = aufgabeid, 
                         )
        

    
########################################################################################
#########   LEISTUNG
########################################################################################


        


class CreateLeistungView (CreateView):
    model = models.Leistung
    form_class = forms.CreateLeistungForm 
    template_name = "arbeitsplan_createLeistung.html"

    def form_valid (self, form):
        leistung = form.save (commit=False)
        leistung.melder = self.request.user
        leistung.save()
        return HttpResponseRedirect(self.success_url)

####################################


class ListLeistungView (ListView):
    template_name = "arbeitsplan_listLeistung.html"
    def get_queryset(self):
        res = []
        for s in models.Leistung.STATUS:
            qs = models.Leistung.objects.filter(status=s[0],
                                                melder=self.request.user,
                                                )
            sum = qs.aggregate(Sum('zeit'))
            res.append((s[0], s[1], qs, sum['zeit__sum']))
            
        return res
    
        # return models.Leistung.objects.filter(melder=self.request.user)
    


class LeistungBearbeitenView (isVorstandMixin, View):
    def get(self, request, zustaendig, *args, **kwargs):
        # print zustaendig
        if zustaendig=="me": 
            mainqs = models.Leistung.objects.filter(aufgabe__verantwortlich=request.user)
        else:
            mainqs = models.Leistung.objects.all()

        # and filter further only the open or rueckfragen;
        # for simplicity, we exlude the other ones:
        
        ## mainqs = mainqs.exclude(status=models.Leistung.ACK
        ##                         ).exclude(status=models.Leistung.NEG)
        ## print "view qs: "
        ## print [type(l) for l in mainqs]

        # formLA = forms.LeistungAkzeptierenForm (initial=mainqs[0])
        ## ff = formset_factory (forms.LeistungAkzeptierenForm, extra =0)
        ## formset = ff(initial = [{'wann': l.wann,
        ##                          'zeit': l.zeit,
        ##                          'melder': l.melder,
        ##                          'aufgabe': l.aufgabe,
        ##                          }
        ##                         for l in mainqs])

        table = LeistungBearbeitenTable (mainqs)
        django_tables2.RequestConfig(self.request).configure(table)

        return render (request,
                       "arbeitsplan_leistungbearbeiten.html",
                       dictionary = {
                           # 'formset': formset,
                           'qs': mainqs,
                           'statusvalues': models.Leistung.STATUS,
                           'table': table, 
                           # 'form': formset, 
                           },
                       )
            
    def post (self, request, zustaendig, *args, **kwargs):
        # clean up data by hand here
        print request.POST 
        data = {}
        for k, v in request.POST.iteritems():
            try:
                print k, v 
                if "status" == k[:6]:
                    print "status detected"
                    opt, num, status = k.split('_')
                    print opt, num, status 
                    if not num in data.keys():
                        data[num] = {'status': "",
                                     'bemerkungVorstand': "",
                        }
                    if v=='on':
                        data[num]['status'] = status

                if 'bemerkungVorstand' == k[:17]:
                    tag, num = k.split('_')
                    if not num in data.keys():
                        data[num] = {'status': "",
                                     'bemerkungVorstand': "",
                        }
                    
                    data[num][tag] = v
                    
            except:
                pass 

        print data

        # and now save the updated values in the data
        for k,v in data.iteritems():
            # they should all exist!
            ## print "----------"
            ## print k, v
            ## print type(v['id_bemerkungVorstand'])
            l = models.Leistung.objects.get (id = int(k))
            safeit = False
            if l.bemerkungVorstand <> v['bemerkungVorstand']:
                l.bemerkungVorstand = v['bemerkungVorstand']
                safeit = True
                
            if l.status <> v['status'] and v['status'] <> '':
                l.status = v['status']
                safeit = True
                
                                 ## status = v['id_status'],
                                 ## 
            if safeit:
                l.save()
            # print l

        # TODO: bei Rueckfrage koennte man eine email senden? oder immer?
        
        return redirect ('/arbeitsplan/leistungenBearbeiten/z=all')    


##########################    


class Salden(isVorstandMixin, FilteredListView):

    filterFormClass = forms.NameFilterForm
    title = "Saldenüberblick über geleistete Arbeit"

    tableClassFactory = staticmethod(SaldenTableFactory)
    tabletitle = "Saldenübersicht"

    filtertitle = "Salden nach Vor- oder Nachnamen filtern"
    filterform_class = forms.NameFilterForm
    filterconfig = [('first_name', 'first_name__icontains'),
                    ('last_name', 'last_name__icontains'),
                    ]

    model = models.User

    def annotate_data(self, userQs):
        res = []
        for u in userQs:
            tmp = {}
            tmp['last_name'] = u.last_name
            tmp['first_name'] = u.first_name
            tmp['box'] = ("box-" + str(u.id), True)
            qs = models.Leistung.objects.filter(melder=u)
            for s in models.Leistung.STATUS:
                zeit = qs.filter(status=s[0]
                                 ).aggregate(Sum('zeit'))['zeit__sum']
                tmp[s[0]] = zeit

            res.append(tmp)

        return res



########################################################################################
### EXPERIMENTELL 
########################################################################################
    

class ErstelleZuteilungView (View):
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
        
            
        return redirect ('arbeitsplan-zuteilunglist')

