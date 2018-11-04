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


        # EMAIL RESERVATION
        t = loader.get_template("boote/email_booking.html")        
        # get records        
        for booking in models.Booking.objects.filter(notified = False).order_by('-date'):
            try:
                c = Context({ 'booking': booking})
                payload = t.render(c)
                sbj = '[SVPB] Reservierung (' + booking.date.strftime('%d.%m.%Y') + ') - ' + booking.boat.type.name + " \"" + booking.boat.name + "\"" 
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
            except:
                print("Unexpected error ")     
            
        # EMAIL ISSUES
        t = loader.get_template("boote/email_issue.html")        
        # get records        
        for issue in models.BoatIssue.objects.filter(notified = False):
            try:
                c = Context({ 'issue': issue})
                payload = t.render(c)
                sbj = '[SVPB] Schadensmeldung - ' + issue.boat.type.name + " \"" + issue.boat.name + "\"" 
                self.stdout.write('From: ' +  settings.DEFAULT_FROM_EMAIL)
                self.stdout.write('To:  bommel@svpb.de, conger@svpb.de')                
                self.stdout.write('Subject: ' + sbj)
                self.stdout.write('Content:\n\r' + payload)
                
                mail.send(
                            ["bommel@svpb.de", "conger@svpb.de", issue.reported_by.email], 
                            settings.DEFAULT_FROM_EMAIL,
                            subject=sbj,                  
                            html_message=payload,
                            )
            
                issue.notified = True
                issue.save()
            except:
                print("Unexpected error ")  

        call_command('send_queued_mail')

        translation.deactivate()