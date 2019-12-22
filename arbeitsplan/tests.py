"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from django.core.mail import outbox

from arbeitsplan.models import *

from pprint import pprint as pp

class SimpleTest(TestCase):
    fixtures=['arbeitsplan/fixtures/testdata/arbeitsplan.json',
              'arbeitsplan/fixtures/testdata/groups.json',
              'arbeitsplan/fixtures/testdata/user.json',
              'arbeitsplan/fixtures/testdata/po.json',
              ]

    # in fixture, all users should have this password:
    plainpassword = "abc"
    superuser = "su"

    def meldungOnlyOne(self):
        """
        Ensure integrity of Meldung:
        for any user/aufgabe combination, there must
        be AT MOST one meldung
        """

        for u in User.objects.all():
            for a in Aufgabe.objects.all():
                pass
        
    def setUp(self):
        """
        Rewrite the passwords for the testusers
        """
        # not necessary; fixture has been adapted so
        # that all users have same password (hopefully!)

        # u = User.objects.get(username="hkarl")
        # u.set_password(self.plainpassword)
        # u.save()
        pass

    def login_user(self, user):

        cl = Client()
        response = cl.post(
            '/login/',
            {'username': user,
             'password': self.plainpassword},
            follow=True,
            )

        self.assertTrue(response.status_code == 200)

        return cl, response

    def test_login_works(self):
        cl, response = self.login_user(self.superuser)

    def test_leistung_bearbeiten(self):
        """
        According to github report #14, lesitung bearbeiten fails.
        Problem not really clear from the description, however? :-(
        """

        cl, response = self.login_user(self.superuser)
        response = cl.get('/arbeitsplan/leistungenBearbeiten/z=me/')
        self.assertEqual(response.status_code, 200)

        # and with some qualifiers:
        response = cl.get('/arbeitsplan/leistungenBearbeiten/z=me/?last_name=&first_name=&aufgabengruppe=3&von=&bis=&status=OF&status=RU&filter=Filter+anwenden')
        self.assertEqual(response.status_code, 200)

    def _test_changes_in_stundenplan(self):
        cl, response = self.login_user(self.superuser)
        response = cl.get('/arbeitsplan/stundenplaene/6/')
        # print response
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
                        # print c
                        for d in tmp[:-1]:
                            # print d
                            d.delete()

            problem2 = self.check_stundenplaene_unique()

            if problem2:
                print("Problem persisted after clean up - giving up")
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
        """is there any process by which studneplaene entries become duplicates?
        Make a change to an Aufgabe Stundenplan

        TODO: not clear how to really do a post here with acceptable overhead
        for writing the test
        """

        # the database better be ok before we test this:
        problem = self.check_stundenplaene_unique()
        self.assertFalse(problem)

        cl, response = self.login_user(self.superuser)
        response = cl.get('/arbeitsplan/aufgabeEditieren/7/')
        self.assertEqual(response.status_code, 200)

        pp(response.context, indent=4)

        ## cl.post('/arbeitsplan/aufgabeEditieren/7/',
        ##         )
        self.assertTrue(True)


    def test_zuteilung_email(self):
        """do the zuteilung emails look right?"""

        # make sure there is at least a single user with a zuteilung_noetig true

        u = Mitglied.objects.get(mitgliedsnummer="00003")
        u.zuteilungBenachrichtigungNoetig = True
        u.save()

        cl, response = self.login_user("su")
        self.assertEqual(response.status_code, 200)

        response = cl.get("/arbeitsplan/benachrichtigen/zuteilung/",
                          follow=True)
        self.assertEqual(response.status_code, 200)
        
        # the user's email must appear in the response page:
        self.assertContains(response, u.user.email, html=False)

        # print response.content

        # do we have the dicts available?
        # print "REQUEST"
        # print response.request
        # print "---------------------"
        # pp (response.context[-1])
        
        # let's generate the email
        response = cl.post("/arbeitsplan/benachrichtigen/zuteilung/",
                           {'eintragen': 'Benachrichtigungen eintragen',
                            'sendit_2': 'on',
                            'ergaenzung': 'ergaenzungtest',
                            'anmerkung_2': 'anmerkungtest'},
                           follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(outbox), 0)

        # and actually send it off:

        # TODO: check how to deal with post_office based mai handling
        #
        # response = cl.get("/arbeitsplan/benachrichtigen/senden/",
        #                   follow=True)
        #
        # self.assertEqual(len(outbox), 1)
        # print outbox[0]

