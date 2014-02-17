from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('adagios',
                      (r'^/$', 'contrib.views.index'),
                      (r'^/(?P<arg1>.+)?$', 'contrib.views.contrib'),
                      (r'^/(?P<arg1>.+)/(?P<arg2>.+)/?$', 'contrib.views.contrib'),
                      (r'^/(?P<arg1>.+)(?P<arg2>.+)/(?P<arg3>.+)/?$', 'contrib.views.contrib'),
                      (r'^/(?P<arg1>.+)(?P<arg2>.+)/(?P<arg3>.+)/(?P<arg4>.+)/?$', 'contrib.views.contrib'),
                       )
