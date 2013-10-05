from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('adagios',
                      (r'^/?$', 'pages.views.index'),
                      (r'^/(?P<pagename>.+)/?$', 'pages.views.serve_page'),
                       )
