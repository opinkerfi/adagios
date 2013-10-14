from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('adagios',
                      (r'^/?$', 'bi.views.index'),
                      (r'^/add/?$', 'bi.views.add'),
                      (r'^/add/subprocess/?$', 'bi.views.add_subprocess'),
                      (r'^/add/graph/?$', 'bi.views.add_graph'),
                      (r'^/(?P<process_name>.+)/edit/status_method$', 'bi.views.change_status_calculation_method'),
                      (r'^/edit/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.edit'),
                      (r'^/json/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.json'),
                      (r'^/graphs/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.graphs_json'),
                      (r'^/delete/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.delete'),
                      (r'^/view/(?P<process_type>.+?)/(?P<process_name>.+?)/?$', 'bi.views.view'),
                      #(r'^/view/(?P<process_name>.+)/?$', 'bi.views.view'),
                       )
