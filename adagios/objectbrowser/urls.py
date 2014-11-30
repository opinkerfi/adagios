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

    url(r'^/$', 'objectbrowser.views.list_object_types', name="objectbrowser"),

    url(r'^/edit_all/(?P<object_type>.+)/(?P<attribute_name>.+)/?$', 'objectbrowser.views.edit_all'),
    url(r'^/search/?$', 'objectbrowser.views.search_objects', name="search"),


    url(r'^/edit/(?P<object_id>.+?)?$', 'objectbrowser.views.edit_object', name="edit_object"),
    url(r'^/import/?$', 'objectbrowser.views.import_objects'),
    url(r'^/edit/?$', 'objectbrowser.views.edit_object'),
    url(r'^/copy_and_edit/(?P<object_id>.+?)?$', 'objectbrowser.views.copy_and_edit_object'),

    url(r'^/copy/(?P<object_id>.+)$', 'objectbrowser.views.copy_object', name="copy_object"),
    url(r'^/delete/(?P<object_id>.+)$', 'objectbrowser.views.delete_object', name="delete_object"),
    url(r'^/delete/(?P<object_type>.+?)/(?P<shortname>.+)/?$', 'objectbrowser.views.delete_object_by_shortname', name="delete_by_shortname"),

    url(r'^/add/(?P<object_type>.+)$', 'objectbrowser.views.add_object', name="addobject"),
    url(r'^/bulk_edit/?$', 'objectbrowser.views.bulk_edit', name='bulk_edit'),
    url(r'^/bulk_delete/?$', 'objectbrowser.views.bulk_delete', name='bulk_delete'),
    url(r'^/bulk_copy/?$', 'objectbrowser.views.bulk_copy', name='bulk_copy'),
    url(r'^/add_to_group/(?P<group_type>.+)/(?P<group_name>.+)/?$', 'objectbrowser.views.add_to_group'),
    url(r'^/add_to_group/(?P<group_type>.+)/?$', 'objectbrowser.views.add_to_group'),
    url(r'^/add_to_group', 'objectbrowser.views.add_to_group'),
    url(r'^/plugins/?$', 'objectbrowser.views.show_plugins'),
    url(r'^/nagios.cfg/?$', 'objectbrowser.views.edit_nagios_cfg'),
    url(r'^/nagios.cfg/edit/?$', 'misc.views.edit_nagios_cfg'),
    url(r'^/geek_edit/id=(?P<object_id>.+)$', 'objectbrowser.views.geek_edit'),
    url(r'^/advanced_edit/id=(?P<object_id>.+)$', 'objectbrowser.views.advanced_edit'),

    # Here for backwards compatibility.
    url(r'^/edit/id=(?P<object_id>.+)$', 'objectbrowser.views.edit_object', ),
    url(r'^/id=(?P<object_id>.+)$', 'objectbrowser.views.edit_object', ),

    # These should be deprecated as of 2012-08-27
    url(r'^/copy_object/id=(?P<object_id>.+)$', 'objectbrowser.views.copy_object'),
    url(r'^/delete_object/id=(?P<object_id>.+)$', 'objectbrowser.views.delete_object'),

    )
