"""Run tests on mitglieder adminstration
"""

from django.test import TestCase
from django.test import Client

from django.contrib.auth.models import User

from pprint import pprint as pp

class MitgliederTest(TestCase):
    # we onyl need the Vorstand group fixture

    fixtures=[
      'arbeitsplan/fixtures/testdata/arbeitsplan.json',
      'arbeitsplan/fixtures/testdata/groups.json',
      'arbeitsplan/fixtures/testdata/user.json',
    ]

    plainpassword = "abc"


    def login_user(self, user):

        cl = Client()
        response = cl.post(
            '/login/',
            {'username': user,
             'password': self.plainpassword}
            )

        pp(response)

        self.assertTrue(response.status_code == 200 or
                        response.status_code == 302)
        return cl


    def _test_login_works(self):
        self.login_user('hkarl')

    def test_add_user(self):
        print "adding user"

        cl = self.login_user('hkarl')

        print "adding"

        response = cl.get(
                '/accounts/add/')

        print "response after get:"
        pp(response)

        response = cl.post(
            '/accounts/add/',
            {'firstname': 'Peter',
             'lastname': 'Pan',
             'email': 'peter@pan.com',
             'mitgliedsnummer': '666666',
             'strasse': 'Testweg',
             'plz': '12345',
             'ort': 'Teststadt',
             },
        )

        print "response:"
        pp(response)

        # check wether user exists:
        try:
            u = User.objects.get(username='666666')
        except User.DoesNotExist:
            print "user Peter Pan not created"
        except Exception as e:
            print "When creating PeterPan: ", e


