from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test

import arbeitsplan.views, svpb.views

from activeTest import active_and_login_required


admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'svpb.views.home', name='home'),
    # url(r'^svpb/', include('svpb.foo.urls')),

    # url (r'^$',
    #      arbeitsplan.views.HomeView.as_view (template_name='home.html'),
    #      name="home",
    #      ),

    url (r'^$',
         TemplateView.as_view (template_name="main.html"),
         name="main",
         ),

    # url (r'^home/$',
    #      arbeitsplan.views.HomeView.as_view (template_name='home.html'),
    #      name="home2",
    #      ),

    url (r'^keinVorstand/$',
         TemplateView.as_view (template_name='keinVorstand.html'),
         name="keinVorstand", 
         ),

    url(r'^arbeitsplan/', include('arbeitsplan.urls')),
                       
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
