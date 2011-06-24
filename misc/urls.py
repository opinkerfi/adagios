from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',

    (r'^/?$', 'misc.views.index'),
    (r'^/contact_us/?', 'misc.views.contact_us'),
)
 
