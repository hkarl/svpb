# email settings:
EMAIL_HOST = 'smtp.strato.de'
EMAIL_PORT = 465
## sender =     'experiment@propgen.de'
## destination = ['holger.karl@uni-paderborn.de']

DEFAULT_FROM_EMAIL = "experiment@propgen.de"
EMAIL_HOST_USER = "experiment@propgen.de"
EMAIL_HOST_PASSWORD = "kgKK.34aKY"
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

# easier for debugging: 
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# using the post office backend for asynchronous delivery: 
# EMAIL_BACKEND = 'post_office.EmailBackend'

SEND_TEST_EMAIL = False
