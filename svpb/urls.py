from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.auth.views import login

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
         name="home", 
         ), 
         
    url (r'^arbeitsplan/aufgaben/$',
         arbeitsplan.views.ListAufgabenView.as_view(),
         name="arbeitsplan-aufgaben",
         ),

    url (r'^arbeitsplan/zuteilungAnzeige/$',
         login_required(arbeitsplan.views.ListZuteilungenView.as_view()),
         name="arbeitsplan-zuteilunglist",
         ),

    url (r'^arbeitsplan/meldungAnzeige/$',
         login_required(arbeitsplan.views.ListMeldungenView.as_view()),
         name="arbeitsplan-meldunglist",
         ),

    url (r'^arbeitsplan/erstelleZuteilung/$',
         login_required(arbeitsplan.views.ErstelleZuteilungView.as_view()),
         name="arbeitsplan-erstellezuteilung",
         ),

    url (r'^arbeitsplan/meldung/$',
         login_required(arbeitsplan.views.UpdateMeldungView.as_view()),
         name="arbeitsplan-meldung",),
         
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url (r'^accounts/login/', login), 
)
