# -*- coding: utf-8 -*-

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
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
 
import django_tables2

import models, forms
# import networkx as nx 

import unicodedata

from tables import *  # TODO: change import not to polute name space 


#################

def isVorstand (user):
    return user.groups.filter(name='Vorstand')

class isVorstandMixin (object):
    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def dispatch(self, *args, **kwargs):
        return super(isVorstandMixin, self).dispatch(*args, **kwargs)
    
###############

def logout_view (request):
    # print "logout view" 
    logout(request)
    return  render (request, "registration/logged_out.html", {})
###############



class UpdateMeldungView (View):

    def get(self,request, *args, **kwargs):
        myForm = forms.MeldungForm()

        # which questions should get an initial check?
        aufgabenMitMeldung = [m.aufgabe.id for m in 
                                models.Meldung.objects.filter(melder_id=request.user.id)]
        # print aufgabenMitMeldung
        
        return render (request,
                       "arbeitsplan_meldung.html",
                       dictionary = {'form': myForm,
                                     'groups': [ (g.id,
                                                  g.gruppe,
                                                  [(a.id,
                                                    a.aufgabe,
                                                    a.datum if a.datum else "",
                                                    a.id in aufgabenMitMeldung, 
                                                    )
                                                    for a in models.Aufgabe.objects.filter(gruppe__exact=g)],
                                                  )
                                                 for g in models.Aufgabengruppe.objects.all()]},
                       )

    def post (self,request, *args, **kwargs):

        myForm = forms.MeldungForm (request.POST)
        if myForm.is_valid():
            # print "processing valid form"
            # print myForm.cleaned_data

            for k, userInput in myForm.cleaned_data.iteritems():
                aid = int(k.split('a')[1])
                # print aid, userInput

                # try to find a meldung with that aid and for this user
                try: 
                    meldungStatus = models.Meldung.objects.get (aufgabe_id=aid,
                                                                melder_id=request.user.id)
                except:
                    # print "get failed"
                    meldungStatus = False

                # print "mledung status",  meldungStatus
                    
                if userInput:
                    # we have to add or update the corresponding meldung
                    if meldungStatus:
                        # update existing object 
                        newMeld = models.Meldung (aufgabe = models.Aufgabe.objects.get(id=aid),
                                                  erstellt = meldungStatus.erstellt, 
                                                  melder = request.user, 
                                                  id = meldungStatus.id)
                    else:
                        #create a new one:
                        newMeld = models.Meldung (aufgabe = models.Aufgabe.objects.get(id=aid),
                                                  melder = request.user, 
                                                  )
                        
                    # print newMeld
                    newMeld.save()
                else:
                    # user does not work on a particular job;
                    # if meldung exists, delete it

                    if meldungStatus:
                        meldungStatus.delete()
                        
                    
            
            return redirect ('arbeitsplan-meldung')

        # print "processing INvalid form"
        return HttpResponse ("Form was invalid - what to do?")

###############################

class FilteredListView (ListView):
    title = ""
    filterform = None 
    template_name = "arbeitsplan_tff.html"

    def get_context_data (self, **kwargs):
        context= super (FilteredListView, self).get_context_data()
        context['title'] = self.title 
        context['filterform'] = self.filterform

        return context
    
    
        
class ListAufgabenView (FilteredListView):

    filterform_class = forms.AufgabengruppeFilterForm
    title = "Alle Aufgaben anzeigen"
    
    def get_queryset (self):
    
        if isVorstand (self.request.user):
            tableClass = AufgabenTableVorstand
        else:
            tableClass = AufgabenTable
            
            
        # evaluate the form:
        self.filterform = self.filterform_class(self.request.GET)
        if self.filterform.is_valid() and self.filterform.cleaned_data['aufgabengruppe'] <> None:
            table = tableClass(models.Aufgabe.objects.filter(gruppe__gruppe=
                                                                self.filterform.cleaned_data['aufgabengruppe']))
        else:
            table = tableClass(models.Aufgabe.objects.all())
        django_tables2.RequestConfig(self.request).configure(table)

        print table 
        return table

        
    
        
