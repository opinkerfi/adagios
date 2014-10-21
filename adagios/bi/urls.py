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
from django.conf import settings

urlpatterns = patterns('adagios',
                      (r'^/?$', 'bi.views.index'),
                      (r'^/add/?$', 'bi.views.add'),
                      (r'^/add/subprocess/?$', 'bi.views.add_subprocess'),
                      (r'^/add/graph/?$', 'bi.views.add_graph'),
                      (r'^/(?P<process_name>.+)/edit/status_method$', 'bi.views.change_status_calculation_method'),
                      (r'^/edit/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.edit'),
                      (r'^/json/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.json'),
                      (r'^/graphs/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.graphs_json'),
                      (r'^/delete/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.delete'),
                      (r'^/view/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.view'),
                      #(r'^/view/(?P<process_name>.+)/?$', 'bi.views.view'),
                       )
