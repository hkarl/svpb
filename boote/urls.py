from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from svpb.activeTest import active_and_login_required

import boote.views

# place app url patterns here

urlpatterns = patterns('',
    url(r'^$',
        active_and_login_required(TemplateView.as_view(template_name="booteHome.html")),
        name="booteHome"),

    url(r'^home/',
        active_and_login_required(TemplateView.as_view(template_name="booteHome.html")),
        name="booteHome"),

    )

