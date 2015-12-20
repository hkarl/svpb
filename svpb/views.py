# -*- coding: utf-8 -*-

"""
Views for the entire adminstration of SVPB
- login

"""


from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import (redirect, render)
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.generic import FormView


@receiver(post_save, sender=User)
def create_mitglied(sender, instance, created, **kwargs):
    # print "creating : ", sender, created
    if created:
        Mitglied.objects.get_or_create(user=instance)


###############

def isVorstand(user):
    return user.groups.filter(name='Vorstand')


def isTeamlead(user):
    return user.teamleader_set.count() > 0


def isVorstandOrTeamleader(user):
    return isVorstand(user) or isTeamlead(user)


class isVorstandMixin(object):
    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def dispatch(self, *args, **kwargs):
        return super(isVorstandMixin, self).dispatch(*args, **kwargs)


class isVorstandOrTeamleaderMixin(object):
    @method_decorator(user_passes_test(isVorstandOrTeamleader, login_url="/keinVorstand/"))
    def dispatch(self, *args, **kwargs):
        return super(isVorstandOrTeamleaderMixin, self).dispatch(*args, **kwargs)


###############

from svpb.forms import (LoginForm,
                        )
from svpb.settings import OFFLINE
from arbeitsplan.models import Mitglied


class SvpbLogin(FormView):
    if OFFLINE:
        template_name = "home.html"
    else:
        template_name = "registration/justForm.html"

    form_class = LoginForm
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = super(SvpbLogin, self).get_context_data(**kwargs)
        context['title'] = "Anmeldung"
        if JAHRESENDE:
            context['intro_text'] = "Zur Zeit ist eine Anmeldung nur für Vorstände und Teamleiter möglich!"
        else:
            context['intro_text'] = ""
        context['post_text'] = format_html('Passwort vergessen? <a href="/reset/recover/"> Hier zurücksetzen.<a/>')
        context['todo_text'] = ""

        return context

    def get_success_url(self):
        try:
            return self.request.GET['next']
        except:
            return super(SvpbLogin, self).get_success_url()

    def form_valid(self, form):
        """form checks the authentication.
        This is only called if the user can be logged in, but is not
        necessarily active"""

        user = form.cleaned_data['user']
        # print user
        if user is not None:
            succ = login(self.request, user)

            if JAHRESENDE and not isVorstandOrTeamleader(user):
                messages.warning(self.request,
                                 format_html(u"Derzeit ist ein Anmeldung nur für Vorstände oder Teamleiter möglich."))
                # make normal users go away
                logout(self.request)
                return redirect('/')

            if JAHRESENDE:
                messages.warning(self.request,
                                 format_html(u"Jahresende-Modus! Bitte <b>vor allem die Aufgaben</b> bearbeiten - Datum prüfen, ggf. direk Mitglieder einteilen!"))

            if user.is_active:
                tmp = user.mitglied.profileIncomplete()
                if tmp:
                    messages.warning(self.request,
                                     format_html(
                                         u"Ihre Profilangaben sind unvollständig.<br>"
                                         u"Es fehlen {}.<br>"
                                         u'Bitte ergänzen Sie <a href="/accounts/edit/">Ihr Profil.</a>',
                                         tmp
                                     ))
                return super(SvpbLogin, self).form_valid(form)
            else:
                return redirect('/accounts/activate/')
        else:
            # This should never happen, end up in form_invalid instead
            print "do the invalid thing"


##############


def logout_view(request):
    # print "logout view"
    logout(request)
    return render(request, "registration/logged_out.html", {})
