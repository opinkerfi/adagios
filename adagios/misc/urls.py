from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^/test/?', 'misc.tests.test'),
    (r'^/settings/?', 'misc.views.settings'),
    (r'^/nagios/?', 'misc.views.nagios'),
    (r'^/gitlog/?', 'misc.views.gitlog'),
    (r'^/service/?', 'misc.views.nagios_service'),
    (r'^/map/?', 'misc.views.map'),
    (r'^/pnp4nagios/?', 'misc.views.pnp4nagios'),
    (r'^/status/host/?$', 'misc.views.status'),
    (r'^/status/hostgroup/?$', 'misc.views.status_hostgroup'),
    (r'^/status/?$', 'misc.views.status_hostgroup'),
    (r'^/status/hostgroup/(?P<hostgroup_name>.+)/?$', 'misc.views.status_hostgroup'),
    (r'^/status/(?P<host_name>.+)/(?P<service_description>.+)/?$', 'misc.views.status_host'),
    (r'^/status/(?P<host_name>.+)$', 'misc.views.status_host'),
    (r'^/editfile(?P<filename>.+)$', 'misc.views.edit_file'),
    (r'^/livestatus/?$', 'misc.views.test_livestatus'),
)
 
