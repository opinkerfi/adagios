from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('adagios',
                      (r'^/(?P<pnp_command>.+)?$', 'pnp.views.pnp'),
                       )
