from django.conf.urls.defaults import *

from django.conf import settings

from django.views.static import serve

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    url(r'^$', 'adagios.views.index', name="home"),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}, name="media"),
    url(r'^objectbrowser', include('adagios.objectbrowser.urls')),
    url(r'^misc', include('adagios.misc.urls')),
    url(r'^pnp', include('adagios.pnp.urls')),
    url(r'^media(?P<path>.*)$',         serve, {'document_root': settings.MEDIA_ROOT }),
    url(r'^rest', include('adagios.rest.urls')),
    url(r'^contrib', include('adagios.contrib.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    
    # Internationalization
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog'),
)
