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

import okconfig
from pynag import Model
import re

def add_defaultservice_to_host(host_name):
    ''' Given a specific hostname, add default service to it '''
    # Get our host
    try: my_host = Model.Host.objects.get_by_shortname(host_name)
    except ValueError: raise okconfig.OKConfigError("Host %s not found." % (host_name)) 
    
    # Dont do anything if file already exists
    service = Model.Service.objects.filter(name=host_name)
    if len(service) != 0:
        return False
    
    # Make sure that host belongs to a okconfig-compatible group
    hostgroup_name = my_host['hostgroups'] or "default"
    hostgroup_name = hostgroup_name.strip('+')
    if hostgroup_name in okconfig.get_groups():
        GROUP=hostgroup_name
    else:
        GROUP='default'
    
    template = default_service_template
    template = re.sub("HOSTNAME", host_name, template)
    template = re.sub("GROUP", GROUP, template)
    file = open( my_host['filename'], 'a')
    file.write(template)
    file.close()
    return True
    

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



default_service_template = '''
# This is a template service for HOSTNAME
# Services that belong to this host should use this as a template
define service {
        name                            HOSTNAME
        use                             GROUP-default_service
        host_name                       HOSTNAME
        contact_groups                  +GROUP
        service_groups                  +GROUP
        service_description             Default Service for HOSTNAME
        register                        0
}
'''

if __name__ == '__main__':
    print add_defaultservice_to_host('host1')
