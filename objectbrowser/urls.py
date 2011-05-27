from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    # Example:
    #(r'^/', 'objectbrowser.views.index'),
    #(r'^/host', 'objectbrowser.views.list_hosts'),
    #(r'^/host/(?P<host_name>.+)$', 'objectbrowser.views.get_host'),
    
    #(r'/contact/+$', 'objectbrowser.views.list_contacts'),
    (r'/(?P<object_type>.+)+$', 'objectbrowser.views.list_objects'),
    (r'/(?P<object_type>.+)/+$', 'objectbrowser.views.list_objects'),
    #(r'/contact/(?P<contact_name>.+)$', 'objectbrowser.views.get_contact'),


    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
