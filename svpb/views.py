# -*- coding: utf-8 -*-

"""
Views for the entire adminstration of SVPB
- login

"""

from django.contrib.auth import authenticate, login
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import FormView
from django.shortcuts import render_to_response, redirect

from svpb.forms import LoginForm, ActivateForm

class SvpbLogin(FormView):

    template_name = "registration/justForm.html"
    form_class = LoginForm
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = super(SvpbLogin, self).get_context_data()
        context['title'] = "Anmeldung"
        context['intro_text'] = ""
        context['post_text'] = ""
        context['todo_text'] = ""
        context['form'] = self.form_class()

        return context

    def form_valid(self, form):
        """form checks the authentication.
        This is only called if the user can be logged in, but is not
        necessarily active"""

        user = form.cleaned_data['user']
        print user
        if user is not None:
            succ = login(self.request, user)
            if user.is_active:
                return super(SvpbLogin, self).form_valid(form)
            else:
                return redirect('/accounts/activate/')
        else:
            # This should never happen, end up in form_invalid instead
            print "do the invalid thing"


class ActivateView(FormView):
    template_name = "registration/justForm.html"
    form_class = ActivateForm
    success_url = "/"

    def get_context_data(self, **kwargs):
        from django.utils.html import format_html, mark_safe

        context = super(ActivateView, self).get_context_data()
        context['title'] = "Aktivieren Sie Ihre SVPB-Konto"
        context['intro_text'] = format_html("""<b>Willkommen bei der ersten Nutzung Ihres SVPB-Kontos</b>
        <p>
        Vor der Nutzung dieser Webseite bitten wir Sie um folgendes:
        <ul>
        <li>Bitte überprüfen Sie Ihre email-Adresse und korrigieren Sie diese
        gegebenenfalls </li>
        <li>Bitte stimmen Sie der Nutzung der Webseite zu </li>
        <li>Bitte stimmen Sie zu, dass der SVPB Ihnen emails im Zusammenhang mit dem
        Arbeitsplan schicken darf. </li>
        <li>Bitte vergeben Sie ein neues Passwort! (Die beiden Eingaben
        müssen übereinstimmen) </li>
        </ul>
        Ohne diese Zustimmungn können Sie diese Webseite leider nicht nutzen!
        """)
        context['post_text'] = ""
        context['todo_text'] = ""
        context['form'] = self.form_class()

        return context

    def get_initial(self):
        initial = super(ActivateView, self).get_initial()
        initial['email'] = self.request.user.email
        return initial

    def form_valid(self, form):
        from django.utils import timezone

        # set user active, store its email, rememmber date
        self.request.user.email = form.cleaned_data['email']
        self.request.user.is_active = True
        self.request.user.mitglied.zustimmungsDatum = timezone.now()
        self.request.user.save()
        self.request.user.mitglied.save()

        return super(ActivateView, self).form_valid(form)
