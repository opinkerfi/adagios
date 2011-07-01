from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',

    #(r'/(?P<attribute_name>.+)=(?P<attribute_value>.+?)/(?P<attribute2_name>.+)=(?P<attribute2_value>.+?)/(?P<attribute3_name>.+)=(?P<attribute3_value>.+?)/?$', 'objectbrowser.views.list_objects'),
    #(r'/(?P<attribute_name>.+)=(?P<attribute_value>.+?)/(?P<attribute2_name>.+)=(?P<attribute2_value>.+?)/?$', 'objectbrowser.views.list_objects'),
    #(r'/(?P<attribute_name>.+)=(?P<attribute_value>.+?)/?$', 'objectbrowser.views.list_objects'),

    # By default, lets just display a list of object_types available
    (r'^/?$', 'objectbrowser.views.list_object_types'),
    (r'^/search/?$', 'objectbrowser.views.list_objects'),
    (r'/id=(?P<object_id>.+)$', 'objectbrowser.views.view_object'),
    (r'/(host|service|timeperiod|contact|contactgroup|servicegroup|command|hostgroup)$', 'objectbrowser.views.list_object'),
    (r'/view_object/id=(?P<object_id>.+)$', 'objectbrowser.views.view_object'),
    (r'/view_object/object_type=(?P<object_type>.+)/shortname=(?P<shortname>.+)$', 'objectbrowser.views.view_object'),
    (r'/confighealth/?$', 'objectbrowser.views.confighealth'),
    (r'/parents/?$', 'objectbrowser.views.view_parents'),
    (r'/nagios.cfg/?$', 'objectbrowser.views.view_nagioscfg'),
    
    # 
    #(r'/(?P<object_type>.+)/?$', 'objectbrowser.views.list_objects'),
    
    #(r'/contact/(?P<contact_name>.+)$', 'objectbrowser.views.get_contact'),


    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
