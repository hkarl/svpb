# -*- coding: utf-8 -*-

from django import forms
import models
from django.forms.models import inlineformset_factory
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Button, Field, Div, HTML
from crispy_forms.bootstrap import StrictButton, FormActions, InlineCheckboxes, InlineField

import django_select2

class PasswordChange(forms.Form):

    pw1 = forms.CharField(max_length=30,
                          required=True,
                          label="Neues Passwort",
                          widget=forms.PasswordInput(),
                          )

    pw2 = forms.CharField(max_length=30,
                          required=True,
                          label="Neues Passwort (Wiederholung)",
                          widget=forms.PasswordInput(),
                          )

    def __init__(self, *args, **kwargs):
        super(PasswordChange, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            'pw1',
            'pw2',
            HTML("<p>"),
            )
        self.helper.add_input(Submit('apply', 'Neues Passwort setzen'))

    def clean(self):
        if self.cleaned_data['pw1'] != self.cleaned_data['pw2']:
            raise ValidationError(u'Die beiden Passwörter stimmen nicht überein',
                            code='invalid'
                            )
        else:
            return self.cleaned_data


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

        # print "crispy form mixin init"
        super(CrispyFormMixin, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"
        # self.helper.field_template = "bootstrap3/layout/inline_field.html"

##############################
## General input forms
##############################


class CreateLeistungForm(CrispyFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CreateLeistungForm, self).__init__(*args, **kwargs)

        self.helper.layout = Layout(
            'aufgabe',
            Field('wann', css_class="datepicker"),
            'zeit',
            # 'auslagen',
            # 'km',
            'bemerkung',
            )

        self.helper.add_input(Submit ('apply', 'Eintragen'))
        # print self.helper.layout

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
        fields = ('gruppe',
                  'verantwortlich',
                  'bemerkung',
                  )

class Select2UserField(django_select2.fields.AutoModelSelect2MultipleField):
    queryset = User.objects
    search_fields = ['username__icontains', ]

    ## def get_model_field_values(self, value):
    ##     print "get_model_field_vlaues"
    ##     print self
    ##     print value
    ##     return {'username': value}

class AufgabeForm(forms.ModelForm):

    schnellzuweisung = django_select2.fields.ModelSelect2MultipleField(
    # schnellzuweisung = Select2UserField(
        queryset=User.objects.all(),
        label="Direkt ausführendes Mitglied auswählen",
        help_text="Direktes Zuteilen eines Mitglieds zu dieser Aufgabe; Melden und Zuteilen dann nicht mehr nötig. ACHTUNG: Löschen ist hier NICHT möglich!",
        required=False)

    class Meta:
        model = models.Aufgabe
        fields = (
            'aufgabe',
            'verantwortlich',
            'gruppe',
            'anzahl',
            'stunden',
            'teamleader',
            'datum',
            'bemerkung',
            )
        widgets = {
            'verantwortlich': django_select2.Select2Widget,
            'teamleader': django_select2.Select2Widget,
            }

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
            'schnellzuweisung',
            )

    def clean(self):

        cleaned_data = super(AufgabeForm, self).clean()

        stundenplan = {}
        for k, v in self.request.POST.iteritems():
            if 'uhrzeit' == k[:7] and v != '0':
                try:
                    v = int(v)
                except:
                    v = 0
                if v < 0:
                    raise ValidationError("Keine negativen Personen im Stundenplan",
                                          code="negativNumber")

                uhrzeit = int(k.split('_')[1])
                stundenplan[uhrzeit] = v

        cleaned_data['stundenplan'] = stundenplan

        # print stundenplan

        if (len(stundenplan) > 0) and (cleaned_data['datum'] is None):
            raise ValidationError("Angaben im Stundenplan erfordern ein Datum.",
                                  code ="illogic") 

        # das kann schon sinnvoll sein: 5 h pro Person...
        # und im Stundenplan dann verteilt
        ## if (len(stundenplan) > 0) and (cleaned_data['anzahl'] > 0):
        ##     raise ValidationError ("Entweder Stundenplan oder Anzahl Personen angeben, nicht beides!",
        ##                            code="illogic")

        return cleaned_data


class EmailAddendumForm (forms.Form):
    ergaenzung = forms.CharField(required=False,
                                 label="Ergänzender Text",
                                 )

    def __init__(self, *args, **kwargs):
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
            self.helper.layout = Layout(self.helper.layout,
                                        l)

        self.helper.layout = Layout(self.helper.layout,
                                    HTML("<p>"),
                                    FormActions(
                                        Submit('filter', 'Filter anwenden'),
                                        ),
                                    )

        # disabluing test, this seems to work
        # self.fields['first_name'].widget.attrs['disabled'] = True

##################################


class NameFilterForm (CrispyFilterMixin, forms.Form):
    last_name = forms.CharField(
        label="Nachname",
        max_length=20,
        required=False,
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
                                                 ('--', 'Alle Mitglieder'),
                                                 ('AM', 'Mitglieder mit Meldung für Aufgabe/Aufgabengruppe'),
                                                 ('FR', 'Nur freie Mitglieder'),
                                                 ('FRAM', 'Nur freie Mitglieder, mit Meldung für Aufgabe/Aufgabengruppe'),
                                                 ('BU',
                                                  'Nur ausgelastete Mitglieder'),
                                                 ('BUAM',
                                                  'Nur ausgelastete Mitglieder, mit Meldung für Aufgabe/Aufgabengruppe'),
                                                 ),
                                             )

    aktive_aufgaben = forms.BooleanField(required=False,
                                         label="Vergangene Aufgaben ausblenden?",
                                         initial=False,
                                         )
    __layout = Layout(
        'mitglied_ausgelastet',
        'aktive_aufgaben',
        )

    def __init__(self, *args, **kwargs):
        "Let's make sure that AM is the default field value"

        super(MitgliedAusgelastetForm, self).__init__(*args, **kwargs)

        # this works, but does not apply the filter setting :-(
        # besides, it makes zero sense to use this as a default, since
        # intially, there is typically no Aufgabengruppe selected.
        # no obvious way to make this work 
        # self.initial['mitglied_ausgelastet'] = 'AM'


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


class GemeldeteAufgabenFilterForm(CrispyFilterMixin, forms.Form):
    gemeldet = forms.ChoiceField(required=False,
                                 initial=False,
                                 label="Gemeldet",
                                 choices=(
                                     ('--', 'Alle Aufgaben'),
                                     ('GA', 'Nur Aufgaben, für die ich gemeldet habe'),
                                     ('NG', 'Nur Aufgaben, für die ich NICHT gemeldet habe'),
                                     ),
                                 )
    __layout = Layout(
        'gemeldet',
        )


###################################
# Stich Forms together into Filters


class AufgabenDatumFilter(AufgabengruppeFilterForm,
                          DateFilterForm,
                          forms.Form):
    pass


class GemeldeteFilter(
        AufgabengruppeFilterForm,
        GemeldeteAufgabenFilterForm,
        DateFilterForm,
        forms.Form,
        ):
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

