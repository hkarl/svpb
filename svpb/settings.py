# Django settings for svpb project.

import os
## let's find the root from where the server runs: 
APPLICATION_DIR = os.path.dirname( globals()[ '__file__' ] )

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

LOGIN_URL = "/login/"

OFFLINE = False
JAHRESENDE = False

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'svpb.sq',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'UserPlaceholder',
        'PASSWORD': 'PasswordPlaceholder',
        'HOST': '127.0.0.1',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'de'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join (APPLICATION_DIR, '..', 'media')


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = 'media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # os.path.join (APPLICATION_DIR, '..', 'arbeitsplan', 'static'),
    os.path.join (APPLICATION_DIR, '..', 'boote', 'static'),
    os.path.join (APPLICATION_DIR, '..', 'templates'),
)


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '26w5_t=fcjff6vk9$ee(03xa&+1c($ot1ixg)p-f(%v#ad$dqy'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth', 
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'svpb.context_processors.global_settings', 
    ) 

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
)

IMPERSONATE_REDIRECT_URL = "/"

def user_is_vorstand(request):
    return request.user.groups.filter(name="Vorstand")
IMPERSONATE_CUSTOM_ALLOW = "svpb.settings.user_is_vorstand"


ROOT_URLCONF = 'svpb.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'svpb.wsgi.application'


TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join (APPLICATION_DIR, '../templates'), 
    os.path.join (APPLICATION_DIR, 'templates'),
    os.path.join (APPLICATION_DIR, '../mitglieder/templates'),
    os.path.join (APPLICATION_DIR, '../boote/templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    ## 'django_admin_bootstrapped.bootstrap3',
    ## 'django_admin_bootstrapped',
    'django.contrib.admin',
    'django_extensions',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'django_tables2',
    'crispy_forms',
    'impersonate',
    'arbeitsplan',
    'boote',
    'post_office',
    'sendfile',
    'password_reset',
    'django_select2',
)

CRISPY_TEMPLATE_PACK = "bootstrap3"


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

#####################
# Own settings:

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {message_constants.DEBUG: 'debug',
                message_constants.INFO: 'info',
                message_constants.SUCCESS: 'success',
                message_constants.WARNING: 'warning',
                message_constants.ERROR: 'danger',}


from emailSettings import *
import smtplib

# let's try a test email
if SEND_TEST_EMAIL:
    from django.core.mail import send_mail
    try:
        print "trying to send test email"
        send_mail('Eine SVPB Nachricht',
                  'Dies ist eine Test nachricht des SVPB Arbeitsplanungsprograms',
                  DEFAULT_FROM_EMAIL,
                  ['holger.karl@uni-paderborn.de'],
                  fail_silently=False)
        print "test email sent"
    except smtplib.SMTPException as e:
        print "test email FAILED: ", e


#####
# XSendfilte interface
# this will only work with nginx, not in development setup - but that's not too important to test there

SENDFILE_BACKEND = "sendfile.backends.development"
SENDFILE_ROOT = os.path.join(STATIC_ROOT, "static/media/doc")
SENDFILE_URL = "/media/doc"


JAHRESSTUNDEN = 10

# for select2: 
SELECT2_BOOTSTRAP = False
AUTO_RENDER_SELECT2_STATICS = False


# for phonenumbers:
PHONENUMBER_DEFAULT_REGION = "DE"
