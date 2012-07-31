from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^/pynag/$', 'rest.views.index', { 'module_name': 'misc.helpers' }),
    (r'^/pynag/(?P<format>.+?)/(?P<attribute>.+)?$', 'rest.views.handle_request', { 'module_name': 'misc.helpers' }),
    (r'^/okconfig/$', 'rest.views.index', {'module_name':'okconfig'}),
    (r'^/okconfig/(?P<format>.+?)/(?P<attribute>.+)?$', 'rest.views.handle_request', {'module_name':'okconfig'}),
)
