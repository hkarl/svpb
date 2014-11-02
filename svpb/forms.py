# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ValidationError
from django.contrib import messages
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Button, Field, Div, HTML

class LoginForm(forms.Form):
    username = forms.CharField(label="Nutzername",
                               help_text="In der Regel: Ihre Mitgliedsnummer")
    password = forms.CharField(widget=forms.PasswordInput,
                               label="Passwort",
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
            raise ValidationError('Der Nutzer konnte nicht angemeldet werden.')

        return self.cleaned_data

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

            if pw1 != pw2:
                raise ValidationError('Die beiden Passwörter müssen übereinstimmen')
        except:
            raise ValidationError('Beide Passwörter müssen angegebn werden')

        return self.cleaned_data
