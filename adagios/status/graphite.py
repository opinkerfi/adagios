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


import re
import adagios.settings

ILLEGAL_CHAR = re.compile(r'[^\w-]')


def _get_graphite_url(base, host, service, metric, from_):
    """ Constructs an URL for Graphite.

    Args:
      - base (str): base URL for Graphite access
      - host (str): hostname
      - service (str): service, e.g. HTTP
      - metric (str): metric, e.g. size, time
      - from_ (str): Graphite time period

    Returns: str
    """
    host_ = _compliant_name(host)
    service_ = _compliant_name(service)
    metric_ = _compliant_name(metric)
    base = base.rstrip('/')
    title = adagios.settings.graphite_title.format(**locals())

    url = "{base}/render?" + adagios.settings.graphite_querystring
    url = url.format(**locals())
    return url


def _compliant_name(name):
    """ Makes the necessary replacements for Graphite. """
    if name == '_HOST_':
        return '__HOST__'
    name = ILLEGAL_CHAR.sub('_', name)
    return name


def get(base, host, service, metrics, units):
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
      - metrics (list): list of metrics, e.g. ["size", "time"]
      - units (list): a list of <name,css_id,unit>,
        see adagios.settings.GRAPHITE_PERIODS

    Returns: list
    """
    graphs = []

    for name, css_id, unit in units:
        m = {}
        for metric in metrics:
            m[metric] = _get_graphite_url(base, host, service, metric, unit)
        graph = dict(name=name, css_id=css_id, metrics=m)
        graphs.append(graph)

    return graphs
