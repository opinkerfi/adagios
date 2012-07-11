from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',

    (r'^/?$', 'misc.views.index'),
    (r'^/contact_us/?', 'misc.views.contact_us'),
    (r'^/test/?', 'misc.tests.test'),
    (r'^/settings/?', 'misc.views.settings'),
    (r'^/nagios/?', 'misc.views.nagios'),
)
 
