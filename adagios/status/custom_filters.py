# -*- coding: utf-8 -*-
#
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

"""
This module manages the different filters subforms used in custom_forms.
A custom filter is a class:
  * inheriting from Default
  * defining fields
  * defining __repr__, its string representation being inserted in the
    Livestatus query at filtering time.
The rest is mapping between these classes and Livestatus tables.columns.
"""

from django import forms
# YAY, Python 2.6 :D (collections.OrderedDict is available from Python 2.7)
from django.utils.datastructures import SortedDict

class Default(object):
    def __init__(self, values={}):    
        self.values = values

    def __repr__(self):
        d = self.values.copy()
        d['op'] = '~' if self.values['regex'] else '='
        d['negate'] = '\nNegate:\n' if self.values['negate'] else ''
        return 'Filter: %(column)s %(op)s %(value)s%(negate)s\n' % d

    def get_fields(self):
        fields = SortedDict([
            ('value', forms.CharField(required=False)),
            ('regex', forms.BooleanField(required=False)),
            ('negate', forms.BooleanField(required=False)),
            ])
        return fields

class HostStates(Default):
    bool_names = ('UP', 'DOWN', 'UNREACHABLE', 'PENDING')
    
    def __repr__(self):
        states = [index
                  for index, key in enumerate(self.__class__.bool_names)
                  if self.values[key]]
        column = self.values['column']
        q = ''
        if len(states) > 0:
            q += ''.join(['Filter: %s = %s\n' % (column, index) for index in states])
            if len(states) > 1:
                q += 'Or: %d\n' % len(states)
        return q

    def get_fields(self):
        fields = SortedDict([(x, forms.BooleanField(required=False))
                             for x in self.__class__.bool_names])
        return fields

class ServiceStates(HostStates):
    bool_names = ('OK', 'WARNING', 'CRITICAL', 'UNKNOWN')

class YesNo(Default):
    def __repr__(self):
        q = 'Filter: %s = %d' % (self.values['column'], int(self.values['value']))
        return q
    
    def get_fields(self):
        fields = SortedDict([('value', forms.ChoiceField(
            required=False,
            choices=[(1, 'Yes'), (0, 'No')],
            widget=forms.widgets.RadioSelect))])
        return fields

mapping = {
    'hosts': {
        'state': HostStates,
        },
    'services': {
        'state': ServiceStates,
        'host_state': HostStates,
        'acknowledged': YesNo,
        }
    }

def get_filter(datasource, column):
    """
    Returns the filter corresponding to the given table (datasource)
    and column, or the default filter if not defined.
    """
    try:
        return mapping[datasource][column]
    except KeyError:
        return Default
