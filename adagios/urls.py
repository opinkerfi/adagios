from django.conf.urls.defaults import *

from django.conf import settings

from django.views.static import serve

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    url(r'^$', 'adagios.misc.views.index', name="home"),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}, name="media"),
    (r'^objectbrowser', include('adagios.objectbrowser.urls')),
    (r'^misc', include('adagios.misc.urls')),
    (r'^pnp', include('adagios.pnp.urls')),
    (r'^pages', include('adagios.pages.urls')),
    (r'^media(?P<path>.*)$',         serve, {'document_root': settings.MEDIA_ROOT }),
    (r'^rest', include('adagios.rest.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
