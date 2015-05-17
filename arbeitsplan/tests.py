"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from arbeitsplan.models import *

from pprint import pprint as pp

class SimpleTest(TestCase):
    fixtures=['arbeitsplan/fixtures/testdata/arbeitsplan.json',
              'arbeitsplan/fixtures/testdata/groups.json',
              'arbeitsplan/fixtures/testdata/user.json',
              'arbeitsplan/fixtures/testdata/post_office.json',
              ]

    plainpassword = "abc"
    def setUp(self):
        """
        Rewrite the passwords for the testusers
        """
        # for u in User.objects.all():
        #     u.set_password(self.plainpassword)

    def login_user(self, user):

        cl = Client()
        response = cl.post(
            '/accounts/login/',
            {'username': user,
             'password': self.plainpassword}
            )

        self.assertTrue(response.status_code == 200 or
                        response.status_code == 302)
        return cl

    def _test_login_works(self):
        self.login_user('hkarl')

    def _test_leistung_bearbeiten(self):
        """
        According to github report #14, lesitung bearbeiten fails. 
        """

        cl = self.login_user('JochenMelzian')
        response = cl.get('/arbeitsplan/leistungenBearbeiten/z=me/')
        self.assertEqual(response.status_code, 200)

        # and with some qualifiers:
        response = cl.get('/arbeitsplan/leistungenBearbeiten/z=me/?last_name=&first_name=&aufgabengruppe=3&von=&bis=&status=OF&status=RU&filter=Filter+anwenden')
        self.assertEqual(response.status_code, 200)

    def _test_changes_in_stundenplan(self):
        cl = self.login_user('JochenMelzian')
        response = cl.get('/arbeitsplan/stundenplaene/6/')
        print response
        self.assertEqual(response.status_code, 200)


    def check_stundenplaene_unique(self):
        problem = False

        for a in Aufgabe.objects.all():
            s = Stundenplan.objects.filter(aufgabe=a)
            for u in range(8,24):
                s2 = s.filter(uhrzeit=u)
                c = s2.count()
                if c>1:
                    problem = True
                    ## print a, u, s2.count()
                    ## print [x.anzahl for x in s2]

        return problem

    def _test_stundenplaene_unique(self):
        """for all comubinations of Aufgabe and uzhrzeit,
        there must be at most ONE entry in stundenplaene"""

        problem1 = self.check_stundenplaene_unique()

        # try to kick out all the redundant combiantions:
        if problem1:
            for a in Aufgabe.objects.all():
                for u in range(8,24):
                    s = Stundenplan.objects.filter(aufgabe=a).filter(uhrzeit=u)
                    c = s.count()
                    if c > 1:
                        tmp = [x for x in s]
                        print c
                        for d in tmp[:-1]:
                            print d
                            d.delete()

            problem2 = self.check_stundenplaene_unique()

            if problem2:
                print "Problem persisted after clean up - giving up"
                self.assertFalse(problem2)
            else:
                # dumping the sanitized data
                from django.core.management import call_command
                output = open("sanitized.json", "w")
                call_command('dumpdata', 'arbeitsplan', format='json',
                             indent=3, stdout=output)
                output.close()

        self.assertFalse(False)

    def _test_stundenplaene_duplicates(self):
        """is there any process by which studneplaene entires become duplicates?
        Make a change to an Aufgabe Stundenplan

        TODO: not clear how to really do a post here with acceptable overhead
        for writing the test
        """

        # the database better be ok before we test this:
        problem = self.check_stundenplaene_unique()
        self.assertFalse(problem)

        cl = self.login_user('JochenMelzian')
        response = cl.get('/arbeitsplan/aufgabeEditieren/7/')
        self.assertEqual(response.status_code, 200)

        pp(response.context, indent=4)

        ## cl.post('/arbeitsplan/aufgabeEditieren/7/',
        ##         )
        self.assertTrue(True)


    def _test_zuteilung_email(self):
        """do the zuutliung emails look right?"""

        # make sure there is at least a single user with a zuteilung_noetig true

        u = User.objects.first()
        u.mitglied.zuteilungBenachrichtigungNoetig = True
        u.mitglied.save()

        cl = self.login_user("hkarl")
        response = cl.get("/arbeitsplan/benachrichtigen/zuteilung/")
        self.assertEqual(response.status_code, 200)
        
        # the user's email must appear in the response page:
        self.assertContains(response, u.email, html=False)

        # do we have the dicts available?
        print "REQUEST"
        print response.request
        print "---------------------"
        print response.context
        
        # let's generate the email
        response = cl.post("/arbeitsplan/benachrichtigen/zuteilung/",
                           {'eintragen': 'Benachrichtigungen eintragen',
                            'sendit_4': 'on'})

        # print response
        self.assertEqual(response.status_code, 302)
