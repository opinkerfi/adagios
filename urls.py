from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^$', 'misc.views.index'),
    (r'^contact_us$', 'misc.views.contact_us'),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^adagios/api/host/(?P<host_name>.*)\.(?P<ext>.+)$', 'configurator.views.api_host'),
    (r'^adagios/api/get_templates\.(?P<ext>.+)$', 'configurator.views.api_get_templates'),
    (r'^adagios/api/gethostbyname/(?P<host_name>.*)$', 'configurator.views.api_gethostbyname'), 
    (r'^adagios/$', 'configurator.views.index'),
    (r'^adagios/addhost$', 'configurator.views.addhost'),
    (r'^objectbrowser', include('objectbrowser.urls')),
    (r'^okconfig', include('okconfig.urls')),
    (r'^misc', include('misc.urls')),
    (r'^rest/okconfig', include('rest.urls'), {'module_name':'configurator.okconfig'}),
    (r'^rest/pynag', include('rest.urls'), {'module_name':'configurator.helpers'}),


    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
