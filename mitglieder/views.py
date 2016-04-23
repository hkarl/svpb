# -*- coding: utf-8 -*-


"""Views for anything that relates to adminstration of members.
Login and logout stays in SVPB
"""
import os

from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command

from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import View, FormView, CreateView, DeleteView
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, get_object_or_404

from django.contrib.auth.models import User, Group

from post_office import mail
from post_office.models import EmailTemplate
from pwgen import pwgen
from sendfile import sendfile

import mitglieder.forms
from arbeitsplan import forms
from arbeitsplan.tables import ImpersonateTable
from mitglieder.tables import MitgliederTable
from arbeitsplan.views import FilteredListView

from mitglieder.forms import (ActivateForm,
                              MitgliederAddForm,
                              AccountEdit,
                              AccountOtherEdit,
                              PersonMitgliedsnummer,
                              )
from arbeitsplan.models import Mitglied
from svpb.forms import MitgliederInactiveResetForm
from svpb.settings import SENDFILE_ROOT
from svpb.views import isVorstandMixin, isVorstand


#-------------------------------------------------

class ActivateView(FormView):
    template_name = "registration/justForm.html"
    form_class = ActivateForm
    success_url = "/"

    def get_context_data(self, **kwargs):

        context = super(ActivateView, self).get_context_data(**kwargs)
        context['title'] = "Aktivieren Sie Ihre SVPB-Konto"
        context['intro_text'] = format_html("""<b>Willkommen bei der ersten Nutzung Ihres SVPB-Kontos</b>
        <p>
        Vor der Nutzung dieser Webseite bitten wir Sie um folgendes:
        <ul>
        <li>Bitte überprüfen Sie Ihre email-Adresse und korrigieren Sie diese
        gegebenenfalls </li>
        <li>Bitte stimmen Sie der Nutzung der Webseite zu </li>
        <li>Bitte stimmen Sie zu, dass der SVPB Ihnen emails
         im Zusammenhang mit dem
        Arbeitsplan schicken darf. </li>
        <li>Bitte vergeben Sie ein neues Passwort! (Die beiden Eingaben
        müssen übereinstimmen) </li>
        </ul>
        Ohne diese Zustimmungn können Sie diese Webseite leider nicht nutzen!
        """)
        context['post_text'] = ""
        context['todo_text'] = ""

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
        self.request.user.set_password(form.cleaned_data['pw1'])

        self.request.user.mitglied.zustimmungsDatum = timezone.now()

        self.request.user.save()
        self.request.user.mitglied.save()

        return super(ActivateView, self).form_valid(form)


def preparePassword(accountList=None):
    """For the given accounts, prepare the passwords and the PDFs for the letters

    Arguments:
    - `accountList`: List of User objects
    Returns:
    - List of tuples: (user object, PDF file)
    """

    from jinja2 import Template
    import codecs, subprocess

    r = []

    # print "preparing passwords for: ", accountList

    for u in accountList:
        pw = pwgen(6, no_symbols=True, no_ambiguous=True)
        u.set_password(pw)
        u.save()

        r.append({'user': u,
                  'mitglied': u.mitglied,
                  'password': pw,
                  'status': u.mitglied.get_status_display(),
                  'geburtsdatum': u.mitglied.geburtsdatum.strftime('%d.%m.%Y'),
                  })

    # generate the PDF
    # assume the template is in templates

    templateText = EmailTemplate.objects.get(name='newUserLaTeX')
    # print templateText.content

    rendered = Template(templateText.content).render(dicts=r)
    # print rendered

    # and now process this via latex:
    f = codecs.open('letters.tex', 'w', 'utf-8')
    f.write(rendered)
    f.close()

    # TODO: use better file names, protect against race conditions

    retval = subprocess.call (["xelatex",
                                '-interaction=batchmode',
                                "letters.tex"])
    ## retval = subprocess.call (["xelatex",
    ##                                '-interaction=batchmode',
    ##                                "letters.tex"])

    # move this file into a directory where only Vorstand has access!
    # remove an older letter first; ignore errors here
    import shutil, os
    try:
        os.remove (os.path.join (SENDFILE_ROOT, 'letters.pdf'))
    except:
        pass

    shutil.move("letters.pdf", SENDFILE_ROOT)

    return r

