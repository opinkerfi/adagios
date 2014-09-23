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
This module looks up and stores Livesatus columns, organised per table,
and stored along with their name, type and description.
Access the data using:
>>> from adagios.status import custom_columns
>>> cols = custom_columns.all_columns

As a sidenote, columns for a specific table can be obtained with this oneliner:
$ printf 'GET columns' | netcat localhost 50000 | awk -F ';' '{if ($3 == "hosts") {print $2}}'
The Filter clause is not implemented in Shinken for the Columns table,
thus forcing us to post-process the data.
"""

import os
import json

from adagios.status import utils

def get_data():
    """
    Queries Livestatus to get the list of all available columns.
    Loops on the backends until one works.
    """
    backends = utils.get_all_backends()
    livestatus = utils.livestatus(None)
    query = 'GET columns'
    # we try every backend until one works properly
    # otherwise columns appear multiple times, coming from multiple backends
    # this is faster than using set() afterwards
    res = None
    for backend in backends:
        try:
            res = livestatus.query(query, backend=backend)
            break
        except:
            continue
    if not res:
        raise Exception('No working backend found.')
    return res

def process_data(data):
    """
    Columns list post-processing.
    This `unflats` the columns, and returns a dict(), with keys being
    the names of the Livestatus tables, and values being lists of
    name/description/type dict()s.
    """
    cols_by_table = {}
    for el in data:
        filtered = {'name': el['name'],
                    'description': el['description'],
                    'type': el['type'],
                    }
        table = el['table']
        if table in cols_by_table.keys():
            if el['name'] not in [x['name'] for x in cols_by_table[table]]:
                pass
                
        try:
            cols_by_table[el['table']].append(filtered)
        except Exception:
            cols_by_table[el['table']] = [filtered]
    return cols_by_table

def get_columns():
    """
    Computes Livestatus columns.
    """
    data = get_data()
    data = process_data(data)
    return data

# we keep this here, so this is only queried and processed once.
all_columns = get_columns()
