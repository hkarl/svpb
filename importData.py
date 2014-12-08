

# remember to set:
# export DJANGO_SETTINGS_MODULE=svpb.settings

import datetime
from pprint import pprint as pp

import sys
import codecs, json


import django
from django.core.exceptions import ObjectDoesNotExist

import svpb
from arbeitsplan.models import User, Mitglied


django.setup()

importfile = "backup/kids.json"

f = codecs.open(importfile, "r", encoding="utf")
dicts = json.load(f)


# see whether we should add these values now to the data base

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_mitglied(sender, instance, created, **kwargs):
    print "creating mitglied", sender, created
    if created:
        Mitglied.objects.create(user=instance)


for d in dicts:
    print "importing: ", d['Name'], d['E-Mail'], d['mnr']

    # try to find a mitglied with that ID as mitgliedsnummer 

    tocreate = False
    
    try:
        m = Mitglied.objects.get(mitgliedsnummer=d['mnr'])

        print "this user already exsits, no further steps taken"

    except ObjectDoesNotExist:
        tocreate = True

    if tocreate:
        try:
            u = User(
                first_name=d['Vorname'],
                last_name=d['Name'],
                is_active=False,
                username=d['id'],
                email=d['E-Mail'],
                )

            u.set_password(d['pw'])
            u.save()

            print "created user ", u.id, u.pk, type(u)

            m = u.mitglied

            print "mitglied", m, type(m)

            print datetime.datetime.strptime(d['Geburtsdatum'], "%Y-%m-%d")
            m.geburtsdatum= datetime.datetime.strptime(d['Geburtsdatum'], "%Y-%m-%d")
            m.mitgliedsnummer=d['id']
            m.ort=d['Ort']
            m.plz=d['PLZ']
            m.strasse=d['Strasse']
            m.gender=d['gender']
            m.status=d['Mitgliedsstatus']


            print m
            
            m.save()
            u.save()
        except Exception as e:
            print 'eeror Mitglied: ', e, d