class AccountAdd(SuccessMessageMixin, isVorstandMixin, CreateView):
    model = Mitglied
    title = "Mitglied hinzufügen"
    template_name = "mitglied_form.html"
    form_class = MitgliederAddForm
    success_url = "/accounts"

    def get_context_data(self, **kwargs):
        context = super(AccountAdd, self).get_context_data(**kwargs)

        context['title'] = self.title

        return context

    def form_valid(self, form):
        # create User and Mitglied based on cleaned data

        # first, make some sanity checks to provide warnings
        u = User(first_name=form.cleaned_data['firstname'],
                 last_name=form.cleaned_data['lastname'],
                 is_active=False,
                 username=form.cleaned_data['mitgliedsnummer'],
                 email=form.cleaned_data['email'],
                 )

        u.set_password('test')
        u.save()

        m = u.mitglied

        m.user = u

        m.geburtsdatum = form.cleaned_data['geburtsdatum']
        m.mitgliedsnummer = form.cleaned_data['mitgliedsnummer']
        m.ort = form.cleaned_data['ort']
        m.plz = form.cleaned_data['plz']
        m.strasse = form.cleaned_data['strasse']
        m.gender = form.cleaned_data['gender']
        m.status = form.cleaned_data['status']
        m.arbeitlast = form.cleaned_data['arbeitslast']
        m.festnetz = form.cleaned_data['festnetz']
        m.mobil = form.cleaned_data['mobil']

        m.save()
        u.save()

        messages.success(self.request,
                         format_html(
                             u"Nutzer {} {} (Nummer: {}, Account: {}) "
                             u"wurde erfolgreich angelegt",
                             u.first_name,
                             u.last_name, m.mitgliedsnummer,
                             u.username
                             ))

        try:
            r = preparePassword([u])
            print u"PAssword erzeugt: ", r

            # copy the produced PDF to the SENDFILE_ROOT directory

            messages.success(self.request,
                             format_html(
                                 u'Das Anschreiben mit Password kann '
                                 u'<a href="{}">hier</a>'
                                 u' heruntergeladen werden.',
                                 u'letters.pdf'
                                 ))

        except Exception as e:
            print "Fehler bei password: ", e
            messages.error(self.request,
                           u"Das Password für den Nutzer konnte nicht gesetzt werden "
                           u"oder das Anschreiben nicht erzeugt werden. Bitten Sie das "
                           u"neue Mitglied, sich über die Webseite selbst ein Password zu "
                           u"generieren.")

        return redirect(self.success_url)

