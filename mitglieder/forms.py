# -*- coding: utf-8 -*-


"""Forms related to handling Mitglieder data
"""

# generic imports from django:
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, HTML


# specfic imports:
from phonenumber_field.formfields import PhoneNumberField

from arbeitsplan import models
from arbeitsplan.forms import NameFilterForm, MitgliedsnummerFilterForm


class ActivateForm(forms.Form):
    email = forms.EmailField(required=True,
                             help_text="Bitte bestätigen Sie Ihre email-Adreese.")
    portal = forms.BooleanField(required=True,
                                initial=False,
                                label="Nutzung der Webseite",
                                help_text="Stimmen Sie der Nutzung dieser Webseite zu?")
    emailNutzung = forms.BooleanField(required=True,
                                      initial=False,
                                      label="Email-Benachrichtigungen",
                                      help_text="Erlauben Sie dem SVPB, Sie per email zu diesem Arbeitsplan zu benachrichtigen?")
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

        # print "creating an Activate Form"

        self.helper = FormHelper()
        super(ActivateForm, self).__init__(*args, **kwargs)
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"

        self.helper.layout = Layout('email', 'portal', 'emailNutzung',
                                    HTML("<p>"),
                                    'pw1', 'pw2', HTML("<p>"),
                                    )
        self.helper.add_input(Submit('apply', 'Aktivieren'))


    def clean(self):
        try:
            pw1 = self.cleaned_data['pw1']
            pw2 = self.cleaned_data['pw2']
        except:
            raise ValidationError('Beide Passwörter müssen angegeben werden')

        if pw1 != pw2:
            raise ValidationError('Die beiden Passwörter müssen übereinstimmen')

        return self.cleaned_data


class MitgliederAddForm(forms.ModelForm):

    firstname = forms.CharField(max_length=20,
                                label="Vorname",)
    lastname = forms.CharField(max_length=20,
                                label="Nachname",)
    email = forms.EmailField(label="email")

    def __init__(self, *args, **kwargs):
        super(MitgliederAddForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout('firstname', 'lastname',
                                    HTML("<p>"),
                                    'email',
                                    HTML("<p>"),
                                    'mitgliedsnummer',

                                    HTML("<p>"),
                                    'geburtsdatum',
                                    'gender',
                                    'strasse', 'plz', 'ort',
                                    HTML("<p>"),
                                    'festnetz',
                                    'mobil',
                                    HTML("<p>"),
                                    'status', 'arbeitslast',
                                    HTML("<p>"),
                                    )

        self.helper.add_input(Submit('apply', 'Mitglied anlegen'))

    def clean(self):
        # try to see if we already have such a user with that mitgliedsnummer:
        # first, strip it off to make sure we did not get messy data

        try:
            mnrnum = int(self.cleaned_data['mitgliedsnummer'])
        except:
            raise ValidationError(
                u"Die Mitgliedsnummer muss eine Zahl sein (führende Nullen sind ok.",
                code='invalid')

        # turn it back, search for such a user:
        mnr = '%05d' % mnrnum

        try:
            u = User.objects.get(username=mnr)
            raise ValidationError(
                u"Ein Nutzer mit dieser Mitgliedsnummer existiert bereits! ({} {}) Bitte wählen Sie eine andere Nummer.".format(
                    u.first_name, u.last_name
                ),
                code="invalid"
            )
        except User.DoesNotExist:
            pass

        self.cleaned_data['mitgliedsnummer'] = mnr

        return self.cleaned_data

    class Meta:
        model = models.Mitglied

        fields = ['mitgliedsnummer', 'geburtsdatum', 'gender',
                  'strasse', 'plz',  'ort',
                  'festnetz', 'mobil',
                  'status', 'arbeitslast']


class AccountEdit(forms.Form):
    email = forms.EmailField(
        required=True,
        help_text="Bitte aktualisieren Sie Ihre email-Adreese.")
    strasse = forms.CharField(
        required=False,
        help_text="Bitte aktualisieren Sie Ihre Strasse und Hausnummer.")
    ort = forms.CharField(
        required=False,
        help_text="Bitte aktualisieren Sie Ihren Wohnort.")
    plz = forms.DecimalField(required=False,
                             help_text="Bitte aktualisieren Sie Ihre PLZ.")

    geburtsdatum = forms.DateField(required=False,
                                   help_text="Bitte aktualisieren Sie Ihr Geburtsdatum.")

    festnetz = PhoneNumberField(required=False,
                                help_text="Ihre Festnetznummer.")

    mobil = PhoneNumberField(required=False,
                             help_text="Ihre Mobilfunknummer.")

    def computeLayout(self):
        return  Layout('email',
                       HTML("<p>"),
                       'strasse',
                       HTML("<p>"),
                       'plz', 'ort',
                       HTML("<p>"),
                       Field('geburtsdatum', css_class="datepicker"),
                       HTML("<p>"),
                       'festnetz',
                       'mobil',
        )

    def __init__(self, *args, **kwargs):
        # print "creating an Account Edit Form"

        self.helper = FormHelper()
        super(AccountEdit, self).__init__(*args, **kwargs)
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"

        self.helper.layout = self.computeLayout()

        self.helper.add_input(Submit('apply', 'Aktualisieren'))


class AccountOtherEdit(AccountEdit):
    vorname = forms.CharField(label="Vorname")
    nachname = forms.CharField(label="Nachname")

    arbeitslast = forms.IntegerField(required=False,
                                     help_text="Zu erbringende Arbeitsstunden pro Jahr",
                                     label="Arbeitsstunden")

    status = forms.ChoiceField(required=False,
                               label="Mitgliedsstatus",
                               choices=models.Mitglied.STATUSDEFAULTS,
                               )
    aktiv = forms.BooleanField(required=False,
                               label="Aktiver Nutzer",
                               help_text="Setzen Sie den Nutzer auf inaktiv, "
                               "um ein neues Passwort verschicken zu können."
                               )

    def computeLayout(self):
        l = super(AccountOtherEdit, self).computeLayout()

        return Layout ('vorname',
                       'nachname',
                       HTML("<p>"),
                       l,
                       'arbeitslast',
                       'status',
                       'aktiv')


class PersonMitgliedsnummer(NameFilterForm,
                            MitgliedsnummerFilterForm,
                            ):
    pass


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