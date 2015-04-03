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

urlpatterns = patterns('',
                      url(r'^/test/?', 'adagios.misc.views.test'),
                      url(r'^/paste/?', 'adagios.misc.views.paste'),
                      url(r'^/?$', 'adagios.misc.views.index'),

                      url(r'^/settings/?', 'adagios.misc.views.settings'),
                      url(r'^/preferences/?', 'adagios.misc.views.preferences'),
                      url(r'^/nagios/?', 'adagios.misc.views.nagios'),
                      url(r'^/iframe/?', 'adagios.misc.views.iframe'),
                      url(r'^/gitlog/?', 'adagios.misc.views.gitlog'),
                      url(r'^/service/?', 'adagios.misc.views.nagios_service'),
                      url(r'^/pnp4nagios/?$', 'adagios.misc.views.pnp4nagios'),
                      url(r'^/pnp4nagios/edit(?P<filename>.+)$', 'adagios.misc.views.pnp4nagios_edit_template'),
                      url(r'^/mail', 'adagios.misc.views.mail'),
                      url(r'^/images/(?P<path>.+)$', 'django.views.static.serve', {'document_root': '/usr/share/nagios3/htdocs/images/logos/'}, name="logo"),
                      url(r'^/images/?$', 'adagios.misc.views.icons'),
                      )
