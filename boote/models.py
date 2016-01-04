from django.db import models
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta


# Create your models here.

class BoatType(models.Model):
    name = models.CharField(max_length=30)
    url = models.CharField(max_length=256)
    length = models.CharField(max_length=15)
    beam = models.CharField(max_length=15)
    draught = models.CharField(max_length=15)


class Boat(models.Model):
    type = models.ForeignKey(BoatType)
    name = models.CharField(max_length=30)
    resp_name = models.CharField(max_length=30, null=True)
    resp_email = models.CharField(max_length=30, null=True)
    resp_tel = models.CharField(max_length=30, null=True)
    remarks = models.CharField(max_length=2000, null=True)
    booking_remarks = models.CharField(max_length=2000, null=True)

    def getBookings7days(self):
        "This function delivers list that describes bookings for upcoming 7 days (0 for free, 1 for partially booked, 2 for fully booked)"
        d1 = datetime.now()
        d2 = d1 + timedelta(days=7)
        result = [0, 0, 0, 0, 0, 0, 0]
        for booking in Booking.objects.filter(boat=self, date__lte=d2, date__gte=d1, status=1):
            offset = (booking.date - d1.date()).days
            result[offset] = 1
        return result

    def getDetailedBookings7Days(self):
        res = [[0 for x in range(22)] for x in range(7)]
        d1 = datetime.now()
        d2 = d1 + timedelta(days=7)
        for booking in Booking.objects.filter(boat=self, date__lte=d2, date__gte=d1, status=1):
            offset = (booking.date - d1.date()).days
            startIdx = (booking.time_from.hour-8)*2+(booking.time_from.minute/30)
            endIdx = (booking.time_to.hour-8)*2+(booking.time_to.minute/30)
            for i in range(startIdx, endIdx):
                res[offset][i] = 1
        return res
    
    def getNumberOfIssues(self):
        return BoatIssue.objects.filter(boat=self, status=1).count()
        
class Booking(models.Model):
    user = models.ForeignKey(User)
    created_date = models.DateField(default=datetime.now)
    boat = models.ForeignKey(Boat)
    status = models.IntegerField(default=1)
    date = models.DateField()
    time_from = models.TimeField()
    time_to = models.TimeField()

class BoatIssue(models.Model):
    boat = models.ForeignKey(Boat)
    status = models.IntegerField(default=1)
    reported_by = models.ForeignKey(User,related_name="user_reporting")
    reported_date = models.DateField()
    reported_descr = models.CharField(max_length=2000)
    fixed_by = models.ForeignKey(User,related_name="user_fixing", null=True)
    fixed_date = models.DateField(null=True)
    fixed_descr = models.CharField(max_length=2000, null=True)
    
