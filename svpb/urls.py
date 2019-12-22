from django.conf import settings
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

import arbeitsplan.views, svpb.views
import mitglieder.views

from .activeTest import active_and_login_required


admin.autodiscover()


urlpatterns = patterns('',

    url (r'^$',
         TemplateView.as_view (template_name="main.html"),
         name="main",
         ),

    url (r'^home/$',
         TemplateView.as_view (template_name="main.html"),
         name="mainHome",
         ),

    url (r'^keinVorstand/$',
         TemplateView.as_view (template_name='keinVorstand.html'),
         name="keinVorstand", 
         ),

    url(r'^arbeitsplan/', include('arbeitsplan.urls')),

    url(r'^accounts/', include('mitglieder.urls')),

    url(r'^boote/', include('boote.urls')),

    url (r'^bootstrap$',
         TemplateView.as_view(template_name="bootstrap.html"),
         name="bootstrap", 
         ),

    url(r'^about$',
        TemplateView.as_view (template_name="about.html"),
        name="about", 
        ),

    url(r'^dsgvo$',
        TemplateView.as_view (template_name="datenschutzerklaerung.html"),
        name="about", 
        ),

    url(r'^admin/', include(admin.site.urls)),

    url (r'^login/',
         svpb.views.SvpbLogin.as_view(),
         name="login"),

    url (r'^logout/', svpb.views.logout_view),

    url (r'^password/change/$',
         active_and_login_required(mitglieder.views.PasswordChange.as_view()),
         name='password_change',
         ),

    # media for manual intergration:
    url(r'^manual/',
        active_and_login_required(arbeitsplan.views.MediaChecks.as_view()),
        name="MediaCheck"),

                       ## Impersonation of other users:
    url(r'^impersonate/', include('impersonate.urls')),

    url(r'^impersonate/liste/$',
        active_and_login_required(mitglieder.views.ImpersonateListe.as_view()),
        name="arbeitsplan-impersonateListe", ),

                       # password reset; compare http://django-password-reset.readthedocs.org/en/latest/quickstart.html
    url(r'^reset/', include('password_reset.urls')),

                       # django select2, see: https://github.com/applegrew/django-select2
    url(r'^select2/', include('django_select2.urls')),

    )

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}))
