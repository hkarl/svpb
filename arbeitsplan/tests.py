"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client

class SimpleTest(TestCase):
    fixtures=['arbeitsplan/fixtures/arbeitsplan.json',
              'arbeitsplan/fixtures/groups.json',
              'arbeitsplan/fixtures/user.json',
              'arbeitsplan/fixtures/post_office.json',
              ]

    plainpassword = "abc"
    def setUp(self):
        """
        Rewrite the passwords for the testusers
        """

        for u in User.objects.all():
            u.set_password(self.plainpassword)

    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

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

    def test_login_works(self):
        self.login_user('hkarl')

    def test_leistung_bearbeiten(self):
        """
        According to github report #14, lesitung bearbeiten fails. 
        """

        cl = self.login_user('JochenMelzian')
        response = cl.get('/arbeitsplan/leistungenBearbeiten/z=me/')
        self.assertEqual(response.status_code, 200)

        # and with some qualifiers:
        response = cl.get('/arbeitsplan/leistungenBearbeiten/z=me/?last_name=&first_name=&aufgabengruppe=3&von=&bis=&status=OF&status=RU&filter=Filter+anwenden')
        self.assertEqual(response.status_code, 200)


