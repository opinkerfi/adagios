from django.conf.urls.defaults import *

urlpatterns = patterns('adagios',
                      (r'^/?$', 'myapp.views.hello_world'),
                      (r'^/url1?$', 'myapp.views.hello_world'),
                      (r'^/url2?$', 'myapp.views.hello_world'),
                       )
