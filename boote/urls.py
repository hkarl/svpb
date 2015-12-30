from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from svpb.activeTest import active_and_login_required

import boote.views

# place app url patterns here

urlpatterns = patterns('',

# BOOTS 
    url (r'boots_liste/$',
         active_and_login_required(boote.views.boot_liste),
         name="boote-liste",
         ),
    url (r'^boot/(?P<boot_pk>[0-9]+)/$',
         active_and_login_required(boote.views.boot_detail),
         name="boot-detail",
         ),
                       
# BOOKING 
    url (r'^booking/overview/$',
         active_and_login_required(boote.views.booking_overview),
         name="booking-overview",
    ),
      
      url (r'^booking/boot/(?P<boot_pk>[0-9]+)/$',
         active_and_login_required(boote.views.booking_boot),
         name="booking-boot",
    ),
                                        
    url (r'^booking/my_bookings/$',
         active_and_login_required(boote.views.booking_my_bookings),
         name="booking-my-bookings",
    ),
    url (r'^booking_remove/(?P<booking_pk>[0-9]+)/$',
         active_and_login_required(boote.views.vereinsboote_remove_booking),
         name="booking-remove",
    ),
    

# OTHER 
    url(r'^$',
        active_and_login_required(TemplateView.as_view(template_name="booteHome.html")),
        name="booteHome"),

    url(r'^home/',
        active_and_login_required(TemplateView.as_view(template_name="booteHome.html")),
        name="booteHome"),

    )

