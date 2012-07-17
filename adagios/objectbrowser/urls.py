from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',

    #(r'/(?P<attribute_name>.+)=(?P<attribute_value>.+?)/(?P<attribute2_name>.+)=(?P<attribute2_value>.+?)/(?P<attribute3_name>.+)=(?P<attribute3_value>.+?)/?$', 'objectbrowser.views.list_objects'),
    #(r'/(?P<attribute_name>.+)=(?P<attribute_value>.+?)/(?P<attribute2_name>.+)=(?P<attribute2_value>.+?)/?$', 'objectbrowser.views.list_objects'),
    #(r'/(?P<attribute_name>.+)=(?P<attribute_value>.+?)/?$', 'objectbrowser.views.list_objects'),

    # By default, lets just display a list of object_types available
    (r'^/$', 'objectbrowser.views.list_object_types'),
    (r'^/search/?$', 'objectbrowser.views.list_objects'),
    (r'^/id=(?P<object_id>.+)$', 'objectbrowser.views.view_object'),
    (r'/view_object/id=(?P<object_id>.+)$', 'objectbrowser.views.view_object'),
    (r'/view_object/object_type=(?P<object_type>.+)/shortname=(?P<shortname>.+)$', 'objectbrowser.views.view_object'),
    (r'/confighealth/?$', 'objectbrowser.views.config_health'),
    (r'/parents/?$', 'objectbrowser.views.view_parents'),
    (r'/plugins/?$', 'objectbrowser.views.show_plugins'),
    (r'/add_service/?$', 'objectbrowser.views.add_service'),
    (r'/nagios.cfg/?$', 'objectbrowser.views.view_nagios_cfg'),
    (r'/geek_edit/id=(?P<object_id>.+)$', 'objectbrowser.views.geek_edit'),
    (r'/advanced_edit/id=(?P<object_id>.+)$', 'objectbrowser.views.advanced_edit'),
    #(r'^$', 'objectbrowser.views.list_object', { 'object_type':"None" } ),
    #(r'^/(contact|host|service|timeperiod|command|contactgroup|hostgroup|servicegroup)', 'objectbrowser.views.list_object'),
    
    # 
    #(r'/(?P<object_type>.+)/?$', 'objectbrowser.views.list_objects'),
    
    #(r'/contact/(?P<contact_name>.+)$', 'objectbrowser.views.get_contact'),


    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
