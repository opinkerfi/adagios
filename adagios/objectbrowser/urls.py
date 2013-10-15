from django.conf.urls.defaults import *


urlpatterns = patterns('adagios',

                       # By default, lets just display a list of object_types
                       # available
                       url(r'^/$', 'objectbrowser.views.list_object_types',
                           name="objectbrowser"),

                       url(r'^/edit_all/(?P<object_type>.+)/(?P<attribute_name>.+)/?$', 'objectbrowser.views.edit_all'),
                       url(r'^/search/?$', 'objectbrowser.views.list_objects', name="search"),
                      (r'^/id=(?P<object_id>.+)$',
                       'objectbrowser.views.edit_object'),
                       url(r'/edit/id=(?P<object_id>.+)$',
                           'objectbrowser.views.edit_object', name="edit_object"),
                       url(r'/copy/id=(?P<object_id>.+)$',
                           'objectbrowser.views.copy_object', name="copy_object"),
                       url(r'/delete/id=(?P<object_id>.+)$',
                           'objectbrowser.views.delete_object', name="delete_object"),
                       url(r'/delete/(?P<object_type>.+?)/(?P<shortname>.+)/?$',
                           'objectbrowser.views.delete_object_by_shortname', name="delete_by_shortname"),

                       url(r'^/add/(?P<object_type>.+)$',
                           'objectbrowser.views.add_object', name="addobject"),
                       url(r'/bulk_edit/?$',
                           'objectbrowser.views.bulk_edit', name='bulk_edit'),
                       url(r'/bulk_delete/?$',
                           'objectbrowser.views.bulk_delete', name='bulk_delete'),
                       url(r'/bulk_copy/?$',
                           'objectbrowser.views.bulk_copy', name='bulk_copy'),
                       url(r'/edit_object/object_type=(?P<object_type>.+)/shortname=(?P<shortname>.+)$',
                           'objectbrowser.views.edit_object', name="edit_by_shortname"),
                       url(r'/add_to_group/(?P<group_type>.+)/(?P<group_name>.+)/?$',
                           'objectbrowser.views.add_to_group'),
                       url(r'/add_to_group/(?P<group_type>.+)/?$',
                           'objectbrowser.views.add_to_group'),
                       url(r'/add_to_group',
                           'objectbrowser.views.add_to_group'),
                      (r'/confighealth/?$',
                       'objectbrowser.views.config_health'),
                      (r'/plugins/?$', 'objectbrowser.views.show_plugins'),
                      (r'/nagios.cfg/?$', 'objectbrowser.views.edit_nagios_cfg'),
                      (r'/nagios.cfg/edit/?$', 'misc.views.edit_nagios_cfg'),
                      (r'/geek_edit/id=(?P<object_id>.+)$',
                       'objectbrowser.views.geek_edit'),
                      (r'/advanced_edit/id=(?P<object_id>.+)$',
                       'objectbrowser.views.advanced_edit'),

                       # These should be deprecated as of 2012-08-27
                      (r'^/search/?$', 'objectbrowser.views.list_objects'),
                      (r'^/id=(?P<object_id>.+)$',
                       'objectbrowser.views.edit_object'),
                      (r'/edit_object/id=(?P<object_id>.+)$',
                       'objectbrowser.views.edit_object'),
                      (r'/copy_object/id=(?P<object_id>.+)$',
                       'objectbrowser.views.copy_object'),
                      (r'/delete_object/id=(?P<object_id>.+)$',
                       'objectbrowser.views.delete_object'),


                       #

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       # (r'^admin/', include(admin.site.urls)),
                       )
