
"""
This seems to be necessary to allow access to constants in settings.py.

see: http://chriskief.com/2013/09/19/access-django-constants-from-settings-py-in-a-template/
"""

from django.conf import settings
 
 
def global_settings(request):
    # return any necessary values
    return {
        'OFFLINE': settings.OFFLINE,
    }