class AccountEdit(SuccessMessageMixin, FormView):
    template_name = "registration/justForm.html"
    form_class = AccountEdit
    success_url = "/"
    post_text = format_html("""
    <p>
    Sie haben Ihr Passwort vergessen? Sie können es <a href="{{% url "password_reset_recover" %}}">
    hier zurücksetzen</a>.
    <p>
    """)

    def get_context_data(self, **kwargs):
        context = super(AccountEdit, self).get_context_data(**kwargs)
        context['title'] = "Aktualisieren Sie Ihr SVPB-Konto"
        context['post_text'] = self.post_text
        return context

    def fillinUser(self, user):
        initial = {}
        initial['email'] = user.email
        initial['strasse'] = user.mitglied.strasse
        initial['plz'] = user.mitglied.plz
        initial['ort'] = user.mitglied.ort
        initial['geburtsdatum'] = user.mitglied.geburtsdatum
        initial['festnetz'] = user.mitglied.festnetz
        initial['mobil'] = user.mitglied.mobil

        return initial

    def get_initial(self):
        initial = super(AccountEdit, self).get_initial()
        initial.update(self.fillinUser(self.get_user()))
        return initial

    def storeUser (self, form, user):
        user.email = form.cleaned_data['email']
        user.mitglied.strasse = form.cleaned_data['strasse']
        user.mitglied.plz = form.cleaned_data['plz']
        user.mitglied.ort = form.cleaned_data['ort']
        user.mitglied.geburtsdatum = form.cleaned_data['geburtsdatum']
        user.mitglied.festnetz = form.cleaned_data['festnetz']
        user.mitglied.mobil = form.cleaned_data['mobil']

    def get_user(self):
        return self.request.user

    def form_valid(self, form):

        if form.has_changed():
            user = self.get_user()
            self.storeUser(form, user)

            user.save()
            user.mitglied.save()

            # print ({'user': user.__dict__,
            #         'mitglied': user.mitglied.__dict__})
            # print type(user)
            # print user.last_name
            # print type(user.mitglied)

            # inform the relevant Vorstand in charge of memeberhsip
            mail.send(['mail@svpb.de'],
                      template="updatedProfile",
                      context={'user': user,
                               'mitglied': user.mitglied,
                               'changed': form.changed_data},
                      priority='now',
                      )

            messages.success(self.request,
                             format_html(
                                 u"Das Profil {} {} ({}) wurde erfolgreich aktualisiert.",
                                 user.first_name, user.last_name,
                                 user.mitglied.mitgliedsnummer))
        else:
            messages.success(self.request,
                             "Sie haben keine Änderungen vorgenommen."
                             )

        return super(AccountEdit, self).form_valid(form)

class AccountOtherEdit(isVorstandMixin, AccountEdit):
    form_class = AccountOtherEdit
    post_text = ""

    def get_context_data(self, **kwargs):
        context = super(AccountOtherEdit, self).get_context_data(**kwargs)
        context['title'] = "Bearbeiten Sie das  SVPB-Konto eines Mitgliedes"
        return context

    def fillinUser(self, user):      
        
        initial = super(AccountOtherEdit, self).fillinUser(user)
        initial['vorname'] = user.first_name
        initial['nachname'] = user.last_name
        initial['arbeitslast'] = user.mitglied.arbeitslast
        initial['status'] = user.mitglied.status
        initial['aktiv'] = user.is_active
        initial['boots_app'] = user.groups.filter(name='Boote').exists()

        return initial

    def storeUser(self, form, user):
        super(AccountOtherEdit, self).storeUser(form, user)
        user.first_name = form.cleaned_data['vorname']
        user.last_name = form.cleaned_data['nachname']
        user.is_active = form.cleaned_data['aktiv']
        user.mitglied.arbeitslast = form.cleaned_data['arbeitslast']
        user.mitglied.status = form.cleaned_data['status']

        # assign BOOTE group
        group_boots = Group.objects.get(name="Boote")
        if (form.cleaned_data['boots_app']):            
            user.groups.add(group_boots)
        else:
            user.groups.remove(group_boots)
        

    def get_user(self):
        userid = self.kwargs['id']
        user = get_object_or_404(User, pk=int(userid))
        return user


class AccountLetters(isVorstandMixin, View):
    """Check whether this user is allowed to download a letters.pdf file
    """

    def get(self, request):
        return sendfile(request,
                        os.path.join(SENDFILE_ROOT,
                                "letters.pdf"))


class AccountList(SuccessMessageMixin, isVorstandMixin, FilteredListView):
    model = User
    template_name = "mitglieder_tff.html"

    title = "Mitglieder bearbeiten"

    # filterform_class = forms.NameFilterForm
    filterform_class = PersonMitgliedsnummer
    filtertile = "Mitglieder nach Vor- oder Nachnamen filtern"

    tabletitle = "Alle Mitglieder"
    tableClass = MitgliederTable

    filterconfig = [('first_name', 'first_name__icontains'),
                    ('last_name', 'last_name__icontains'),
                    ('mitgliedsnummer', 'mitglied__mitgliedsnummer__icontains'),
                    ]

    intro_text = mark_safe("""Diese Seite zeigt eine Liste aller Mitglieder an.
    Sie dient vor allem dazu, einzelne Mitglieder-Konten zu finden und zu editieren.
    Eine Übersicht über gemeldete, zugeteilte, erbrachte und akzeptieren
    Arbeitsstunden findet sich separat in der <a href="/arbeitsplan/salden/">Saldenübersicht</a>.
    """)
    

