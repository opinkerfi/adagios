from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',

    (r'^/?$', 'okconfig.views.index'),
    (r'^/scan_network/?', 'okconfig.views.scan_network'),
    (r'^/addgroup/?', 'okconfig.views.addgroup'),
    (r'^/addtemplate/?', 'okconfig.views.addtemplate'),
    (r'^/addhost/?', 'okconfig.views.addhost'),
    (r'^/verify_okconfig/?', 'okconfig.views.verify_okconfig'),
)
 
