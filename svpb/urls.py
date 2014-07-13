from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.contrib.auth.decorators import login_required

import arbeitsplan.views
import arbeitsplan.models 


admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'svpb.views.home', name='home'),
    # url(r'^svpb/', include('svpb.foo.urls')),

    url (r'^$',
         TemplateView.as_view (template_name='home.html'),
         name="home", 
         ), 

    url (r'^home/$',
         TemplateView.as_view (template_name='home.html'),
         name="home",
         ),

    url (r'^keinVorstand/$',
         TemplateView.as_view (template_name='keinVorstand.html'),
         name="keinVorstand", 
         ),

    url (r'^arbeitsplan/benachrichtigen/leistung/$',
         arbeitsplan.views.LeistungEmailView.as_view(),
         name="arbeitsplan-benachrichtigen-leistung",
         ),

    url (r'^arbeitsplan/benachrichtigen/zuteilung/$',
         arbeitsplan.views.ZuteilungEmailView.as_view(),
         name="arbeitsplan-benachrichtigen-leistung",
         ),

    url (r'^arbeitsplan/benachrichtigen/senden/$',
         arbeitsplan.views.EmailSendenView.as_view(),
         name="arbeitsplan-benachrichtigen-senden",
         ),

    url (r'^arbeitsplan/aufgaben/$',
         arbeitsplan.views.ListAufgabenView.as_view(),
         name="arbeitsplan-aufgaben",
         ),

    url (r'^arbeitsplan/zuteilungAnzeige/(?P<wer>[a-zA-Z]+)/$',
         login_required(arbeitsplan.views.ListZuteilungenView.as_view()),
         name="arbeitsplan-zuteilunglist",
         ),

    url (r'^arbeitsplan/meldungVorstand/$',
         login_required(arbeitsplan.views.MeldungVorstandView.as_view()),
         name="arbeitsplan-meldungVorstand",
         ),

    url (r'^arbeitsplan/erstelleZuteilung/$',
         login_required(arbeitsplan.views.ErstelleZuteilungView.as_view()),
         name="arbeitsplan-erstellezuteilung",
         ),

    url (r'^arbeitsplan/manuelleZuteilung/$',
         login_required(arbeitsplan.views.ManuelleZuteilungView.as_view()),
         name="arbeitsplan-manuellezuteilung",
         ),

    url (r'^arbeitsplan/manuelleZuteilung/(?P<aufgabe>\d+)/$',
         login_required(arbeitsplan.views.ManuelleZuteilungView.as_view()),
         name="arbeitsplan-manuellezuteilungAufgabe",
         ),

    url (r'^arbeitsplan/zuteilungUebersicht/$',
         login_required(arbeitsplan.views.ZuteilungUebersichtView.as_view()),
         name="arbeitsplan-zuteilungUebersicht",
         ),

    url (r'^arbeitsplan/stundenplaene/(?P<aufgabeid>\d+)/$',
         login_required(arbeitsplan.views.StundenplaeneEdit.as_view()),
         name="arbeitsplan-stundenplaeneEdit",
         ),

    url (r'^arbeitsplan/meldung/$',
         login_required(arbeitsplan.views.CreateMeldungenView.as_view()),
         name="arbeitsplan-meldung",),

    url (r'^arbeitsplan/leistung/$',
         login_required(arbeitsplan.views.CreateLeistungView.as_view(
             success_url="/home/")),
         name="arbeitsplan-leistung",),

    url (r'^arbeitsplan/leistungenBearbeiten/z=(?P<zustaendig>[a-zA-Z]+)/$',
         login_required(arbeitsplan.views.LeistungBearbeitenView.as_view()),
         name="arbeitsplan-leistungBearbeiten",),

    url (r'^arbeitsplan/leistungListe/$',
         login_required(arbeitsplan.views.ListLeistungView.as_view()),
         name="arbeitsplan-leistungListe",),

    url (r'^arbeitsplan/salden/$',
         login_required(arbeitsplan.views.Salden.as_view()),
         name="arbeitsplan-salden",),

    url (r'^arbeitsplan/aufgabeErzeugen/$',
         login_required(arbeitsplan.views.AufgabenCreate.as_view()),
         name="arbeitsplan-aufgabenErzeugen",),

    url (r'^arbeitsplan/aufgabeEditieren/(?P<pk>\d+)/$',
         login_required(arbeitsplan.views.AufgabenUpdate.as_view()),
         name="arbeitsplan-aufgabenEdit",),

    url(r'^arbeitsplan/aufgabengruppeErzeugen/$',
         login_required(arbeitsplan.views.AufgabengruppeCreate.as_view()),
         name="arbeitsplan-aufgabengruppeCreate",),

    url(r'^arbeitsplan/aufgabengruppen/$',
         login_required(arbeitsplan.views.AufgabengruppeList.as_view()),
         name="arbeitsplan-aufgabengruppeList",),

    url (r'^arbeitsplan/aufgabengruppeEditieren/(?P<pk>\d+)/$',
         login_required(arbeitsplan.views.AufgabengruppeUpdate.as_view()),
         name="arbeitsplan-aufgabengruppeEdit",),

    url (r'^bootstrap$',
         TemplateView.as_view(template_name="bootstrap.html"),
         name="bootstrap", 
         ),

    url(r'^about$',
        TemplateView.as_view (template_name="about.html"),
        name="about", 
        ),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url (r'^accounts/login/', login),

    url (r'^logout/', arbeitsplan.views.logout_view),

    url (r'^password/change/$',
         login_required(arbeitsplan.views.PasswordChange.as_view()),
         name='password_change',
         ),

    ## Impersonation of other users:
    url(r'^impersonate/', include('impersonate.urls')),
    url(r'^impersonate/liste/$',
         login_required(arbeitsplan.views.ImpersonateListe.as_view()),
         name="arbeitsplan-impersonateListe",),

)