class ListZuteilungenView (FilteredListView):
    title = "Alle Zuteilungen anzeigen"
    filterform_class = forms.PersonAufgabengruppeFilterForm
    
    def get_queryset (self):
        if "all" in  self.request.path: 
            qs = models.Zuteilung.objects.all()
        else:
            qs = models.Zuteilung.objects.filter (ausfuehrer =self.request.user)

        self.filterform = self.filterform_class(self.request.GET)
        if self.filterform.is_valid():
            print self.filterform.cleaned_data
            if self.filterform.cleaned_data['aufgabengruppe'] <> None:
                qs = qs.filter (aufgabe__gruppe__gruppe = self.filterform.cleaned_data['aufgabengruppe'])
            if self.filterform.cleaned_data['first_name'] <> "":
                qs = qs.filter (ausfuehrer__first_name__icontains = self.filterform.cleaned_data['first_name'])
            if self.filterform.cleaned_data['last_name'] <> "":
                qs = qs.filter (ausfuehrer__last_name__icontains = self.filterform.cleaned_data['last_name'])
        

        table = ZuteilungTable(qs)
        # TODO: actually, "me" should be enforced when the user is not a Vorstand!
        
        django_tables2.RequestConfig(self.request).configure(table)
        return table 
        
        
class ListMeldungenView (isVorstandMixin, FilteredListView):

    title = "Alle Meldungen anzeigen"
    filterform_class = forms.PersonAufgabengruppeFilterForm
    
    def get_queryset (self):
        qs = models.Meldung.objects.all()
        self.filterform = self.filterform_class(self.request.GET)
        if self.filterform.is_valid():
            print self.filterform.cleaned_data
            if self.filterform.cleaned_data['aufgabengruppe'] <> None:
                qs = qs.filter (aufgabe__gruppe__gruppe = self.filterform.cleaned_data['aufgabengruppe'])
            if self.filterform.cleaned_data['first_name'] <> "":
                qs = qs.filter (melder__first_name__icontains = self.filterform.cleaned_data['first_name'])
            if self.filterform.cleaned_data['last_name'] <> "":
                qs = qs.filter (melder__last_name__icontains = self.filterform.cleaned_data['last_name'])
            
        table = MeldungTable(qs)
        django_tables2.RequestConfig(self.request).configure(table)
        return table



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



class NameFilterView (View):
    
    def applyFilter (self, request):

        qs = models.User.objects.all()

        form = self.filterFormClass(request.GET)
        if form.is_valid():
            if 'filter' in request.GET:
                last_name = form.cleaned_data['last_name']

                if last_name <> "":
                    qs= qs.filter (last_name__icontains=last_name)
                
                first_name = form.cleaned_data['first_name']
                if first_name <> "":
                    qs= qs.filter (first_name__icontains=first_name)
                
        else:
            print "filter not valid"
            
        return (qs, form)
        
class Salden(isVorstandMixin, NameFilterView):

    filterFormClass = forms.NameFilterForm
    
    def get (self, request, *args, **kwargs):

        userQs, filterForm = self.applyFilter(request)

        res = []
        for u in userQs.order_by('last_name', 'first_name'):
            tmp = {}
            tmp['last_name'] = u.last_name
            tmp['first_name'] = u.first_name
            tmp['box'] = ("box-" + str(u.id), True) 
            qs = models.Leistung.objects.filter(melder=u)
            for s in  models.Leistung.STATUS:
                zeit = qs.filter(status=s[0]
                                ).aggregate(Sum('zeit'))['zeit__sum']
                tmp[s[0]] = zeit

            res.append(tmp)
            
        table = SaldenTableFactory(res)

        django_tables2.RequestConfig (request, paginate={"per_page": 25}).configure(table)

        # for filtering:

        return render (request,
                       "arbeitsplan_salden.html",
                        {'salden': table,
                         'filter': filterForm, 
                        })
    
    def post (self, request, *args, **kwargs):
        print request
        return redirect ("arbeitsplan-salden")
    
    
