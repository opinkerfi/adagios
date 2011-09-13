from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',

    (r'^/?$', 'okconfig_.views.index'),
    (r'^/scan_network/?', 'okconfig_.views.scan_network'),
    (r'^/addgroup/?', 'okconfig_.views.addgroup'),
    (r'^/addtemplate/?', 'okconfig_.views.addtemplate'),
    (r'^/addhost/?', 'okconfig_.views.addhost'),
    (r'^/verify_okconfig/?', 'okconfig_.views.verify_okconfig'),
)
 
