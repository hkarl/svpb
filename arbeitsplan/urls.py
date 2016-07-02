from django.conf.urls import patterns, url


import arbeitsplan.views
import arbeitsplan.models

from svpb.activeTest import active_and_login_required


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'svpb.views.home', name='home'),
    # url(r'^svpb/', include('svpb.foo.urls')),

    url (r'^home/$',
         active_and_login_required(arbeitsplan.views.HomeView.as_view (template_name='home.html')),
         name="home2Arbeitsplan",
         ),

    url (r'^$',
         active_and_login_required(arbeitsplan.views.HomeView.as_view (template_name='home.html')),
         name="homeArbeitsplan",
         ),

    url (r'^benachrichtigen/leistung/$',
         active_and_login_required(arbeitsplan.views.LeistungEmailView.as_view()),
         name="arbeitsplan-benachrichtigen-leistung",
         ),

    url (r'^benachrichtigen/zuteilung/$',
         active_and_login_required(arbeitsplan.views.ZuteilungEmailView.as_view()),
         name="arbeitsplan-benachrichtigen-zuteilung",
         ),

    url (r'^benachrichtigen/senden/$',
         active_and_login_required(arbeitsplan.views.EmailSendenView.as_view()),
         name="arbeitsplan-benachrichtigen-senden",
         ),

    url (r'^benachrichtigen/templateListe/$',
         active_and_login_required(arbeitsplan.views.ListEmailTemplate.as_view()),
         name="arbeitsplan-benachrichtigen-liste",
         ),

    url (r'^benachrichtigen/meldungsAufforderung/$',
         active_and_login_required(arbeitsplan.views.MeldungNoetigEmailView.as_view()),
         name="arbeitsplan-benachrichtigen-meldungsaufforderung",
         ),

    url(r'^aufgaben/$',
        active_and_login_required(arbeitsplan.views.ListAufgabenView.as_view()),
        name="arbeitsplan-aufgaben",
        ),

    url(r'^aufgabenTeamleader/$',
        active_and_login_required(arbeitsplan.views.ListAufgabenTeamleader.as_view()),
        name="arbeitsplan-aufgabenTeamleader",
        ),

    url(r'^aufgabenVorstand/$',
        active_and_login_required(arbeitsplan.views.ListAufgabenVorstandView.as_view()),
        name="arbeitsplan-aufgabenVorstand",
        ),

    url (r'^zuteilungAnzeige/(?P<wer>[a-zA-Z]+)/$',
         active_and_login_required(arbeitsplan.views.ListZuteilungenView.as_view()),
         name="arbeitsplan-zuteilunglist",
         ),

    url (r'^meldungVorstand/$',
         active_and_login_required(arbeitsplan.views.MeldungVorstandView.as_view()),
         name="arbeitsplan-meldungVorstand",
         ),

    url (r'^erstelleZuteilung/$',
         active_and_login_required(arbeitsplan.views.ErstelleZuteilungView.as_view()),
         name="arbeitsplan-erstellezuteilung",
         ),

    url (r'^manuelleZuteilung/$',
         active_and_login_required(arbeitsplan.views.ManuelleZuteilungView.as_view()),
         name="arbeitsplan-manuellezuteilung",
         ),

    url (r'^manuelleZuteilung/(?P<aufgabe>\d+)/$',
         active_and_login_required(arbeitsplan.views.ManuelleZuteilungView.as_view()),
         name="arbeitsplan-manuellezuteilungAufgabe",
         ),

    url (r'^zuteilungUebersicht/$',
         active_and_login_required(arbeitsplan.views.ZuteilungUebersichtView.as_view()),
         name="arbeitsplan-zuteilungUebersicht",
         ),

    url (r'^zuteilungDelete/(?P<pk>\d+)/$',
         active_and_login_required(arbeitsplan.views.ZuteilungLoeschenView.as_view()),
         name="arbeitsplan-zuteilungDelete",
         ),

    url (r'^stundenplaene/(?P<aufgabeid>\d+)/$',
         active_and_login_required(arbeitsplan.views.StundenplaeneEdit.as_view()),
         name="arbeitsplan-stundenplaeneEdit",
         ),

    url (r'^meldung/$',
         active_and_login_required(arbeitsplan.views.CreateMeldungenView.as_view()),
         name="arbeitsplan-meldung",),

    url (r'^meldung/liste/$',
         active_and_login_required(arbeitsplan.views.MeldungenListeView.as_view()),
         name="arbeitsplan-meldungListe",),

    url(r'^meldung/quick/(?P<aufgabeid>\d+)/$',
        active_and_login_required(arbeitsplan.views.QuickMeldung.as_view()),
        name="arbeitsplan-quickmeldung",
        ),

    url (r'^leistung/$',
         active_and_login_required(arbeitsplan.views.CreateLeistungView.as_view(
             success_url="/home/")),
         name="arbeitsplan-leistung",),

    url (r'^leistungAlle/$',
         active_and_login_required(arbeitsplan.views.CreateLeistungView.as_view(
             success_url="/home/")),
         name="arbeitsplan-leistung",),

    url (r'^leistungenBearbeiten/z=(?P<zustaendig>[a-zA-Z]+)/$',
         active_and_login_required(arbeitsplan.views.LeistungBearbeitenView.as_view()),
         name="arbeitsplan-leistungBearbeiten",),

    url (r'^leistungListe/$',
         active_and_login_required(arbeitsplan.views.ListLeistungView.as_view()),
         name="arbeitsplan-leistungListe",),

    url (r'^salden/$',
         active_and_login_required(arbeitsplan.views.Salden.as_view()),
         name="arbeitsplan-salden",),

    url (r'^aufgabeErzeugen/$',
         active_and_login_required(arbeitsplan.views.AufgabenCreate.as_view()),
         name="arbeitsplan-aufgabenErzeugen",),

    url (r'^aufgabeEditieren/(?P<pk>\d+)/$',
         active_and_login_required(arbeitsplan.views.AufgabenUpdate.as_view()),
         name="arbeitsplan-aufgabenEdit",),

    url (r'^aufgabeLoeschen/(?P<pk>\d+)/$',
         active_and_login_required(arbeitsplan.views.AufgabeLoeschen.as_view()),
         name="arbeitsplan-aufgabenDelete",),

    url(r'^aufgabengruppeErzeugen/$',
         active_and_login_required(arbeitsplan.views.AufgabengruppeCreate.as_view()),
         name="arbeitsplan-aufgabengruppeCreate",),

    url(r'^aufgabengruppen/$',
         active_and_login_required(arbeitsplan.views.AufgabengruppeList.as_view()),
         name="arbeitsplan-aufgabengruppeList",),

    url (r'^aufgabengruppeEditieren/(?P<pk>\d+)/$',
         active_and_login_required(arbeitsplan.views.AufgabengruppeUpdate.as_view()),
         name="arbeitsplan-aufgabengruppeEdit",),


)
