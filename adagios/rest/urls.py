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
                       url(r'^/?$', 'rest.views.list_modules'),
                       )



# Example:
# rest_modules['module_name'] = 'module_path'
# will make /adagios/rest/module_name/ available and it loads all
# functions from 'module_path'

rest_modules = {}
rest_modules['pynag'] = 'adagios.misc.helpers'
rest_modules['okconfig'] = 'okconfig'
rest_modules['status'] = 'adagios.rest.status'
rest_modules['adagios'] = 'adagios.misc.rest'


# We are going to generate some url patterns, for clarification here is the end result shown for the status module:
#url(r'^/status/$', 'rest.views.index', { 'module_name': 'adagios.rest.status'    }, name="rest/status"),
#url(r'^/status.js$', 'rest.views.javascript', { 'module_name': 'adagios.rest.status'    }, ),
#(r'^/status/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', { 'module_name': 'adagios.rest.status' }),

for module_name, module_path in rest_modules.items():
    base_pattern = r'^/%s' % module_name
    args = {'module_name': module_name, 'module_path': module_path}
    urlpatterns += patterns('adagios',
        url(base_pattern + '/$',   'rest.views.index', args, name="rest/%s" % module_name),
        url(base_pattern + '.js$', 'rest.views.javascript', args, ),
        url(base_pattern + '/(?P<format>.+?)/(?P<attribute>.+?)/?$', 'rest.views.handle_request', args),
    )
