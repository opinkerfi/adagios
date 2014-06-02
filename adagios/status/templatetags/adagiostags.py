# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Pall Sigurdsson <palli@opensource.is>
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

import math
import socket
from geoip import geolite2
from datetime import datetime, timedelta
from django import template
from django.utils.timesince import timesince
from django.utils.translation import ugettext as _
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter("timestamp")
def timestamp(value):
    try:
        return datetime.fromtimestamp(value)
    except (AttributeError, TypeError):
        return ''

@register.filter("duration")
def duration(value):
    """ Used as a filter, returns a human-readable duration.
    'value' must be in seconds.
    """
    zero = datetime.min
    try:
        return timesince(zero, zero + timedelta(0, value))
    except Exception:
        return value

@register.filter("hash")
def hash(h, key):
    try:
        return h[key]
    except KeyError as e:
        return ''

@register.filter("replace")
@stringfilter
def replace(value, args):
    """ args must be a comma-separated string: "pattern, replacement" """
    try:
        pattern, replacement = args.split(',')
    except Exception as e:
        return value
    return value.replace(pattern, replacement)

@register.filter("locateip")
def locateip(value):
    def is_legal_ip(ip):
        try:
            socket.inet_pton(socket.AF_INET, address)
        except Exception:
            try:
                socket.inet_pton(socket.AF_INET6, address)
            except Exception:
                return False
        return True
    
    if not is_legal_ip(value):
        try:
            value = socket.gethostbyname(value)
        except Exception:
            return None
    try:
        match = geolite2.lookup(value)
        lat, lon = match.location
    except Exception as e:
        print value, e
        return None
    #return (lon, lat)
    return '%s,%s' % (lon, lat)
