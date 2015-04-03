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

from django.conf.urls import url, patterns, include
from adagios import settings
from django.views.static import serve

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    # Example:
    url(r'^$', 'adagios.views.index', name="home"),
    url(r'^403', 'adagios.views.http_403'),
    url(r'^objectbrowser', include('adagios.objectbrowser.urls')),
    url(r'^status', include('adagios.status.urls')),
    url(r'^bi', include('adagios.bi.urls')),
    url(r'^misc', include('adagios.misc.urls')),
    url(r'^pnp', include('adagios.pnp.urls')),
    url(r'^media(?P<path>.*)$',         serve, {'document_root': settings.STATIC_ROOT }),
    url(r'^rest', include('adagios.rest.urls')),
    url(r'^contrib', include('adagios.contrib.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),

    # Internationalization
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}, name="media"),
    )
        

# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#urlpatterns += staticfiles_urlpatterns()

