from django import forms
from datetime import datetime, timedelta
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Hidden, HTML
from crispy_forms.bootstrap import (
    PrependedText, PrependedAppendedText, FormActions)
from crispy_forms.bootstrap import TabHolder, Tab
from django.core.exceptions import ValidationError
from gc import disable
from .models import Booking, Boat
import StringIO
from .custom_widgets import AdvancedFileInput
from PIL import Image


import locale
locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")


TIME = []
TIME.append(["-","-"])
TIME.append(["08:00","08:00"])
TIME.append(["08:30","08:30"])
TIME.append(["09:00","09:00"])
TIME.append(["09:30","09:30"])
TIME.append(["10:00","10:00"])
TIME.append(["10:30","10:30"])
TIME.append(["11:00","11:00"])
TIME.append(["11:30","11:30"])
TIME.append(["12:00","12:00"])
TIME.append(["12:30","12:30"])
TIME.append(["13:00","13:00"])
TIME.append(["13:30","13:30"])
TIME.append(["14:00","14:00"])
TIME.append(["14:30","14:30"])
TIME.append(["15:00","15:00"])
TIME.append(["15:30","15:30"])
TIME.append(["16:00","16:00"])
TIME.append(["16:30","16:30"])
TIME.append(["17:00","17:00"])
TIME.append(["17:30","17:30"])
TIME.append(["18:00","18:00"])
TIME.append(["18:30","18:30"])
TIME.append(["19:00","19:00"])

DURATION = []
DURATION.append(["-","-"])
DURATION.append(["60","1 Stunde"])
DURATION.append(["90","1.5 Stunden"])
DURATION.append(["120","2 Stunden"])

BOOKING_TYPE = []
BOOKING_TYPE.append(['AUS', 'Ausbildung'])
BOOKING_TYPE.append(['REG', 'Regatta'])

MONTHS= []
MONTHS.append(['01','Januar'])
MONTHS.append(['02','Februar'])
MONTHS.append(['03','Maerz'])
MONTHS.append(['04','April'])
MONTHS.append(['05','Mai'])
MONTHS.append(['06','Juni'])
MONTHS.append(['07','Juli'])
MONTHS.append(['08','August'])
MONTHS.append(['09','September'])
MONTHS.append(['10','Oktober'])
MONTHS.append(['11','November'])
MONTHS.append(['12','Dezember'])

DAYS = []
for i in range(1,10):
    DAYS.append(['0'+str(i),'0'+str(i)])
for i in range(10,32):
    DAYS.append([str(i),str(i)])

    
class NewReservationForm(forms.Form):
    
    res_date = forms.ChoiceField(label="Datum",required=True, widget=forms.Select(attrs={"onChange":'showbooking()'}), choices=[])
    res_start = forms.ChoiceField(label="Von",required=True, widget=forms.Select(attrs={"onChange":'showbooking()'}), choices=TIME)
    res_duration = forms.ChoiceField(label="Dauer",required=True, widget=forms.Select(attrs={"onChange":'showbooking()'}), choices=DURATION)
        
    accepted_datenschutz = forms.BooleanField(label="Ich akceptiere, dass meine Name fur die Reservation sichtbar fur anderen Mitgliedern ist.", required=True)
    
    accepted_agb = forms.BooleanField(label="Ich akceptiere <a href='/static/boote/AlgemRegelnVereinsboote.pdf' target='_blank'>Allgemeine Regeln zur Nutzung der Vereinsboote</a>.", required=True)
    
    def __init__(self, *args, **kwargs):
        super(NewReservationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-reservation-form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'POST'

        # initialize DATES   
        DATES = []
        d = datetime.now()
        for i in range(1,8):
            d = d + timedelta(days=1)
            DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%d. %b)")])
        self.fields['res_date'] = forms.ChoiceField(label="Datum",required=True, widget=forms.Select(attrs={"onChange":'showbooking()'}), choices=DATES)

        self.helper.add_input(Submit('submit', 'Verbindlich reservieren'))
        
        
    def clean(self):
        import re
        
        cleaned_data = super(NewReservationForm, self).clean()
        
        # check date and time
        try:
            res_date = cleaned_data['res_date']
            res_start = cleaned_data['res_start']        
        except KeyError:
            res_date = ''
            res_start =''
             
        try:
            start = datetime.strptime(res_date + " " + res_start, '%Y-%m-%d %H:%M')
        except ValueError:
            raise forms.ValidationError("Bitte Datum und Uhrzeit auswaehlen.")
        
        # check duration
        res_duration = cleaned_data['res_duration']
        try:
            res_duration = int(res_duration)
        except ValueError:
            raise forms.ValidationError("Bitte Dauer auswaehlen.")
        
        if (res_duration<30):
            raise forms.ValidationError("Minimale Reservation von 30 Minuten moeglich.")
        if (res_duration>120):
            raise forms.ValidationError("Maximal 2 Stunden Reservation moeglich.")
        
        end = start + timedelta(0,0,0,0,res_duration) # minutes                        
        res_end =  end            
                    
