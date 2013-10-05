from django.conf.urls.defaults import *
from django.conf import settings

'''
urlpatterns = patterns('adagios',
    url(r'^/pynag/$',   'rest.views.index', { 'module_name': 'adagios.rest.objectbrowser' }, name="rest/pynag" ),
    url(r'^/adagios/$', 'rest.views.index', { 'module_name': 'adagios.misc.rest'    }, name="rest/adagios"),
    url(r'^/status/$', 'rest.views.index', { 'module_name': 'adagios.rest.status'    }, name="rest/status"),
    url(r'^/status.js$', 'rest.views.javascript', { 'module_name': 'adagios.rest.status'    }, ),
    url(r'^/pynag.js$', 'rest.views.javascript', { 'module_name': 'adagios.rest.objectbrowser'    }, ),
    url(r'^/adagios.js$', 'rest.views.javascript', { 'module_name': 'adagios.misc.rest'    }, ),
    (r'^/pynag/$', 'rest.views.index', { 'module_name': 'adagios.rest.objectbrowser' }),
    (r'^/okconfig/$', 'rest.views.index', {'module_name':'okconfig'}),
    (r'^/pynag/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', { 'module_name': 'adagios.rest.objectbrowser' }),
    (r'^/okconfig/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', {'module_name':'okconfig'}, ),
    (r'^/adagios/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', { 'module_name': 'adagios.misc.rest' }, ),
    (r'^/status/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', { 'module_name': 'adagios.rest.status' }),
)
'''
urlpatterns = []
# Example:
# rest_modules['module_name'] = 'module_path'
# will make /adagios/rest/module_name/ available and it loads all
# functions from 'module_path'

rest_modules = {}
rest_modules['pynag'] = 'adagios.misc.helpers'
rest_modules['okconfig'] = 'okconfig'
rest_modules['status'] = 'adagios.rest.status'


# We are going to generate some url patterns, for clarification here is the end result shown for the status module:
#url(r'^/status/$', 'rest.views.index', { 'module_name': 'adagios.rest.status'    }, name="rest/status"),
#url(r'^/status.js$', 'rest.views.javascript', { 'module_name': 'adagios.rest.status'    }, ),
#(r'^/status/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', { 'module_name': 'adagios.rest.status' }),

for module_name, module_path in rest_modules.items():
    base_pattern = r'^/%s' % module_name
    args = {'module_name': module_name, 'module_path': module_path}
    urlpatterns += patterns('adagios',
                            url(base_pattern + '/$',   'rest.views.index',
                                args, name="rest/%s" % module_name),
                            url(base_pattern + '.js$',
                                'rest.views.javascript', args, ),
                           (base_pattern + '/(?P<format>.+?)/(?P<attribute>.+?)/?$',
                            'rest.views.handle_request', args),
                            )