class AccountInactiveReset(FormView):
    """Für allen nicht-aktiven Accounts neue Passwörter erzeugen und PDF anlegen.
    """

    template_name = "inactive_reset.html"
    form_class = MitgliederInactiveResetForm
    success_url = "accounts/"

    def form_valid(self, form):

        if 'reset' in self.request.POST:
            userQs = User.objects.filter(is_active=False)

            try:
                r = preparePassword(userQs)
                print "PAssword erzeugt: ", r

                # copy the produced PDF to the SENDFILE_ROOT directory

                messages.success(self.request,
                                 format_html(
                                     'Das Anschreiben mit Password kann '
                                     '<a href="{}">hier</a>'
                                     ' heruntergeladen werden.',
                                     'accounts/letters.pdf'
                                     ))

            except Exception as e:
                print "Fehler bei password: ", e
                messages.error(self.request,
                               u"Ein Password konnte nicht gesetzt werden "
                               u"oder das Anschreiben nicht erzeugt werden. "
                               u"Bitte benachrichtigen Sie den Administrator.")

        return redirect(self.success_url)


class AccountDelete(SuccessMessageMixin, isVorstandMixin, DeleteView):
    model = User
    success_url = reverse_lazy("accountList")
    # success_url = "/accounts/list"
    template_name = "user_confirm_delete.html"
    # success_message = "%(first_name) %(last_name) wurde gelöscht!"
    success_message = "Mitglied wurde gelöscht!"


class MitgliederExcel(View):
    """For Vorstand, send back an Excel file with all
    the Mitlgieders in various filtering combinations"""

    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def get(self, request):

        if isVorstand(request.user):
            # call the command to prepare the excel file

            # repeated name; TODO: move this from here and mitgliedExcel.py into settings
            filename = "mitglieder.xlsx"
            basepath = SENDFILE_ROOT

            call_command('mitgliedExcel')

            return sendfile(request,
                            os.path.join(basepath, filename))
        else:
            return redirect ("keinVorstand")


class PasswordChange(FormView):
    template_name = "password_change.html"
    form_class = mitglieder.forms.PasswordChange
    success_url = reverse_lazy("main")

    def form_valid(self, form):
        try:
            u = self.request.user
            u.set_password(form.cleaned_data['pw1'])
            u.save()
            messages.success(self.request,
                             u'Ihr Passwort wurde erfolgreich geändert'
                             )
        except Exception as e:
            messages.error(self.request,
                           u'Ihre Passwortänderung ist fehlgeschlagen: ' +
                           str(e),
                           )
        return super(PasswordChange, self).form_valid(form)


class ImpersonateListe(isVorstandMixin, FilteredListView):
    """Show a table with all Mitglieder,
    pick one to impersonate.
    Needs a suitable linked Column to point
    to impersonate/user-id
    """
    title = "Darzustellenden Nutzer auswählen"
    tableClass = ImpersonateTable
    tabletitle = "Mitglieder"
    model = User

    filterform_class = forms.NameFilterForm
    filterconfig = [('first_name', 'first_name__icontains'),
                    ('last_name', 'last_name__icontains'),
                    ]


    intro_text = """Sie können die Identität eines
    anderen Nutzers annehmen,
    beispielsweise um Meldungen oder Leistungen für diesen einzutragen.
    <p>
    Bitte gehen Sie verantwortlich mit dieser Möglichkeit um!
    <p>
    Beachten Sie: Diese Funktion funktioniert nicht bei Mitgliedern
    mit Sonderstatus (z.B. Adminstratoren dieser Webseite).
    """

    def get_data(self):
        return (self.model.objects
                .filter(is_active=True)
                .filter(is_staff=False)
                .filter(is_superuser=False)
                .exclude(id=self.request.user.id))
    pass


