from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
                      (r'^/test/?', 'adagios.misc.views.test'),
                      (r'^/paste/?', 'adagios.misc.views.paste'),


                      (r'^/edit_check_command/?',
                       'adagios.misc.views.edit_check_command'),
                      (r'^/settings/?', 'adagios.misc.views.settings'),
                      (r'^/nagios/?', 'adagios.misc.views.nagios'),
                      (r'^/gitlog/?', 'adagios.misc.views.gitlog'),
                      (r'^/service/?', 'adagios.misc.views.nagios_service'),
                      (r'^/map/?', 'adagios.misc.views.map_view'),
                      (r'^/pnp4nagios/?$', 'adagios.misc.views.pnp4nagios'),
                      (r'^/pnp4nagios/edit(?P<filename>.+)$',
                       'adagios.misc.views.pnp4nagios_edit_template'),
                      (r'^/signout$', 'adagios.misc.views.sign_out'),
                      (r'^/mail', 'adagios.misc.views.mail'),
                       url(r'^/images/(?P<path>.+)$', 'django.views.static.serve',
                           {'document_root': '/usr/share/nagios3/htdocs/images/logos/'}, name="logo"),
                      (r'^/images/?$', 'adagios.misc.views.icons'),
                       )
