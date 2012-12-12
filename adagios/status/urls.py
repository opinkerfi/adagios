from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^/?$', 'status.views.status_index'),
    (r'^/test/?$', 'status.views.test_livestatus'),
    (r'^/boxview/?$', 'status.views.status_boxview'),
    (r'^/paneview/?$', 'status.views.status_paneview'),
    (r'^/state_history/?$', 'status.views.state_history'),
    (r'^/problems/?$', 'status.views.status_problems'),
    (r'^/log/?$', 'status.views.status_log'),
    (r'^/parents/?$', 'status.views.status_parents'),
    (r'^/hostgroups/?$', 'status.views.status_hostgroup'),
    (r'^/hostgroups/(?P<hostgroup_name>.+)/?$', 'status.views.status_hostgroup'),
    (r'^/hosts/?$', 'status.views.status'),
    (r'^/hosts/(?P<host_name>.+?)/(?P<service_description>.+)/?$', 'status.views.status_detail'),
    (r'^/hosts/(?P<host_name>.+)/$', 'status.views.status_detail'),
    (r'^/hosts/(?P<host_name>.+)$', 'status.views.status_detail'),

    )
 
