# -*- coding: utf-8 -*-

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, HTML
from django import forms
from django.core.exceptions import ValidationError


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
            print("raising validation in Login", username)
            raise ValidationError('Der Nutzer konnte nicht angemeldet werden.')

        return self.cleaned_data


class MitgliederInactiveResetForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(MitgliederInactiveResetForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.add_input(Submit('reset', 'Passwörter zurücksetzen'))
        self.helper.add_input(Submit('nono', 'Lieber nicht!'))

        
