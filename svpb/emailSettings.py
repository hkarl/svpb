# email settings:
EMAIL_HOST = ''
EMAIL_PORT = 465

DEFAULT_FROM_EMAIL = ""
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = "XXX"
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

# easier for debugging: 
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# using the post office backend for asynchronous delivery:
# EMAIL_BACKEND = 'post_office.EmailBackend'

SEND_TEST_EMAIL = False
