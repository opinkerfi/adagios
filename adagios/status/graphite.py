# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Matthieu Caneill <matthieu.caneill@savoirfairelinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


def _get_graphite_url(base, host, service, metric, from_, title, width, height, prefix=''):
    """ Constructs an URL for Graphite.
    
    Args:
      - base (str): base URL for Graphite access
      - host (str): hostname
      - service (str): service, e.g. HTTP
      - metric (str): metric, e.g. size, time
      - from_ (str): Graphite time period
      - title (str): title of the graphic
      - width (int): width in pixels
      - height (int): height in pixels
      - prefix (str): Prefix to put in front of your graphite datapoint

    Returns: str
    """
    host = _compliant_name(host)
    service = _compliant_name(service)
    metric = _compliant_name(metric)

    base = base.rstrip('/')

    url = ('%(base)s/render/'
           '?width=%(width)s'
           '&height=%(height)s'
           '&from=%(from_)s'
           '&target=%(prefix)s%(host)s.%(service)s.%(metric)s'
           '&target=%(prefix)s%(host)s.%(service)s.%(metric)s_warn'
           '&target=%(prefix)s%(host)s.%(service)s.%(metric)s_crit'
           '&title=%(title)s')
    
    url %= dict(base=base, host=host, service=service, metric=metric,
                from_=from_, width=width, height=height, title=title, prefix=prefix)
    return url

def _compliant_name(name):
    """ Makes the necessary replacements for Graphite. """
    if name == '_HOST_':
        return '__HOST__'
    for t in (' ', '/', '.'):
        name = name.replace(t, '_')
        print(t)
    return name

def get(base, host, service, metrics, units, width, height, prefix=''):
    """ Returns a data structure containg URLs for Graphite.

    The structure looks like:
    [{'name': 'One day',
      'css_id' : 'day',
      'metrics': {'size': 'http://url-of-size-metric',
                  'time': 'http://url-of-time-metric'}
     },
     {...}]
    
    Args:
      - base (str): base URL for Graphite access
      - host (str): hostname
      - service (str): service, e.g. HTTP
      - metric (str): metric, e.g. size, time
      - units (list): a list of <name,css_id,unit>,
        see adagios.settings.GRAPHITE_PERIODS
      - width (int): width in pixels
      - height (int): height in pixels

    Returns: list
    """
    graphs = []
    title = '%(host)s - %(service)s - %(metric)s'
    
    for name, css_id, unit in units:
        m = {}
        for metric in metrics:
            titl = title % dict(host=host, service=service, metric=metric)
            m[metric] = _get_graphite_url(base, host, service, metric,
                                          unit, titl, width, height, prefix)
        graph = dict(name=name, css_id=css_id, metrics=m)
        graphs.append(graph)
    
    return graphs