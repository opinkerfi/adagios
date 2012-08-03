from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^/test/?', 'misc.tests.test'),
    (r'^/settings/?', 'misc.views.settings'),
    (r'^/nagios/?', 'misc.views.nagios'),
)
 