##########################    

    
    

        
class ManuelleZuteilungView (isVorstandMixin, NameFilterView):
    """Manuelles Eintragen von Zuteilungen
    """

    filterFormClass = forms.PersonAufgabengruppeFilterForm
    
    def get (self,request, *args, **kwargs):
        """Baue eine Tabelle zusammen, die den Zuteilungen aus der DAtenbank
        entspricht."""

        userQs, filterForm = self.applyFilter (request)

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
            for m in mQs: 
                tag = unicodedata.normalize('NFKD', m.aufgabe.aufgabe).encode('ASCII', 'ignore')
                tmp[tag] = (0, 'box_'+  str(u.id)+"_"+str(m.aufgabe.id))
                statuslist[str(u.id)+"_"+str(m.aufgabe.id)]='0'

            zQs =  models.Zuteilung.objects.filter(ausfuehrer=u)
            if filterForm.cleaned_data['aufgabengruppe'] <> None:
                zQs = zQs.filter(aufgabe__gruppe__gruppe =  filterForm.cleaned_data['aufgabengruppe'])
            
            for z in zQs: 
                tag = unicodedata.normalize('NFKD', z.aufgabe.aufgabe).encode('ASCII', 'ignore')
                tmp[tag] = (1, 'box_'+ str(u.id)+"_"+str(z.aufgabe.id))
                statuslist[str(u.id)+"_"+str(z.aufgabe.id)]='1'


                
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
        return redirect ("arbeitsplan-manuellezuteilung")

    
##########################    
    
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
    
                          
class AufgabenUpdate (SuccessMessageMixin, UpdateView):
    model = models.Aufgabe
    form_class = forms.AufgabeForm
    template_name = "arbeitsplan_aufgabenCreate.html"
    # success_url = "home.html"
    success_url = reverse_lazy("arbeitsplan-aufgaben")
    success_message = 'Die  <a href="%(url)s">Aufgabe %(id)s</a> wurde erfolgreich verändert.'
    title = "Aufgabe ändern"
    buttontext = "Änderung eintragen"

    def get_success_message (self, cleaned_data):
        """See documentation at: https://docs.djangoproject.com/en/1.6/ref/contrib/messages/
        """
        msg =  mark_safe(self.success_message % dict (cleaned_data,
                                                      url = reverse ('arbeitsplan-aufgabenEdit',
                                                                     args=(self.object.id,)), 
                                                      id=self.object.id))

        # messages.warning(self.request, "aber komisch ist die schon")
        
        # print "succesS_msg: ", msg
        return msg
    
    
    def get_context_data (self, **kwargs):
        context = super (AufgabenUpdate, self).get_context_data (**kwargs)
        context['title'] = self.title
        context['buttontext'] = self.buttontext

        # hier Stundenplanwerte aus DB holen
        # a dict with default values, to be overwirtten with values from data base
        # then converted back into a list to be passed into the template
        stundenplan = dict([(u, 0) for u in range(8,24)])
        for s in models.Stundenplan.objects.filter (aufgabe=self.object):
            stundenplan[s.uhrzeit] = s.anzahl
        
        context['stundenplan'] = stundenplan.items()
        
        return context 
        
    
    def get_form_kwargs (self):
        kwargs = super(AufgabenUpdate, self).get_form_kwargs()
        kwargs.update({
            'request' : self.request
            })
        return kwargs

    def form_valid (self, form):

        # store the aufgabe
        super (AufgabenUpdate, self).form_valid(form)

        # manipulate the stundenplan
        stundenplan = form.cleaned_data['stundenplan']
        for sDB in models.Stundenplan.objects.filter(aufgabe=self.object):
            print sDB
            if sDB.uhrzeit in stundenplan:
                if stundenplan[sDB.uhrzeit] <> sDB.anzahl:
                    sDB.anzahl = stundenplan[sDB.uhrzeit]
                    sDB.save()
                    del stundenplan[sDB.uhrzeit]
            else:
                sDB.delete()

        # all the keys remaining in stundenplan have to be added
        for uhrzeit, anzahl in stundenplan.iteritems():
            sobj = models.Stundenplan (aufgabe = self.object,
                                       uhrzeit = uhrzeit,
                                       anzahl = anzahl)
            sobj.save()


        return redirect ("arbeitsplan-aufgaben")
        ## return render (self.request,
        ##                self.get_success_url(),
        ##                ## {'msg': format_html(u'Die Aufgabe <a href="{1}">{0}</a> wurde erfolgreich verändert.',
        ##                ##                     self.object.id,
        ##                ##                     reverse ('arbeitsplan-aufgabenEdit',
        ##                ##                              args=(self.object.id,),
        ##                ##                              )
        ##                ##                     ),
        ##                ##  'msgclass': 'success'}
        ##                 )
