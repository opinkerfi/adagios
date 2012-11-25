from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^/test/?', 'misc.tests.test'),
    (r'^/settings/?', 'misc.views.settings'),
    (r'^/nagios/?', 'misc.views.nagios'),
    (r'^/gitlog/?', 'misc.views.gitlog'),
    (r'^/service/?', 'misc.views.nagios_service'),
    (r'^/map/?', 'misc.views.map'),
    (r'^/pnp4nagios/?', 'misc.views.pnp4nagios'),
    (r'^/editfile(?P<filename>.+)$', 'misc.views.edit_file'),
    (r'^/signout$', 'misc.views.sign_out'),
)
 
