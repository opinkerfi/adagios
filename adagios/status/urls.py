from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('adagios',
                      (r'^/?$', 'status.views.status_index'),
                      (r'^/test/?$', 'status.views.test_livestatus'),
                      (r'^/boxview/?$', 'status.views.status_boxview'),
                      (r'^/(?P<object_type>.+?)s.tiles/?$',
                       'status.views.status_tiles'),

                      (r'^/paneview/?$', 'status.views.status_paneview'),
                      (r'^/state_history/?$', 'status.views.state_history'),
                      (r'^/problems/?$', 'status.views.dashboard'),

                      (r'^/dashboard/?$', 'status.views.dashboard'),
                      (r'^/log/?$', 'status.views.status_log'),
                      (r'^/parents/?$', 'status.views.status_parents'),
                      (r'^/hostgroups/?$', 'status.views.status_hostgroups'),
                      (r'^/hostgroups/(?P<hostgroup_name>.+)/?$',
                       'status.views.status_hostgroup'),
                      (r'^/servicegroups/?$',
                       'status.views.status_servicegroups'),
                      (r'^/hosts/?$', 'status.views.status_host'),
                      (r'^/services/?$', 'status.views.services'),
                      (r'^/services_old/?$', 'status.views.status'),
                      (r'^/contacts/(?P<contact_name>.+)/?$',
                       'status.views.contact_detail'),
                      (r'^/contacts/?$', 'status.views.contact_list'),
                      (r'^/contactgroups/(?P<contactgroup_name>.+)/?$',
                       'status.views.contactgroup_detail'),
                      (r'^/comments/?$', 'status.views.comment_list'),
                      (r'^/downtimes/?$', 'status.views.downtime_list'),
                      (r'^/perfdata/?$', 'status.views.perfdata'),
                      (r'^/perfdata2/?$', 'status.views.perfdata2'),
                       #(r'^/hosts/(?P<host_name>.+?)/(?P<service_description>.+)/?$', 'status.views.status_detail'),
                       #(r'^/hosts/(?P<host_name>.+)/$', 'status.views.status_detail'),
                       #(r'^/hosts/(?P<host_name>.+)$', 'status.views.status_detail'),
                      (r'^/error/?$', 'status.views.error_page'),
                      (r'^/detail/?$', 'status.views.status_detail'),

                      (r'^/snippets/log/?$', 'status.views.snippets_log'),

                       )
