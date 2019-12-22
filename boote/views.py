from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from datetime import datetime, timedelta
import time 
from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render
from .models import Boat, BoatType, Booking, BoatIssue
# from django.core.urlresolvers import reverse
from django.urls import reverse
from django.shortcuts import redirect
from django.db.models import Q
from .forms import NewReservationForm, NewClubReservationForm, BootIssueForm, BootEditForm
from django.core.mail import send_mail, BadHeaderError
from django.core.mail import EmailMessage

def booking_today(request):
    template = loader.get_template('boote/booking_today.html')

    user = request.user

    overview = []
    for boat in Boat.objects.filter(club_boat = True, active = True):
        overview.append([boat.name, boat.type.name, boat.pk, boat.getBookings7days()])
 
    bookings_today = Booking.objects.filter(date=datetime.now(), status='1').order_by('date')
    
    bookings = []
    for boat in Boat.objects.filter(club_boat = True, active = True):
        bookings.append([boat, boat.getDetailedBookingsToday])

    dates = []
    d = datetime.now()
    for i in range(0, 7):
        dates.append([d.strftime("%A"), d.strftime("%d. %b")])
        d = d + timedelta(days=1)

    context = RequestContext(request, 
                            {'booking_overview': overview, 
                             "booking_dates": dates, 
                             "bookings": bookings, 
                             'date': datetime.now().strftime("%A, %d. %b"),
                             })
    
    return HttpResponse(template.render(context))

def booking_overview(request):
    template = loader.get_template('boote/booking_overview.html')

    user = request.user

    overview = []
    for boat in Boat.objects.filter(club_boat = True, active = True):
        overview.append([boat.name, boat.type.name, boat.pk, boat.getBookings7days()])
 
    bookings_today = Booking.objects.filter(date=datetime.now(), status='1').order_by('date')
    
    bookings = []
    for boat in Boat.objects.filter(club_boat = True, active = True):
        bookings.append([boat, boat.getDetailedBookingsToday])

    dates = []
    d = datetime.now()
    for i in range(0, 7):
        dates.append([d.strftime("%A"), d.strftime("%d. %b")])
        d = d + timedelta(days=1)

    context = RequestContext(request, 
                            {'booking_overview': overview, 
                             "booking_dates": dates, 
                             "bookings": bookings, 
                             'date': datetime.now().strftime("%A"),
                             })
    
    return HttpResponse(template.render(context))

def booking_training_public(request):
    template = loader.get_template('boote/booking_traning.html')
    
    bookings_train = Booking.objects.filter(status=1, type='AUS', date__gte=datetime.now()).order_by('date')
   
    context = RequestContext(request, {"bookings":bookings_train, 'date': datetime.now()})
    
    return HttpResponse(template.render(context))


def booking_today_public(request):
    template = loader.get_template('boote/booking_today_public.html')
    
    bookings_today = Booking.objects.filter(date=datetime.now(), status='1').order_by('date')
    
    bookings = []
    for boat in Boat.objects.filter(club_boat = True):
        bookings.append([boat, boat.getDetailedBookingsToday])
    
    context = RequestContext(request, {"bookings":bookings, 'date': datetime.now()})
    
    return HttpResponse(template.render(context))


def booking_all(request):
    template = loader.get_template('boote/booking_all.html')

    user = request.user

    bookings = []
    for booking in Booking.objects.filter().order_by('-date'):
        bookings.append([booking, booking.date.strftime("%A"), booking.date.strftime("%Y %b %d"), booking.time_from.strftime("%H:%M"), booking.time_to.strftime("%H:%M")])
  
    context = RequestContext(request, {
        "bookings": bookings,        
        })
    return HttpResponse(template.render(context))

def booking_my_bookings(request):
    template = loader.get_template('boote/booking_my_bookings.html')

    user = request.user

    mybookings = []
    for booking in Booking.objects.filter(user=user, status=1, type='PRV', date__gte=datetime.now()).order_by('date'):
        mybookings.append([booking.user, booking.created_date, booking.date.strftime("%A"), booking.date.strftime("%Y/%d/%m"), booking.time_from.strftime("%H:%M"), booking.time_to.strftime("%H:%M"), booking.boat, booking.pk])
  
    context = RequestContext(request, {
        "mybookings": mybookings,        
        })
    return HttpResponse(template.render(context))