class NewClubReservationForm(forms.Form):       
    club_boats = Boat.objects.filter(club_boat='true')
    CBOATS = []
    for cb in club_boats:
        CBOATS.append([cb.pk,cb.name + " (" + cb.type.name + ")"])  
    
    res_type = forms.ChoiceField(label="Reservations-Typ",required=True, widget=forms.Select(), choices=BOOKING_TYPE)
    res_boat = forms.ChoiceField(label="Vereinsboot",required=True, widget=forms.Select(), choices=CBOATS)
    res_month = forms.ChoiceField(label="Monat",required=True, widget=forms.Select(), choices=MONTHS)
    res_day = forms.ChoiceField(label="Tag des Monats",required=True, widget=forms.Select(), choices=DAYS)
    res_start = forms.ChoiceField(label="Von",required=True, widget=forms.Select(), choices=TIME, initial='08:00')
    res_end = forms.ChoiceField(label="Bis",required=True, widget=forms.Select(), choices=TIME, initial='19:00')
    
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-reservation-form-club'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'POST'

        self.helper.add_input(Submit('submit', 'Termin speichern'))
        super(NewClubReservationForm, self).__init__(*args, **kwargs)
        
    def clean(self):
        import re
        
        cleaned_data = super(NewClubReservationForm, self).clean()
        
        # check date and time
        now = datetime.now()
        res_year = now.year
        res_month = cleaned_data['res_month']
        res_day = cleaned_data['res_day']
        res_start = cleaned_data['res_start']
        res_end = cleaned_data['res_end']              
        
        res_date=str(res_year) + "-" + res_month + "-"+ res_day
         
        try:            
            start = datetime.strptime(res_date + " " + res_start, '%Y-%m-%d %H:%M')
        except ValueError:
            raise forms.ValidationError("Bitte Datum und Uhrzeit auswaehlen.")
        
        try:
            start = datetime.strptime(res_date + " " + res_start, '%Y-%m-%d %H:%M')
        except ValueError:
            raise forms.ValidationError("Bitte Datum und Start-Uhrzeit auswaehlen.")
        try:
            end = datetime.strptime(res_date + " " + res_end, '%Y-%m-%d %H:%M')
        except ValueError:
            raise forms.ValidationError("Bitte Datum und End-Uhrzeit auswaehlen.")
        
        if start>=end:
            raise forms.ValidationError("End muss nach dem Start sein.")
        

class BootIssueForm(forms.Form):    
    res_reported_descr = forms.CharField(label="Beschreibung",required=True,widget= forms.Textarea)    
    
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-boot-issue'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'POST'

        self.helper.add_input(Submit('submit', 'Speichern'))
        super(BootIssueForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(BootIssueForm, self).clean()
        res_reported_descr = cleaned_data.get("res_reported_descr")
        
        
class BootEditForm(forms.ModelForm):    

    def __init__(self, *args, **kwargs):
        super(BootEditForm, self).__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_id = 'id-boot-edit'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'POST'

        self.helper.add_input(Submit('submit', 'Speichern'))
                
        self.helper.layout = Layout(
            TabHolder(
                    Tab(
                          'Hauptinformationen',
                          'type',
                          'name',
                          'remarks',                          
                          
                    ),
                    Tab(
                          'Bild',
                          'photo',
                    ),
                    Tab(
                          'Bootspate',                              
                          Field('resp_name', placeholder="Vorname Nachname"),
                          PrependedText('resp_email', '@', placeholder="z.B. some@email.com"),
                          Field('resp_tel', placeholder="z.B. 0171 554 5522"),
                          
                    ),   
                    Tab(
                          'Reservationen',
                          'club_boat',
                          'booking_remarks'
                    ),
            )
        ) 
        
        self.fields['booking_remarks'].required = False
        self.fields['booking_remarks'].label = "Wichtige Hinweise (Reservation)"
        
        self.fields['club_boat'].label = "Vereinsboot"
        
        self.fields['photo'].required = False
        self.fields['photo'].label = "Bild (Format: JPG)"
         
        self.fields['resp_name'].label = "Bootspate"
        self.fields['resp_email'].label = "Email"
        self.fields['resp_tel'].label = "Telefonnummer"
        

    def clean(self):
        cleaned_data = super(BootEditForm, self).clean()
        
        # scale image        
        image_field = self.cleaned_data.get('photo')
        if image_field:
            image_file = StringIO.StringIO(image_field.read())
            image = Image.open(image_file)
            w, h = image.size

            image = image.resize((400, 400*h/w), Image.ANTIALIAS)

            image_file = StringIO.StringIO()
            image.save(image_file, 'JPEG', quality=90)

            image_field.file = image_file        
    
    class Meta:
        model = Boat
        exclude = ('owner',)
        widgets = {
          'remarks': forms.Textarea(attrs={'rows':4, 'cols':15}),
          'booking_remarks': forms.Textarea(attrs={'rows':4, 'cols':15}),
          'photo': AdvancedFileInput()          
        }
               
