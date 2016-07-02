from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

import mitglieder.forms
from svpb.activeTest import active_and_login_required

import mitglieder.views

urlpatterns = patterns('',
    url(r'^$',
        active_and_login_required(TemplateView.as_view(template_name="mitgliederHome.html")),
        name="mitgliederHome"),

    url(r'^home/',
        active_and_login_required(TemplateView.as_view(template_name="mitgliederHome.html")),
        name="mitgliederHome"),

    # url (r'^accounts/login/', login),
    url (r'^activate/',
         login_required(mitglieder.views.ActivateView.as_view()),
         name="activate"),

    # to edit my own account:
    url(r'^edit/',
        active_and_login_required(mitglieder.views.AccountEdit.as_view()),
        name="accountEdit"),

    # to edit other people:
    url(r'^editOther/(?P<id>\d+)/',
        active_and_login_required(mitglieder.views.AccountOtherEdit.as_view()),
        name="accountOtherEdit"),

    url(r'^delete/(?P<pk>\d+)/',
        active_and_login_required(mitglieder.views.AccountDelete.as_view()),
        name="accountDelete"),

    url(r'^add/',
        active_and_login_required(mitglieder.views.AccountAdd.as_view()),
        name="accountAdd"
        ),

    url(r'^list/',
        active_and_login_required(mitglieder.views.AccountList.as_view()),
        name="accountList"
        ),

    url(r'^inaktiveReset/',
        active_and_login_required(mitglieder.views.AccountInactiveReset.as_view()),
        name="accountInactiveReset"
        ),

    url(r'^letters.pdf',
        active_and_login_required(mitglieder.views.AccountLetters.as_view()),
        name="accountLetters"
        ),

    # sammlung aller Mitglieder
    url(r'^mitgliederexcel.xlsx',
        active_and_login_required(mitglieder.views.MitgliederExcel.as_view()),
        name="mitgliedExcel"
        ),

   )