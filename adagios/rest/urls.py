from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('adagios',
    url(r'^/pynag/$',   'rest.views.index', { 'module_name': 'misc.helpers' }, name="rest/pynag" ),
    url(r'^/adagios/$', 'rest.views.index', { 'module_name': 'misc.rest'    }, name="rest/adagios"),
    url(r'^/status/$', 'rest.views.index', { 'module_name': 'status.rest'    }, name="rest/status"),
    url(r'^/status.js$', 'rest.views.javascript', { 'module_name': 'status.rest'    }, ),
    url(r'^/pynag.js$', 'rest.views.javascript', { 'module_name': 'misc.helpers'    }, ),
    url(r'^/adagios.js$', 'rest.views.javascript', { 'module_name': 'misc.rest'    }, ),
    (r'^/pynag/$', 'rest.views.index', { 'module_name': 'misc.helpers' }),
    (r'^/okconfig/$', 'rest.views.index', {'module_name':'okconfig'}),
    (r'^/pynag/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', { 'module_name': 'adagios.misc.helpers' }),
    (r'^/okconfig/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', {'module_name':'adagios.okconfig'}, ),
    (r'^/adagios/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', { 'module_name': 'adagios.misc.rest' }, ),
    (r'^/status/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', { 'module_name': 'adagios.status.rest' }),
)
