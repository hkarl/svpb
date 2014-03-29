# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View, ListView
from django.contrib.auth.models import User 

import models, forms


class UpdateMeldungView (View):

    def get(self,request, *args, **kwargs):
        print "meldung get"
        myForm = forms.MeldungForm()

        # which questions should get an initial check?
        aufgabenMitMeldung = [m.aufgabe.id for m in 
                                models.Meldung.objects.filter(melder_id=request.user.id)]
        print aufgabenMitMeldung
        
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
        print "meldung post"
        myForm = forms.MeldungForm (request.POST)
        if myForm.is_valid():
            print "processing valid form"
            print myForm.cleaned_data

            for k, userInput in myForm.cleaned_data.iteritems():
                aid = int(k.split('a')[1])
                print aid, userInput

                # try to find a meldung with that aid and for this user
                try: 
                    meldungStatus = models.Meldung.objects.get (aufgabe_id=aid,
                                                                melder_id=request.user.id)
                except:
                    print "get failed"
                    meldungStatus = False

                print "mledung status",  meldungStatus
                    
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
                        
                    print newMeld
                    newMeld.save()
                else:
                    # user does not work on a particular job;
                    # if meldung exists, delete it

                    if meldungStatus:
                        meldungStatus.delete()
                        
                    
            
            return redirect ('arbeitsplan-meldung')

        print "processing INvalid form"
        return HttpResponse ("Form was invalid - what to do?")

class ListAufgabenView (ListView):

    model = models.Aufgabe
    template_name = "arbeitsplan_aufgabenlist.html"
    
