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
                      url(r'^/?$', 'bi.views.index'),
                      url(r'^/add/?$', 'bi.views.add'),
                      url(r'^/add/subprocess/?$', 'bi.views.add_subprocess'),
                      url(r'^/add/graph/?$', 'bi.views.add_graph'),
                      url(r'^/(?P<process_name>.+)/edit/status_method$', 'bi.views.change_status_calculation_method'),
                      url(r'^/edit/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.edit'),
                      url(r'^/json/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.json'),
                      url(r'^/graphs/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.graphs_json'),
                      url(r'^/delete/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.delete'),
                      url(r'^/view/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.view'),
                      #(r'^/view/(?P<process_name>.+)/?$', 'bi.views.view'),
                       )

