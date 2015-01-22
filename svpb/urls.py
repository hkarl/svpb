from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME

import arbeitsplan.views, svpb.views
import arbeitsplan.models 


admin.autodiscover()

def active_and_login_required(function=None,
                              redirect_field_name=REDIRECT_FIELD_NAME,
                              login_url=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_active,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


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
         active_and_login_required(arbeitsplan.views.LeistungEmailView.as_view()),
         name="arbeitsplan-benachrichtigen-leistung",
         ),

    url (r'^arbeitsplan/benachrichtigen/zuteilung/$',
         active_and_login_required(arbeitsplan.views.ZuteilungEmailView.as_view()),
         name="arbeitsplan-benachrichtigen-leistung",
         ),

    url (r'^arbeitsplan/benachrichtigen/senden/$',
         active_and_login_required(arbeitsplan.views.EmailSendenView.as_view()),
         name="arbeitsplan-benachrichtigen-senden",
         ),

    url(r'^arbeitsplan/aufgaben/$',
        active_and_login_required(arbeitsplan.views.ListAufgabenView.as_view()),
        name="arbeitsplan-aufgaben",
        ),

    url(r'^arbeitsplan/aufgabenVorstand/$',
        active_and_login_required(arbeitsplan.views.ListAufgabenVorstandView.as_view()),
        name="arbeitsplan-aufgabenVorstand",
        ),

    url (r'^arbeitsplan/zuteilungAnzeige/(?P<wer>[a-zA-Z]+)/$',
         active_and_login_required(arbeitsplan.views.ListZuteilungenView.as_view()),
         name="arbeitsplan-zuteilunglist",
         ),

    url (r'^arbeitsplan/meldungVorstand/$',
         active_and_login_required(arbeitsplan.views.MeldungVorstandView.as_view()),
         name="arbeitsplan-meldungVorstand",
         ),

    url (r'^arbeitsplan/erstelleZuteilung/$',
         active_and_login_required(arbeitsplan.views.ErstelleZuteilungView.as_view()),
         name="arbeitsplan-erstellezuteilung",
         ),

    url (r'^arbeitsplan/manuelleZuteilung/$',
         active_and_login_required(arbeitsplan.views.ManuelleZuteilungView.as_view()),
         name="arbeitsplan-manuellezuteilung",
         ),

    url (r'^arbeitsplan/manuelleZuteilung/(?P<aufgabe>\d+)/$',
         active_and_login_required(arbeitsplan.views.ManuelleZuteilungView.as_view()),
         name="arbeitsplan-manuellezuteilungAufgabe",
         ),

    url (r'^arbeitsplan/zuteilungUebersicht/$',
         active_and_login_required(arbeitsplan.views.ZuteilungUebersichtView.as_view()),
         name="arbeitsplan-zuteilungUebersicht",
         ),

    url (r'^arbeitsplan/stundenplaene/(?P<aufgabeid>\d+)/$',
         active_and_login_required(arbeitsplan.views.StundenplaeneEdit.as_view()),
         name="arbeitsplan-stundenplaeneEdit",
         ),

    url (r'^arbeitsplan/meldung/$',
         active_and_login_required(arbeitsplan.views.CreateMeldungenView.as_view()),
         name="arbeitsplan-meldung",),
         
    url (r'^arbeitsplan/meldung/liste/$',
         active_and_login_required(arbeitsplan.views.MeldungenListeView.as_view()),
         name="arbeitsplan-meldungListe",),

    url(r'^arbeitsplan/meldung/quick/(?P<aufgabeid>\d+)/$',
        active_and_login_required(arbeitsplan.views.QuickMeldung.as_view()),
        name="arbeitsplan-quickmeldung",
        ),

    url (r'^arbeitsplan/leistung/$',
         active_and_login_required(arbeitsplan.views.CreateLeistungView.as_view(
             success_url="/home/")),
         name="arbeitsplan-leistung",),

    url (r'^arbeitsplan/leistungenBearbeiten/z=(?P<zustaendig>[a-zA-Z]+)/$',
         active_and_login_required(arbeitsplan.views.LeistungBearbeitenView.as_view()),
         name="arbeitsplan-leistungBearbeiten",),

    url (r'^arbeitsplan/leistungListe/$',
         active_and_login_required(arbeitsplan.views.ListLeistungView.as_view()),
         name="arbeitsplan-leistungListe",),

    url (r'^arbeitsplan/salden/$',
         active_and_login_required(arbeitsplan.views.Salden.as_view()),
         name="arbeitsplan-salden",),

    url (r'^arbeitsplan/aufgabeErzeugen/$',
         active_and_login_required(arbeitsplan.views.AufgabenCreate.as_view()),
         name="arbeitsplan-aufgabenErzeugen",),

    url (r'^arbeitsplan/aufgabeEditieren/(?P<pk>\d+)/$',
         active_and_login_required(arbeitsplan.views.AufgabenUpdate.as_view()),
         name="arbeitsplan-aufgabenEdit",),

    url (r'^arbeitsplan/aufgabeLoeschen/(?P<pk>\d+)/$',
         active_and_login_required(arbeitsplan.views.AufgabeLoeschen.as_view()),
         name="arbeitsplan-aufgabenDelete",),

    url(r'^arbeitsplan/aufgabengruppeErzeugen/$',
         active_and_login_required(arbeitsplan.views.AufgabengruppeCreate.as_view()),
         name="arbeitsplan-aufgabengruppeCreate",),

    url(r'^arbeitsplan/aufgabengruppen/$',
         active_and_login_required(arbeitsplan.views.AufgabengruppeList.as_view()),
         name="arbeitsplan-aufgabengruppeList",),

    url (r'^arbeitsplan/aufgabengruppeEditieren/(?P<pk>\d+)/$',
         active_and_login_required(arbeitsplan.views.AufgabengruppeUpdate.as_view()),
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

    # url (r'^accounts/login/', login),
    url (r'^accounts/login/',
         svpb.views.SvpbLogin.as_view(),
         name="login"),

    url (r'^accounts/activate/',
         login_required(svpb.views.ActivateView.as_view()),
         name="activate"),

    url (r'^logout/', arbeitsplan.views.logout_view),

    url (r'^password/change/$',
         active_and_login_required(arbeitsplan.views.PasswordChange.as_view()),
         name='password_change',
         ),

    # to edit my own account: 
    url(r'^accounts/edit/',
        active_and_login_required(svpb.views.AccountEdit.as_view()),
        name="accountEdit"),

    # to edit other people: 
    url(r'^accounts/editOther/(?P<id>\d+)/',
        active_and_login_required(svpb.views.AccountOtherEdit.as_view()),
        name="accountOtherEdit"),

    url(r'^accounts/delete/(?P<pk>\d+)/',
        active_and_login_required(svpb.views.AccountDelete.as_view()),
        name="accountDelete"),
        
    url(r'^accounts/add/',
        active_and_login_required(svpb.views.AccountAdd.as_view()),
        name="accountAdd"
        ),

    url(r'^accounts/list/',
        active_and_login_required(arbeitsplan.views.AccountList.as_view()),
        name="accountList"
        ),

    url(r'^accounts/inaktiveReset/',
        active_and_login_required(svpb.views.AccountInactiveReset.as_view()),
        name="accountInactiveReset"
        ),
        
    url(r'^accounts/letters.pdf',
        active_and_login_required(svpb.views.AccountLetters.as_view()),
        name="accountLetters"
        ),

    # sammlung aller Mitglieder
    url(r'^accounts/mitgliederexcel.xlsx',
        active_and_login_required(svpb.views.MitgliederExcel.as_view()),
        name="mitgliedExcel"
        ),
    
    # media for manual intergration:
    url(r'^manual/',
        active_and_login_required(arbeitsplan.views.MediaChecks.as_view()),
        name="MediaCheck"),

    ## Impersonation of other users:
    url(r'^impersonate/', include('impersonate.urls')),
    url(r'^impersonate/liste/$',
         active_and_login_required(arbeitsplan.views.ImpersonateListe.as_view()),
         name="arbeitsplan-impersonateListe",),

    # password reset; compare http://django-password-reset.readthedocs.org/en/latest/quickstart.html
    url(r'^reset/', include('password_reset.urls')),

    # django select2, see: https://github.com/applegrew/django-select2
    url(r'^select2/', include('django_select2.urls')),
)
