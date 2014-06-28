# -*- coding: utf-8 -*-

from django import forms
import models
from django.forms.models import inlineformset_factory
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Button, Field, Div, HTML
from crispy_forms.bootstrap import StrictButton, FormActions, InlineCheckboxes, InlineField


class CrispyFormMixin(object):
    """Define basic crispy fields
    """

    def __init__(self, *args, **kwargs):
        """
        Add the necessary attributes for crispy to work,
        after the superclass constructur has done its work. 
        Arguments:
        - `*args`:
        - `**kwargs`:
        """

        print "crispy form mixin init" 
        super(CrispyFormMixin, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"
        # self.helper.field_template = "bootstrap3/layout/inline_field.html"



##############################
## General input forms
##############################

class CreateLeistungForm (CrispyFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CreateLeistungForm, self).__init__(*args, **kwargs)

        self.helper.layout = Layout(
            'aufgabe',
            Field('wann', css_class = "datepicker"),
            'zeit',
            ## 'auslagen',
            ## 'km',
            'bemerkung',
            )

        self.helper.add_input (Submit ('apply', 'Eintragen'))
        print self.helper.layout

    class Meta:
        model = models.Leistung
        exclude = ('melder',
                   'erstellt',
                   'veraendert',
                   'status',
                   'bemerkungVorstand',
                   'benachrichtigt',
                   )


class AufgabengruppeForm(CrispyFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AufgabengruppeForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
        
    class Meta:
        model = models.Aufgabengruppe

class AufgabeForm (forms.ModelForm):
    class Meta:
        model = models.Aufgabe

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(AufgabeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_errors = True
        self.helper.form_error_title = "Allgemeine Fehler"

        self.helper.layout = Layout(
            'aufgabe',
            'verantwortlich',
            'gruppe',
            'anzahl',
            'stunden',
            'teamleader',
            Field('datum', css_class="datepicker"),
            'bemerkung',
            )

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

        # das kann schon sinnvoll sein: 5 h pro Person...
        # und im Stundenplan dann verteilt
        ## if (len(stundenplan) > 0) and (cleaned_data['anzahl'] > 0):
        ##     raise ValidationError ("Entweder Stundenplan oder Anzahl Personen angeben, nicht beides!",
        ##                            code="illogic")

        cleaned_data['stundenplan'] = stundenplan
        return cleaned_data


class EmailAddendumForm (forms.Form):
    ergaenzung = forms.CharField(required=False,
                                 label="Ergänzender Text",
                                 )

    def __init__ (self, *args, **kwargs):
        super(EmailAddendumForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


##################################
## Filter forms
#################################



class CrispyFilterMixin(CrispyFormMixin):
    """A specific Form mixin, specialiced for filters (common case).

    It tries to be smart in constructing the layout object. It looks at the
    __layout attributes of all the current class and all the mixins, up to this
    base class. In that order, it patches together the layout object itself.
    """

    def get_mixin_names(self):
        """
        Get all the mixins standing between the current class and
        this base class, in mro order.
        We need the names later on, not the class object.
        """
        mixins = []
        for m in self.__class__.mro():
            if m == CrispyFilterMixin:
                break
            mixins.append(m.__name__)
        return mixins

    def get_mixin_attributes(self, attr):
        """Assuming that the current class has several mixings
        which all define a call attribute, get the values
        of these attributes as a list, in mro.
        """

        mixins = self.get_mixin_names()
        res = []
        for m in mixins:
            try:
                tmp = self.__getattribute__('_' + m + '__' + attr)
                res.append(tmp)
            except AttributeError:
                pass

        # print "get_mixin:", res
        return res

    def __init__(self, *args, **kwargs):
        """
        Set the form help fields to the specific filtering case
        """
        super(CrispyFilterMixin, self).__init__(*args, **kwargs)

        self.helper.form_method = "get"
        self.helper.form_action = ""

        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"

        # get all the __layout attributes from the derived classes,
        # in mro order. Then, patch taht together into the self.helper.layout,
        # adding the filter anwendern always as the last
        layoutattributes = self.get_mixin_attributes('layout')

        self.helper.layout = Layout()
        for l in layoutattributes:
            self.helper.layout = Layout (self.helper.layout,
                                         l)

        self.helper.layout = Layout (self.helper.layout,
                                     HTML("<p>"),
                                     FormActions(
                                        Submit ('filter', 'Filter anwenden'),
                                        ),
                                     )

        # disabluing test, this seems to work 
        # self.fields['first_name'].widget.attrs['disabled'] = True

##################################


class NameFilterForm (CrispyFilterMixin, forms.Form):
    last_name = forms.CharField (
        label = "Nachname",
        max_length = 20,
        required = False,
        )

    first_name = forms.CharField (
        label = "Vorname",
        max_length = 20,
        required = False,
        )

    __layout = Layout(
        'last_name',
        'first_name',
        )


class AufgabengruppeFilterForm (CrispyFilterMixin, forms.Form):

    aufgabengruppe = forms.ModelChoiceField (queryset = models.Aufgabengruppe.objects.all(),
                                            label="Aufgabengruppe", 
                                            required=False)

    __layout = Layout (
        'aufgabengruppe',
        )
 
class PersonAufgabengruppeFilterForm (NameFilterForm,
                                      AufgabengruppeFilterForm,
                                      forms.Form):
    pass


class PraeferenzFilterForm (CrispyFilterMixin, forms.Form):

    praeferenz = forms.MultipleChoiceField(choices=models.Meldung.PRAEFERENZ,
                                           widget=forms.CheckboxSelectMultiple,
                                           label="Vorliebe Mitglied",
                                           required=False,
                                           initial=[models.Meldung.PRAEFERENZ[1][0],
                                                    models.Meldung.PRAEFERENZ[2][0],
                                                    models.Meldung.PRAEFERENZ[3][0],
                                                    ],
                                             )
    __layout = Layout(
        InlineCheckboxes('praeferenz'),
        )

class PersonAufgGrpPraefernzFilterForm (NameFilterForm,
                                        AufgabengruppeFilterForm,
                                        PraeferenzFilterForm,
                                        forms.Form):
    pass


class DateFilterForm (CrispyFilterMixin, forms.Form):
    von = forms.DateField (label="Von",
                           required=False)
    bis = forms.DateField (label="Bis",
                           required=False)
    __layout = Layout(
        InlineField ('von', css_class="datepicker",), 
        InlineField ('bis', css_class="datepicker",), 
        )


class StatusFilterForm (CrispyFilterMixin, forms.Form):
    status = forms.MultipleChoiceField(choices=models.Leistung.STATUS,
                                           widget=forms.CheckboxSelectMultiple,
                                           label="Bearbeitungsstatus",
                                           required=False,
                                           initial=[models.Leistung.STATUS[0][0],
                                                    models.Leistung.STATUS[2][0],
                                                    ],
                                             )
    __layout = Layout(
        InlineCheckboxes('status'),
        )

class StatusFilterForm2 (CrispyFilterMixin, forms.Form):
    status = forms.MultipleChoiceField(choices=models.Leistung.STATUS,
                                           widget=forms.CheckboxSelectMultiple,
                                           label="Bearbeitungsstatus",
                                           required=False,
                                           initial=[models.Leistung.STATUS[1][0],
                                                    models.Leistung.STATUS[2][0],
                                                    models.Leistung.STATUS[3][0],
                                                    ],
                                             )
    __layout = Layout(
        InlineCheckboxes('status'),
        )

class LeistungBenachrichtigtForm(CrispyFilterMixin, forms.Form):
    benachrichtigt = forms.BooleanField(required=False,
                                        initial=False,
                                        label="Auch schon benachrichtigte Leistungen anzeigen",
                                     )

    __layout = Layout(
        'benachrichtigt',
        )


class ZuteilungBenachrichtigungForm(CrispyFilterMixin, forms.Form):
    benachrichtigt = forms.BooleanField(required=False,
                                        initial=False,
                                        label="Auch schon benachrichtige"
                                        " Mitglieder anzeigen?",
                                        )

    __layout = Layout(
        'benachrichtigt'
        )


class MitgliedAusgelastetForm(CrispyFilterMixin, forms.Form):
    """
    Is the Mitglied already assigned sufficient amount of work?
    """

    mitglied_ausgelastet = forms.ChoiceField(required=False,
                                             label="Mitglied ausgelastet?",
                                             choices=(
                                                 ('--', '------'),
                                                 ('FR', 'Freie anzeigen'),
                                                 ('BU',
                                                  'Ausgelastete anzeigen'),
                                                 ),
                                             )
    __layout = Layout(
        'mitglied_ausgelastet'
        )


class ZuteilungStatusForm(CrispyFilterMixin, forms.Form):
    """Possible status:
    - aufgabe has not enough zuteilungen
    - aufgabe has not even enough meldungen
    ??
    """

    zuteilungen_ausreichend = forms.ChoiceField(required=False,
                                                label="Zuteilugnen ausreichend?",
                                                choices = (
                                                     ('--', 'Alle anzeigen'),
                                                     ('UN', 'Aufgaben mit unzureichenden Zuteilungen'),
                                                     ('ZU', 'Aufgaben mit zureichenden Zuteilungen'),
                                                     ),
                                                 )

    stundenplan = forms.BooleanField(required=False,
                                     initial=False,
                                     label="Stundenplan anzeigen?")

    __layout = Layout(
        'zuteilungen_ausreichend',
        'stundenplan',
        )


class SaldenStatusForm(CrispyFilterMixin, forms.Form):
    saldenstatus = forms.ChoiceField(required=False,
                                     initial=False,
                                     label="Saldenstatus",
                                     choices=(('--', 'Kein Statusfilter'),
                                              ('OK', 'Pensum erfüllt'),
                                              ('CH', 'Chancen zu erfüllen'),
                                              ('PR', 'Pensum kann nicht erfüllt werden'),
                                              ))
    __layout = Layout(
        'saldenstatus'
        )


# Stich Forms together into Filters 

class AufgabenDatumFilter(AufgabengruppeFilterForm,
                          DateFilterForm,
                          forms.Form):
    pass 


class LeistungFilter(NameFilterForm,
                     AufgabengruppeFilterForm,
                     DateFilterForm,
                     StatusFilterForm,
                     forms.Form): 
    pass


class LeistungEmailFilter(AufgabengruppeFilterForm,
                          StatusFilterForm2,
                          LeistungBenachrichtigtForm):
    pass


class ZuteilungManuellFilter(AufgabengruppeFilterForm,
                             ZuteilungStatusForm,
                             forms.Form,
                             ):
    pass


class ZuteilungMitglied(PersonAufgabengruppeFilterForm,
                        MitgliedAusgelastetForm,
                        forms.Form):
    pass


class ZuteilungEmailFilter(NameFilterForm,
                           ZuteilungBenachrichtigungForm,
                           ):
    pass


class SaldenFilter(NameFilterForm,
                   SaldenStatusForm,
                   forms.Form):
    pass

