from django.conf.urls import *

urlpatterns = patterns('',

    # By default, lets just display a list of object_types available
    url(r'^/$', 'objectbrowser.views.list_object_types', name="objectbrowser"),

    (r'^/search/?$', 'objectbrowser.views.list_objects'),
    (r'^/id=(?P<object_id>.+)$', 'objectbrowser.views.edit_object'),
    url(r'/edit/id=(?P<object_id>.+)$', 'objectbrowser.views.edit_object', name="edit_object"),
    url(r'/copy/id=(?P<object_id>.+)$', 'objectbrowser.views.copy_object', name="copy_object"),
    url(r'/delete/id=(?P<object_id>.+)$', 'objectbrowser.views.delete_object', name="delete_object"),
    url(r'^/add/(?P<object_type>.+)$', 'objectbrowser.views.edit_object', name="addobject"),
    url(r'/bulk_edit/?$', 'objectbrowser.views.bulk_edit', name='bulk_edit'),
    url(r'/bulk_delete/?$', 'objectbrowser.views.bulk_delete', name='bulk_delete'),
    url(r'/bulk_copy/?$', 'objectbrowser.views.bulk_copy', name='bulk_copy'),
    url(r'/edit_object/object_type=(?P<object_type>.+)/shortname=(?P<shortname>.+)$', 'objectbrowser.views.edit_object', name="edit_by_shortname"),
    (r'/confighealth/?$', 'objectbrowser.views.config_health'),
    (r'/plugins/?$', 'objectbrowser.views.show_plugins'),
    (r'/nagios.cfg/?$', 'objectbrowser.views.edit_nagios_cfg'),
    (r'/geek_edit/id=(?P<object_id>.+)$', 'objectbrowser.views.geek_edit'),
    (r'/advanced_edit/id=(?P<object_id>.+)$', 'objectbrowser.views.advanced_edit'),

    # These should be deprecated as of 2012-08-27
    (r'^/search/?$', 'objectbrowser.views.list_objects'),
    (r'^/id=(?P<object_id>.+)$', 'objectbrowser.views.edit_object'),
    (r'/edit_object/id=(?P<object_id>.+)$', 'objectbrowser.views.edit_object'),
    (r'/copy_object/id=(?P<object_id>.+)$', 'objectbrowser.views.copy_object'),
    (r'/delete_object/id=(?P<object_id>.+)$', 'objectbrowser.views.delete_object'),

    # 

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
