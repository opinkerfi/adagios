#!/usr/bin/python
#
# Copyright 2011, Pall Sigurdsson <palli@opensource.is>
#
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

''' This module provides helper functions for okconfig '''

from pynag import Model
import os



def group_exists(group_name):
    ''' Check if a servicegroup,contactgroup or hostgroups exist with shortname == group_name
    
    Returns:
        False if no groups are found, otherwise it returns a list of groups
    '''
    servicegroups = Model.Servicegroup.objects.filter(shortname=group_name)
    contactgroups = Model.Contactgroup.objects.filter(shortname=group_name)
    hostgroups = Model.Hostgroup.objects.filter(shortname=group_name)
    result = (servicegroups+contactgroups+hostgroups)
    if result == ([]):
        return False
    return result