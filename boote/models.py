from django.db import models
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta
#from django.core.files.storage import FileSystemStorage

import uuid

#image_storage = FileSystemStorage(location='/static/boote/boat_gallery')

# Create your models here.

class BoatType(models.Model):
    name = models.CharField(max_length=30)
    url = models.CharField(max_length=256)
    length = models.CharField(max_length=15)
    beam = models.CharField(max_length=15)
    draught = models.CharField(max_length=15)
    def __str__(self):
        return self.name

def boat_img_path(instance, filename):
    unique_filename = uuid.uuid4()
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'boats_gallery/{1}{2}'.format(instance.pk, unique_filename, filename[-4:])



class Boat(models.Model):
    owner = models.ForeignKey(User,
                    on_delete=models.PROTECT
                    # not really sure what to do with a boat when owner is deleted? TODO
                                  )
    
    type = models.ForeignKey(BoatType,
                    on_delete=models.PROTECT,
                    # cannot delete a boat type as long as there are boats of it
                    )
                    
    photo = models.ImageField(upload_to=boat_img_path, null=True)
    name = models.CharField(max_length=30)
    active = models.BooleanField(default=True)
    briefing = models.CharField(max_length=2000, null=True, default='')
    remarks = models.CharField(max_length=2000, null=True)
    club_boat = models.BooleanField(default=False)
    booking_remarks = models.CharField(max_length=2000, null=True, default='')     
    
    def getBookings7days(self):
        "This function delivers list that describes bookings for upcoming 7 days (0 for free, 1 for partially booked, 2 for fully booked)"
        d1 = datetime.now()
        d2 = d1 + timedelta(days=6)
        result = [0, 0, 0, 0, 0, 0, 0]
        for booking in Booking.objects.filter(boat=self, date__lte=d2, date__gte=d1, status=1):
            offset = (booking.date - d1.date()).days
            result[offset] = 1
        return result

    def getDetailedBookingsToday(self):
        print(self.name)
        res = [['', '', ''] for x in range(28)] 
        d1 = datetime.now().replace(hour=7, minute=0)
        d2 = d1.replace(hour=21)
        print(d1, ' do ' , d2)
        for booking in Booking.objects.filter(boat=self, date__lte=d2, date__gte=d1, status=1):            
            uid = booking.user.username
            usertag = booking.user.first_name + " " + booking.user.last_name              
            startIdx = round((booking.time_from.hour-8)*2+(booking.time_from.minute/30))
            endIdx = round((booking.time_to.hour-8)*2+(booking.time_to.minute/30))
            for i in range(max(0, startIdx), min(28, endIdx)):
                res[i] = [uid, usertag, booking.type]
        return res
    
    def getDetailedBookings7Days(self):
        res = [[[0,''] for x in range(28)] for x in range(7)]
        d1 = datetime.now()
        d2 = d1 + timedelta(days=6)
        for booking in Booking.objects.filter(boat=self, date__lte=d2, date__gte=d1, status=1):
            offset = (booking.date - d1.date()).days
            uid = booking.user.username 
            startIdx = round((booking.time_from.hour-8)*2+(booking.time_from.minute/30))
            endIdx = round((booking.time_to.hour-8)*2+(booking.time_to.minute/30))
            for i in range(max(0, startIdx), min(28, (endIdx))):
                res[offset][i] = [uid, booking.type]
        return res
    
    def getNumberOfIssues(self):
        return BoatIssue.objects.filter(boat=self, status=1).count()
        
class Booking(models.Model):
    user = models.ForeignKey(User,
                on_delete=models.CASCADE)
    created_date = models.DateField(default=datetime.now)
    boat = models.ForeignKey(Boat,
                on_delete=models.CASCADE)
    status = models.IntegerField(default=1)
    type = models.CharField(max_length=3, choices=(('PRV', 'Freie Nutzung'), ('AUS', 'Ausbildung'), ('REG', 'Regatta'),), default='PRV')
    date = models.DateField()
    time_from = models.TimeField()
    time_to = models.TimeField()
    notified = models.BooleanField(default=False)

class BoatIssue(models.Model):
    boat = models.ForeignKey(Boat,
                on_delete=models.CASCADE)
    status = models.IntegerField(default=1)
    reported_by = models.ForeignKey(User,
                        related_name="user_reporting",
                        on_delete=models.PROTECT,
                        # probably not a good idea to delete issue until it is resolved,
                        # might want to talk to the reporter of the issue
                        )
    reported_date = models.DateField()
    reported_descr = models.CharField(max_length=2000)
    fixed_by = models.ForeignKey(User,
                    on_delete=models.SET_NULL,
                    related_name="user_fixing", null=True)
    fixed_date = models.DateField(null=True)
    fixed_descr = models.CharField(max_length=2000, null=True)
    notified = models.BooleanField(default=False)
