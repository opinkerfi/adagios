# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Pall Sigurdsson <palli@opensource.is>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import url, patterns

urlpatterns = patterns('adagios',
                        url(r'^/?$', 'status.views.status_index'),
                        url(r'^/acknowledgements/?$', 'status.views.acknowledgement_list'),
                        url(r'^/error/?$', 'status.views.error_page'),
                        url(r'^/comments/?$', 'status.views.comment_list'),
                        url(r'^/contacts/?$', 'status.views.contact_list'),
                        url(r'^/contactgroups/?$', 'status.views.contactgroups'),
                        url(r'^/dashboard/?$', 'status.views.dashboard'),
                        url(r'^/detail/?$', 'status.views.detail'),
                        url(r'^/downtimes/?$', 'status.views.downtime_list'),
                        url(r'^/hostgroups/?$', 'status.views.status_hostgroups'),
                        url(r'^/hosts/?$', 'status.views.hosts'),
                        url(r'^/log/?$', 'status.views.log'),
                        url(r'^/map/?', 'status.views.map_view'),
                        url(r'^/parents/?$', 'status.views.network_parents'),
                        url(r'^/perfdata/?$', 'status.views.perfdata'),
                        url(r'^/perfdata2/?$', 'status.views.perfdata2'),
                        url(r'^/problems/?$', 'status.views.problems'),
                        url(r'^/servicegroups/?$', 'status.views.status_servicegroups'),
                        url(r'^/services/?$', 'status.views.services'),
                        url(r'^/state_history/?$', 'status.views.state_history'),
                        url(r'^/backends/?$', 'status.views.backends'),



                        # Misc snippets
                        url(r'^/snippets/log/?$', 'status.views.snippets_log'),
                        url(r'^/snippets/services/?$', 'status.views.snippets_services'),
                        url(r'^/snippets/hosts/?$', 'status.views.snippets_hosts'),

                        # Misc tests
                        url(r'^/test/services/?$', 'status.views.services_js'),
                        url(r'^/test/status_dt/?$', 'status.views.status_dt'),
                        url(r'^/test/livestatus/?$', 'status.views.test_livestatus'),

                        # Deprecated as of 2013-03-23
                        url(r'^/contacts/(?P<contact_name>.+)/?$', 'status.views.contact_detail'),
                        url(r'^/hostgroups/(?P<hostgroup_name>.+)/?$', 'status.views.status_hostgroup'),
                        url(r'^/contactgroups/(?P<contactgroup_name>.+)/?$', 'status.views.contactgroup_detail'),
                        url(r'^/servicegroups/(?P<servicegroup_name>.+)/?$', 'status.views.servicegroup_detail'),
                        url(r'^/services_old/?$', 'status.views.status'),


                        )
