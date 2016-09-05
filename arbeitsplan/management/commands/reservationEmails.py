"""
Define a command that should be run from a crontab.
Check offene oder Rueckfragen Leistungsmeldungen. 
Send an email to the person in charge. 
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.utils import translation
from django.conf import settings
from django.template import loader, Context

from post_office import mail

import boote.models as models

import datetime
import pprint

class Command(BaseCommand):
    """Go through all reservations 
    and send out 
    """
    
    args = ""
    help = "Send out Reservations."
    

    def handle(self, *args, **options):
        # set the locale right, to get the dates represented correctly
        translation.activate(settings.LANGUAGE_CODE)


        t = loader.get_template("boote/email_booking.html")
        
        # get records
        
        for booking in models.Booking.objects.filter(notified = False).order_by('-date'):
            c = Context({ 'booking': booking})
            payload = t.render(c)
            sbj = '[SVPB] Reservation (' + booking.date.strftime('%d, %b %Y') + ') - ' + booking.boat.type.name + " \"" + booking.boat.name + "\"" 
            self.stdout.write('From: ' +  settings.DEFAULT_FROM_EMAIL)
            self.stdout.write('To: ' + booking.user.email)
            self.stdout.write('Subject: ' + sbj)
            self.stdout.write('Content:\n\r' + payload)
            
            mail.send(
                  [booking.user.email], 
                  settings.DEFAULT_FROM_EMAIL,
                  subject=sbj,                  
                  html_message=payload,
            )
            
            booking.notified = True
            booking.save()     
        

        call_command('send_queued_mail')

        translation.deactivate()