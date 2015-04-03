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

                      url(r'^/scan_network/?', 'okconfig_.views.scan_network'),
                      url(r'^/addgroup/?', 'okconfig_.views.addgroup'),
                      url(r'^/addtemplate/?', 'okconfig_.views.addtemplate'),
                      url(r'^/addhost/?', 'okconfig_.views.addhost'),
                      url(r'^/addservice/?', 'okconfig_.views.addservice'),
                      url(r'^/install_agent/?', 'okconfig_.views.install_agent'),
                      url(r'^/edit/?$', 'okconfig_.views.choose_host'),
                      url(r'^/edit/(?P<host_name>.+)$', 'okconfig_.views.edit'),
                      url(r'^/verify_okconfig/?',
                       'okconfig_.views.verify_okconfig'),
                      )
