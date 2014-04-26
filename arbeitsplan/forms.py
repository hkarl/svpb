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

                

class CreateLeistungForm (forms.ModelForm):
    class Meta:
        model = models.Leistung
        exclude = ('melder',
                   'erstellt',
                   'veraendert',
                   'status',
                   'bemerkungVorstand',
                   )
            
##################################

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout

class NameFilterForm (forms.Form):

    last_name = forms.CharField (
        label="Nachname",
        max_length=20,
        required =False,
        )
    
    first_name = forms.CharField (
        label="Vorname",
        max_length=20,
        required =False,
        )

    ## failed attempts to use crispy-forms: 
    ## def __init__(self, *args, **kwargs):
    ##     super(NameFilterForm, self).__init__(*args, **kwargs)
    ##     self.helper = FormHelper()
    ##     self.helper.form_id = "namefilterForm"
    ##     self.helper.form_method = "get"
    ##     self.helper.form_action = "filter_name"

    ##     self.helper.add_input (Submit('filter', 'Filter anwenden'))
        
    ##     self.helper.form_class = "form-horizontal"
    ##     self.helper.label_class = "col-lg-2"
    ##     self.helper.field_class = "col-lg-8"
    ##     self.helper.layout = Layout(
    ##         'last_name',
    ##         'first_name',
    ##         )
        

class ArbeitsgruppenFilterForm (NameFilterForm):

    aufgabengruppe = forms.ModelChoiceField (queryset = models.Aufgabengruppe.objects.all(),
                                            label="Aufgabengruppe", 
                                            required=False) 

    
## class LeistungBearbeitenForm (forms.ModelForm):
##     ## def __init__ (self, qs, *args, **kwargs):
##     ##     print "form init: ", qs, args, kwargs
##     ##     super (LeistungBearbeitenForm, self).__init__ (*args, **kwargs)

##     ##     for l in qs:
##     ##         self.fields[str(l.id)] = forms.ChoiceField (label=l.__unicode__(),
##     ##                                                     choices = models.Leistung.STATUS,
##     ##                                                     widget=forms.RadioSelect,         
##     ##                                                     required=False)

##     class Meta:
##         model = models.Leistung
##         fields = (
##             ## 'melder',
##             ##       'aufgabe',
##             ##       'wann',
##             ##       'zeit',
##             ##       'auslagen', 
##                    'bemerkungVorstand',
##                    'status',
##                    )
        
