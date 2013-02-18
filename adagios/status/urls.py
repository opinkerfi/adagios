from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^/?$', 'status.views.status_index'),
    (r'^/test/?$', 'status.views.test_livestatus'),
    (r'^/boxview/?$', 'status.views.status_boxview'),
    (r'^/(?P<object_type>.+?)s.tiles/?$', 'status.views.status_tiles'),

    (r'^/paneview/?$', 'status.views.status_paneview'),
    (r'^/state_history/?$', 'status.views.state_history'),
    (r'^/problems/?$', 'status.views.status_problems'),
    (r'^/log/?$', 'status.views.status_log'),
    (r'^/parents/?$', 'status.views.status_parents'),
    (r'^/hostgroups/?$', 'status.views.status_hostgroups'),
    (r'^/hostgroups/(?P<hostgroup_name>.+)/?$', 'status.views.status_hostgroup'),
    (r'^/hosts/?$', 'status.views.status_host'),
    (r'^/services/?$', 'status.views.status'),
    (r'^/contacts/(?P<contact_name>.+)/?$', 'status.views.contact_detail'),
    (r'^/contacts/?$', 'status.views.contact_list'),
    (r'^/comments/?$', 'status.views.comment_list'),
    #(r'^/hosts/(?P<host_name>.+?)/(?P<service_description>.+)/?$', 'status.views.status_detail'),
    #(r'^/hosts/(?P<host_name>.+)/$', 'status.views.status_detail'),
    #(r'^/hosts/(?P<host_name>.+)$', 'status.views.status_detail'),
    (r'^/error/?$', 'status.views.error_page'),
    (r'^/detail/?$', 'status.views.status_detail'),

    )
 
