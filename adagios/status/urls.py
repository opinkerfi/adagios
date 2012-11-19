from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^/test/?$', 'status.views.test_livestatus'),
    (r'^/host/?$', 'status.views.status'),
    (r'^/hostgroup/?$', 'status.views.status_hostgroup'),
    (r'^/?$', 'status.views.status_hostgroup'),
    (r'^/hostgroup/(?P<hostgroup_name>.+)/?$', 'status.views.status_hostgroup'),
    (r'^/(?P<host_name>.+)/(?P<service_description>.+)/?$', 'status.views.status_detail'),
    (r'^/(?P<host_name>.+)/$', 'status.views.status_detail'),
    (r'^/(?P<host_name>.+)$', 'status.views.status_detail'),
    )
 