def boot_liste(request):
    template = loader.get_template('boote/boot_liste.html')

    user = request.user
    
    boots_verein = []
    for boat in Boat.objects.filter(club_boat = True, active = True).order_by('-type'):
        boots_verein.append([boat, boat.getNumberOfIssues])
    
    boots_andere = []
    for boat in Boat.objects.filter(club_boat = False, active = True).order_by('-type'):
        boots_andere.append([boat])
        
    context = RequestContext(request, {'boots_verein': boots_verein,'boots_andere': boots_andere})
    
    return HttpResponse(template.render(context))

def boot_detail(request, boot_pk):
    template = loader.get_template('boote/boot_detail.html')
    boat = Boat.objects.get(pk=boot_pk)
    user = request.user    
    ismyboat = (user == boat.owner)
    for g in user.groups.all():
        if g.name == "Vorstand":
            ismyboat = True
    
    numIssues = boat.getNumberOfIssues
    
    context = RequestContext(request, {        
        'boot': boat,
        'user': user,
        'ismyboat': ismyboat,
        'numIssues' : numIssues
    })
    
    return HttpResponse(template.render(context))


def booking_boot(request, boot_pk):
    template = loader.get_template('boote/booking_boot.html')
    boot = Boat.objects.get(pk=boot_pk)
    user = request.user
        
    bookings = Boat.getDetailedBookings7Days(boot)
    overview = []
    d = datetime.now()
    for i in range(0, 7):
        overview.append([d.strftime("%A"), d.strftime("%d. %b"), bookings[i]])
        d = d + timedelta(days=1)
   
    error_list=[]
    
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        
        # create a form instance and populate it with data from the request:
        form = NewReservationForm(request.POST)        
        
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            res_date = form.cleaned_data['res_date']
            res_start = form.cleaned_data['res_start']
            res_duration = form.cleaned_data['res_duration']
            res_duration = int(res_duration)
            
            start = datetime.strptime(res_date + " " + res_start, '%Y-%m-%d %H:%M')
            end = start + timedelta(0, 0, 0, 0, res_duration) # minutes                        
            res_end =  end            

            # check if dates overlapping
            if (Booking.objects.filter(boat=boot, date=res_date, status=1, time_from__lte=res_start, time_to__gt=res_start)):
                error_list.append("Dein Termin startet in anderen besezten Termin");
            if (Booking.objects.filter(boat=boot, date=res_date, status=1, time_from__lt=res_end, time_to__gt=res_end)):
                error_list.append("Dein Termin endet in anderen besezten Termin");
            if (Booking.objects.filter(boat=boot, date=res_date, status=1, time_from__gte=res_start, time_to__lte=res_end)):
                error_list.append("Dein Termin ist schon besetzt mit anderen Termin");
                
            if (not error_list):
                # save new booking
                b = Booking(user=user, boat=boot, date=res_date, time_from=res_start, time_to=res_end)
                b.save()
                # redirect to a new URL:
                return HttpResponseRedirect(reverse('booking-my-bookings'))            

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NewReservationForm()
    
    context = RequestContext(request, {
        'error_list': error_list,        
        'form': form,        
        'boot': boot,
        'user': user,
        'booking_overview': overview,

    })
    return HttpResponse(template.render(context))

def booking_priority_boot_list(request):
    return booking_priority_boot(request, False)

def booking_priority_boot_new(request):
    return booking_priority_boot(request, True)

def booking_priority_boot(request, new_booking=False):
    template = loader.get_template('boote/booking_priority_boot.html')    
    
    user = request.user
    bookings_reg = Booking.objects.filter(status=1, type='REG', date__gte=datetime.now()).order_by('date')
    bookings_aus = Booking.objects.filter(status=1, type='AUS', date__gte=datetime.now()).order_by('date')
    d = datetime.now()    
   
    error_list=[]
    
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        
        # create a form instance and populate it with data from the request:
        form = NewClubReservationForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            res_boat = form.cleaned_data['res_boat']
            res_year = datetime.now().year
            res_month = form.cleaned_data['res_month']
            res_day = form.cleaned_data['res_day']
            res_start = form.cleaned_data['res_start']
            res_end = form.cleaned_data['res_end']     
            res_type = form.cleaned_data['res_type']
            
            # construct the res_date
            res_date=str(res_year) + "-" + res_month + "-"+ res_day
            
            # no checking for overlapping            
                
            if (not error_list):
                # save new booking
                for b in res_boat:
                    boot = Boat.objects.get(pk=b)
                    b = Booking(user=user, type=res_type, boat=boot, date=res_date, time_from=res_start, time_to=res_end)
                    b.save()
                
                # redirect to a new URL:
                return HttpResponseRedirect(reverse('priority-booking-boot-list'))            


    # if a GET (or any other method) we'll create a blank form
    else:        
        form = NewClubReservationForm()  
        
    
    
    context = RequestContext(request, {
        'error_list': error_list,        
        'form': form,
        'user': user,
        'edit': new_booking,
        'bookings_reg': bookings_reg,
        'bookings_aus': bookings_aus,

    })
    return HttpResponse(template.render(context))

