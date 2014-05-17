from django import forms
import models
from django.forms.models import inlineformset_factory
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Button
from crispy_forms.bootstrap import StrictButton, FormActions, InlineCheckboxes



class CreateLeistungForm (forms.ModelForm):

    def __init__ (self, *args, **kwargs):
        super(CreateLeistungForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = ""
        self.helper.form_method = "post"
        self.helper.add_input (Submit ('apply', 'Eintragen'))

    class Meta:
        model = models.Leistung
        exclude = ('melder',
                   'erstellt',
                   'veraendert',
                   'status',
                   'bemerkungVorstand',
                   )
            
##################################



class NameFilterForm (forms.Form):
    last_name = forms.CharField (
        label="Nachname",
        max_length=20,
        required =False,
        )

    # disabledWidget = forms.TextInput(attrs={'readonly': True})    
    first_name = forms.CharField (
        label = "Vorname",
        max_length = 20,
        required = False,
        # widget=disabledWidget,
        )

    def __init__(self, *args, **kwargs):
        super(NameFilterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "namefilterForm"
        self.helper.form_method = "get"
        self.helper.form_action = ""

        # self.helper.add_input (Submit('filter', 'Filter anwenden'))

        self.helper.form_class = "form-inline"
        ## self.helper.label_class = "col-lg-2"
        ## self.helper.field_class = "col-lg-8"
        # self.helper.help_text_inline = True
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.layout = Layout(
            'last_name',
            'first_name',
            Submit ('filter', 'Filter anwenden'),
            )

        # disabluing test, this seems to work 
        # self.fields['first_name'].widget.attrs['disabled'] = True

class AufgabengruppeFilterForm (forms.Form):

    def __init__(self, *args, **kwargs):
        super(AufgabengruppeFilterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "aufgabengruppefilterForm"
        self.helper.form_method = "get"
        self.helper.form_action = ""

        # self.helper.add_input (Submit('filter', 'Filter anwenden'))
        
        self.helper.form_class = "form-inline"
        ## self.helper.label_class = "col-lg-2"
        ## self.helper.field_class = "col-lg-8"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"

        self.helper.layout = Layout(
            'aufgabengruppe',
            Submit ('filter', 'Filter anwenden'),
            )
        
    aufgabengruppe = forms.ModelChoiceField (queryset = models.Aufgabengruppe.objects.all(),
                                            label="Aufgabengruppe", 
                                            required=False) 
 
class PersonAufgabengruppeFilterForm (NameFilterForm):

    def __init__(self, *args, **kwargs):
        super(PersonAufgabengruppeFilterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "aufgabengruppefilterForm"
        self.helper.form_method = "get"
        self.helper.form_action = ""

        # self.helper.add_input (Submit('filter', 'Filter anwenden'))
        
        self.helper.form_class = "form-inline"
        ## self.helper.label_class = "col-lg-2"
        ## self.helper.field_class = "col-lg-8"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"

        self.helper.layout = Layout(
            'last_name',
            'first_name',
            'aufgabengruppe',
            Submit ('filter', 'Filter anwenden'),
            )
        
    aufgabengruppe = forms.ModelChoiceField (queryset = models.Aufgabengruppe.objects.all(),
                                            label="Aufgabengruppe", 
                                            required=False) 

class PersonAufgGrpPraefernzFilterForm (PersonAufgabengruppeFilterForm):
    def __init__(self, *args, **kwargs):
        super(PersonAufgGrpPraefernzFilterForm, self).__init__(*args, **kwargs)
        self.helper.form_id = "PersonAufgGrpPraefernzFilterForm"

        
        self.helper.layout = Layout(
            'last_name',
            'first_name',
            'aufgabengruppe',
            InlineCheckboxes('praeferenz'), 
            Submit ('filter', 'Filter anwenden'),
            )

    praeferenz = forms.MultipleChoiceField(choices=models.Meldung.PRAEFERENZ,
                                           widget=forms.CheckboxSelectMultiple,
                                           label="Praeferenz Mitglied",
                                           required =False,
                                           initial=[models.Meldung.PRAEFERENZ[1][0],
                                                    models.Meldung.PRAEFERENZ[2][0],
                                                    models.Meldung.PRAEFERENZ[3][0],
                                                    ],
                                             )


class AufgabeForm (forms.ModelForm):
    class Meta:
        model = models.Aufgabe

    def __init__ (self, request, *args, **kwargs):
        self.request = request 
        super(AufgabeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors =  True
        self.helper.form_error_title = "Allgemeine Fehler" 

    def clean (self):
        ## print "in form clean"
        ## print self.request 

        cleaned_data = super(AufgabeForm, self).clean()

        stundenplan = {}
        for k,v in self.request.POST.iteritems():
            if 'uhrzeit' == k[:7] and v <> '0':
                try:
                    v = int(v)
                except:
                    v = 0 
                if v <0:
                    raise ValidationError ("Keine negativen Personen im Stundenplan",
                                           code="negativNumber") 
                    
                uhrzeit = int(k.split('_')[1])
                stundenplan[uhrzeit] =  v

        print stundenplan
        print cleaned_data['datum'] 
        if (len(stundenplan) > 0) and (cleaned_data['datum'] == None):
            raise ValidationError ("Angaben im Stundenplan erfordern ein Datum.",
                                   code ="illogic") 

        # das kann schon sinnvoll sein: 5 h pro Person... und im Stundenplan dann verteilt 
        ## if (len(stundenplan) > 0) and (cleaned_data['anzahl'] > 0):
        ##     raise ValidationError ("Entweder Stundenplan oder Anzahl Personen angeben, nicht beides!",
        ##                            code="illogic")
        
        cleaned_data['stundenplan'] = stundenplan 
        return cleaned_data 
