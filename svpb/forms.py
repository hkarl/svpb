# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ValidationError
from django.contrib import messages
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Button, Field, Div, HTML

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

            print username, password
            user = authenticate(username=username,
                                password=password)

            if user:
                self.cleaned_data['user'] = user
            else:
                error = True
        except:
            error = True

        if error:
            print "raising validation"
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

    def __init__(self, *args, **kwargs):
        print "creating an Activate Form"

        self.helper = FormHelper()
        super(AccountEdit, self).__init__(*args, **kwargs)
        self.helper.form_id = self.__class__.__name__
        self.helper.form_method = "post"

        self.helper.layout = Layout('email',
                                    HTML("<p>"),
                                    'strasse',
                                    HTML("<p>"),
                                    'plz', 'ort',
                                    HTML("<p>"),
                                    Field('geburtsdatum', css_class="datepicker"),
                                    HTML("<p>"),
                                    )
        self.helper.add_input(Submit('apply', 'Aktualisieren'))


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
        print "creating an Activate Form"

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