def booking_remove(request, booking_pk):
    booking = Booking.objects. get(pk=booking_pk, user=request.user)
    booking.status=0
    booking.save()
    return redirect('booking-my-bookings')


def boot_issues_all(request):
    template = loader.get_template('boote/boot_issue_all.html')
    user = request.user
    issues = BoatIssue.objects.filter().order_by('-reported_date')
        
    context = RequestContext(request, {
        'user': user,
        'issues': issues,        
    })
    return HttpResponse(template.render(context))

def boot_issues(request, boot_pk):
    template = loader.get_template('boote/boot_issue.html')
    boot = Boat.objects.get(pk=boot_pk)
    user = request.user
    issues = BoatIssue.objects.filter(boat=boot_pk, )
    
    
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = BootIssueForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            res_reported_descr = form.cleaned_data['res_reported_descr']
            
            b = BoatIssue(boat=boot, status=1, reported_descr=res_reported_descr, reported_by=user, reported_date=datetime.now())
            b.save()
            # redirect to a new URL:
            return redirect('boot-issues', boot.pk)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = BootIssueForm()

    context = RequestContext(request, {
        'form_issue': form,
        'boot': boot,
        'user': user,
        'issues': issues,        
    })
    return HttpResponse(template.render(context))

def boot_fix_issue(request, issue_pk):
    issue = BoatIssue.objects.get(pk=issue_pk)
    issue.status = 2
    issue.fixed_by = request.user
    issue.fixed_date = datetime.now()
    issue.save()
    return redirect('boot-issues', issue.boat.pk)


def boot_edit_list(request):
    return boot_edit(request, 0, False)

def boot_edit_new(request):
    return boot_edit(request, 0, True, True)

def boot_edit(request, boot_pk, edit=True, new_boat=False):
    template = loader.get_template('boote/boot_edit.html')    
    user = request.user
    my_boats = Boat.objects.filter(owner=user)
    
    adminUser = False
    for g in user.groups.all():
        if g.name == "Vorstand":
            adminUser = True
            my_boats = Boat.objects.filter()
    
    
    # PROCESSING USER INPUT 
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:            
        form = BootEditForm(request.POST, request.FILES)            
        # check whether it's valid:
        if form.is_valid():            
            # process           
            if new_boat:
                boat = Boat()
                boat.owner = user
            else:
                if adminUser:
                    boat = Boat.objects.get(pk=boot_pk)
                else:                        
                    boat = Boat.objects.get(pk=boot_pk, owner=user)                                                 

            boat.type = form.cleaned_data['type']
            boat.name = form.cleaned_data['name']
            boat.active = form.cleaned_data['active']
            boat.remarks = form.cleaned_data['remarks']
            boat.briefing = form.cleaned_data['briefing']
            boat.club_boat = form.cleaned_data['club_boat']
            boat.booking_remarks = form.cleaned_data['booking_remarks']
            if form.cleaned_data['photo'] is not None:
                boat.photo = form.cleaned_data['photo']

            # persist in DB
            boat.save()

            # redirect to a new URL:
            return redirect('boot-detail', boat.pk)
        else:
            # error
            context = RequestContext(request, {
            'form_boot_edit': form,
            'edit': edit,                
            'my_boats': my_boats,
            'user': user,                
            })

            return HttpResponse(template.render(context))
    
    # CREATING USER QUERY / FORM 
    if edit == True:
        if new_boat:
            boat = Boat()
        else:
            if adminUser:
                boat = Boat.objects.get(pk=boot_pk)
            else:
                boat = Boat.objects.get(pk=boot_pk, owner=user)
            
        form = BootEditForm(instance = boat)    
                    
        context = RequestContext(request, {
                'form_boot_edit': form,
                'edit': edit,
                'boat': boat,
                'my_boats': my_boats,
                'user': user,                
                })
    else:
        context = RequestContext(request, {                
                'edit': edit,                
                'my_boats': my_boats,
                'user': user,                
                })
    return HttpResponse(template.render(context))
