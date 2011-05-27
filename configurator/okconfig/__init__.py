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

"""This module provides an interface to okconfig utilities
and operations such as adding new hosts to Nagios or adding
templates to current hosts

Example Usage:

import okconfig
okconfig.cfg_file="/etc/nagios/nagios.cfg"
okconfig.addhost("myhost.example.com", group_name="databases", templates=["linux","mysql"]) 
"""

__author__ = "Pall Sigurdsson"
__copyright__ = "Copyright 2011, Pall Sigurdsson"
__credits__ = ["Pall Sigurdsson"]
__license__ = "GPL"
__version__ = "0.3"
__maintainer__ = "Pall Sigurdsson"
__email__ = "palli@opensource.is"
__status__ = "Development"


cfg_file="/etc/nagios/nagios.cfg"
template_directory="/etc/nagios/okconfig/examples"
destination_directory="/etc/nagios/okconfig/hosts"


def verify():
	"""Checks if okconfig is installed and properly configured.
	
	Returns True/False
	"""
	pass

def addhost(host_name, ipaddress=None, group_name="default", templates=[], use=None, force=False):
	"""Adds a new host to Nagios. Returns true if operation is successful.
	
	Args:
	 host_name -- Hostname of the host to be added
	 ipaddress -- IP Address of the host (if None, it will be looked up in DNS)
	 group_name -- Primary host/contactgroup for this host. (if none, use "default")
	 templates -- List of template names to be added to this host
	 use -- if this host inherits another host (i.e. "windows-server")
	 force -- Force operation. Overwrite config files needed.
	
	Examples:
	 addhost(host_name="example_host",group="database_servers")

	Returns:
	 True if operation was successful.
	"""
	pass

def addtemplate(host_name, template_name, force=False):
	"""Adds a new template to existing host in Nagios.
	
	Args:
	 host_name -- Hostname to add template to (i.e. "host.example.com")
	 template_name -- Name of the template to be added (i.e. "mysql")
	 force -- Force operation, overwrites configuration if it already exists	
	
	Examples:
	 addtemplate(host_name="host.example.com", template="mysql")
	
	Returns:
	 True if operation is succesful.
	"""
	pass

def addgroup(group_name, alias=None, force=False):
	"""
	Adds a new hostgroup/contactgroup/servicegroup combo to Nagios.
	
	Args:
	 group_name -- Name of the group to be added (i.e. "db-servers")
	 alias -- Group alias (i.e. "Database Servers")
	 force -- Force operation, overwrites configuration if it already exists
	
	Examples:
	 addgroup(group_name="db-servers", alias="Database Servers")

	Returns:
	 True if operation was successful
	"""
	pass

def findhost(host_name):
	"""
	Returns the filename which defines a specied host. Returns None on failure.
	
	Args:
	 host_name -- Name of the host to find
	
	Examples:
	>>> print findhost("host.example.com")
	"/etc/okconfig/hosts/default/host.example.com-host.cfg"
	"""
	pass

def get_templates():
	""" Returns a list of available templates """


	return {
		'windows': {
            'parents': [],
			'name': 'Microsoft Windows',
		},
		'linux': {
            'parents': [],
            'name': 'Linux'
		},
        'dnsregistration': {
            'parents': ['linux', 'windows'],
            'name': 'DNS Registration'
        },
        'mssql': {
            'parents': ['windows'],
            'name': 'Microsoft SQL Server',
        },
        'exchange': {
            'parents': ['windows'],
            'name': 'Microsoft Exchange Server',
        },
        'ssh': {
            'parents': ['linux'],
            'name': 'Secure Shell Service'
        }
	}


def get_hosts():
	""" Returns a list of available hosts """
	#return ["host1","host2","host3"]
	pass

def install_nsclient(remote_host, username, password):
	""" Logs into remote (windows) host and installs NSClient.
	
	Args:
	 remote_host -- Hostname/IPAddress of remote host
	 username -- Name of a user with administrative privileges on the remote host
	 password -- Password to use
	
	Returns:
	 True if operation was successful. Otherwise False
	"""
	pass

def install_nrpe(remote_host, username, password=None):
	""" Logs into remote (unix) host and install nrpe-client.
	
	Args:
	 remote_host -- Hostname/IPAddress of remote host
	 username -- Username to use
	 password -- Password to use. If None, try to use ssh keys
	
	Returns:
	 True if operation was successful.
	"""
	pass

if __name__ == '__main__':
	'This leaves room for some unit testing while being run from the command line'
