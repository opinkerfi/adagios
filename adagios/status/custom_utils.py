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
This module provides helpers to manage the custom views.
"""

import locale
locale.setlocale(locale.LC_ALL, "")

from adagios.status import custom_filters

def data_to_query(data):
    """
    Transforms a view dict into a Livestatus query.

    The passed dict represents a stored (in userdata) custom view, it
    has the same structure as a forms set in custom_edit.
    """
    d = {}
    d['datasource'] = data['metadata'][0]['data_source']
    d['columns'] = [x['name'] for x in data['columns'] if x['name']]
    # we have to add columns which are in d['sorts'], otherwise the data
    # postprocessor can't do its job
    #sorts = [x['column'] for x in data['sorts']]
    add_sorts = [x['column'] for x in data['sorts'] if x not in d['columns']]
    d['columns'] = ' '.join(d['columns'] + add_sorts)
    if d['columns']:
        d['columns'] = 'Columns: ' + d['columns'] + '\n'
    d['stats'] = ''.join(['Stats: %(column)s = %(value)s\n' % x for x in data['stats']])
    d['filters'] = ''.join([str(custom_filters.get_filter(d['datasource'], x['column'])(x))
                            for x in data['filters'] if x['column']])
    query = ('GET %(datasource)s\n'
             '%(columns)s'
             '%(filters)s'
             '%(stats)s') % d
    # Remove unneeded linebreaks at the end:
    query = query.strip()
    return query

class _OppositeStr(str):
    """ Simple hack to not implement the sorting by ourselves.
    By allowing the construction of opposite strings (as in the
    mathematical opposite), we can have the DESC functionality
    while only using the key parameter of sorted.
    It's the opposite day! http://youtu.be/G1p6VrAmq9g
    """
    def __cmp__(self, o):
        return -1 * cmp(str(self), str(o))
    def __lt__(self, o):
        return self.__cmp__(o) < 0

def _format_sort(string):
    """ Let's not pay attention to capitals and esoteric chars. """
    return locale.strxfrm(str(string).lower())

def sort_data(data, sorts):
    """
    Sorts columns, in reverse order where it's specified, or normal order
    otherwise.
    """
    return [_OppositeStr(_format_sort(data[x['column']])) if x['reverse']
        else _format_sort(data[x['column']])
        for x in sorts]
