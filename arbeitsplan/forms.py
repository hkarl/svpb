from django import forms
import models

class MeldungForm (forms.Form):

    def __init__ (self, *args, **kwargs):

        super (MeldungForm, self).__init__ (*args, **kwargs)

        # iter over aufgaben, construct a field for each
        ## for a in models.Aufgabe.objects.all():
        ##     print a.aufgabe, a.id, a.gruppe, a.gruppe.id
        ##     self.fields[str(a.gruppe.id) + "_" + str(a.id)]  = forms.BooleanField (label=a.aufgabe,
        ##                                                                            required=False)
            

        for g in models.Aufgabengruppe.objects.all():
            # print "Gruppe",  g.gruppe
            for a in models.Aufgabe.objects.filter(gruppe__exact=g):
                # print "Aufgabe", a.aufgabe
                self.fields["g"+ str(g.id) + "_a" + str(a.id)] = forms.BooleanField (label=a.aufgabe,
                                                                                     required=False,
                                                                                     )
                
