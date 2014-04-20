# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic import View, ListView, CreateView, FormView
from django.contrib.auth.models import User 
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.contrib.auth import logout
from django.forms.models import modelformset_factory

import models, forms
# import networkx as nx 


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
    return  render (request, "home.html", {})
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

class ListAufgabenView (ListView):

    model = models.Aufgabe
    template_name = "arbeitsplan_aufgabenlist.html"

class ListZuteilungenView (ListView):

    model = models.Zuteilung
    template_name = "arbeitsplan_zuteilunglist.html" 

class ListMeldungenView (isVorstandMixin, ListView):

    model = models.Meldung
    template_name = "arbeitsplan_meldunglist.html" 


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
        
        mainqs = mainqs.exclude(status=models.Leistung.ACK
                                ).exclude(status=models.Leistung.NEG)
        print "view qs: "
        print [l.id for l in mainqs]
        return render (request,
                       "arbeitsplan_leistungbearbeiten.html",
                       dictionary = {
                           # 'formset': formset,
                           'qs': mainqs,
                           'statusvalues': models.Leistung.STATUS, 
                           },
                       )
            
    def post (self, request, zustaendig, *args, **kwargs):
        # clean up data by hand here
        print request.POST 
        data = {}
        for k, v in request.POST.iteritems():
            try: 
                tag, num = k.split('-')
                if (tag == 'id_status' or tag=='id_bemerkungVorstand'):
                    if not num in data.keys():
                        data[num] = {'id_status': "",
                                     'id_bemerkungVorstand': "",
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
            l.bemerkungVorstand = v['id_bemerkungVorstand']
            l.status = v['id_status']
                                 ## status = v['id_status'],
                                 ## 
                                 
            l.save()
            print l

        # TODO: bei Rueckfrage koennte man eine email senden? oder immer?
        
        return redirect ('/arbeitsplan/leistungenBearbeiten/z=all')    
##########################    


class Salden(isVorstandMixin, ListView):
    template_name = "arbeitsplan_salden.html"
    def get_queryset (self):
        res = [ {'user': u,
                 'leistungen': [models.Leistung.objects.filter(melder=u
                                                ).filter(status=s[0]
                                                ).aggregate(Sum('zeit'))['zeit__sum']
                                for s in models.Leistung.STATUS]
                 } 
            for u in models.User.objects.all().order_by('last_name', 'first_name')]
        # print (res, models.Leistung.STATUS)
        return {'salden': res,
                'status': models.Leistung.STATUS, 
                }
    
##########################    
    
class ErstelleZuteilungView (View):

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

