# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ValidationError
from django.contrib import messages
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Button, Field, Div, HTML

from arbeitsplan import models
from django.contrib.auth.models import User

from phonenumber_field.formfields import PhoneNumberField

class LoginForm(forms.Form):
    username = forms.CharField(label="Nutzername",
                               help_text="In der Regel: Ihre Mitgliedsnummer, mit führenden 0 auf 5 Stellen  aufgefüllt")
    password = forms.CharField(widget=forms.PasswordInput,
                               label="Passwort",
                               required=True,
                               )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"

        self.helper.layout = Layout('username', 'password', HTML("<p>"),)
        self.helper.add_input(Submit('apply', 'Anmelden'))

    def clean(self):
        from django.contrib.auth import authenticate
        error = False

        try:
            username = self.cleaned_data['username']
            password = self.cleaned_data['password']

            # print username, password
            user = authenticate(username=username,
                                password=password)

            if user:
                self.cleaned_data['user'] = user
            else:
                error = True
        except:
            error = True

        if error:
            print "raising validation in Login", username
            raise ValidationError('Der Nutzer konnte nicht angemeldet werden.')

        return self.cleaned_data


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


class MitgliederInactiveResetForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(MitgliederInactiveResetForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.add_input(Submit('reset', 'Passwörter zurücksetzen'))
        self.helper.add_input(Submit('nono', 'Lieber nicht!'))

        
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
                  'status', 'arbeitslast']
