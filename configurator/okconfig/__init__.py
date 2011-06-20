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
template_directory="/etc/nagios/okconfig/templates"
examples_directory="/etc/nagios/okconfig/examples"
destination_directory="/etc/nagios/okconfig/hosts"


from sys import exit
from sys import argv
from sys import path
path.insert(0, "/opt/pynag")
from pynag import Model
from os import getenv,putenv,environ

import os.path
import subprocess

required_gateways = []




def verify():
	"""Checks if okconfig is installed and properly configured.
	
	Returns True/False
	
	Check if:
	1) cfg_file exists
	2) template_directory exists
	3) destination_directory exists (and is writable)
	4) the following commands are in path:
		addhost, addgroup, addtemplate
	"""
	# TODO: Check if okconfig is writeable
	
	# 1)
	if not os.path.isfile(cfg_file):
		return False
	# 2)
	if not os.path.isdir(template_directory):
		return False
	# 3)
	if not os.path.isdir(destination_directory):
		return False
	# 4)
	my_path = os.environ['PATH'].split(':')
	for command in ['addhost', 'addgroup', 'addtemplate']:
		command_was_found = False
		for possible_path in my_path:
			full_path = "%s/%s" % (possible_path,command)
			if os.path.isfile(full_path):
				command_was_found = True
				break 
		if not command_was_found:
			"command %s not found in path" % (command)
			return False
	return True

def addhost(host_name, address=None, group_name="default", templates=[], use=None, force=False):
	"""Adds a new host to Nagios. Returns true if operation is successful.
	
	Args:
	 host_name -- Hostname of the host to be added
	 address -- IP Address of the host (if None, it will be looked up in DNS)
	 group_name -- Primary host/contactgroup for this host. (if none, use "default")
	 templates -- List of template names to be added to this host
	 use -- if this host inherits another host (i.e. "windows-server")
	 force -- Force operation. Overwrite config files needed.
	
	Examples:
	 addhost(host_name="example_host",group="database_servers")

	Returns:
	 String message with result of addhost
	"""
	if address == None:
		address = ''
	else:
		address = "--ip '%s'" % (address)
	if force == True:
		force = '--force'
	else:
		force = ''
	group_name = "--group '%s'" % (group_name)
	if use == None:
		use = ''
	else:
		use = "--parent '%s'" % (use)
	command = "addhost --host '%s' %s %s %s" % (host_name, address, use, force)
	result = runCommand(command)
	return result

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
	if force == True:
		force = '--force'
	else:
		force = ''
	command = "addtemplate --host '%s' --template '%s' %s" % (host_name, template_name, force)
	return runCommand(command)

def addgroup(group_name, alias=None, force=False):
	"""Adds a new hostgroup/contactgroup/servicegroup combo to Nagios.
	
	Args:
	 group_name -- Name of the group to be added (i.e. "db-servers")
	 alias -- Group alias (i.e. "Database Servers")
	 force -- Force operation, overwrites configuration if it already exists
	
	Examples:
	 addgroup(group_name="db-servers", alias="Database Servers")

	Returns:
	 True if operation was successful
	""" 
	if alias == None: alias=group_name
	if force == True:
		force = '--force'
	else:
		force = ''
	command = "addgroup --group '%s' --alias '%s' %s" % (group_name, alias, force)
	return runCommand(command)

def findhost(host_name):
	"""Returns the filename which defines a specied host. Returns None on failure.
	
	Args:
	 host_name -- Name of the host to find
	
	Examples:
	>>> print findhost("host.example.com")
	"/etc/okconfig/hosts/default/host.example.com-host.cfg"
	"""
	pass

def get_templates():
	""" Returns a list of available templates """
	result = {}
	if not os.path.isdir(examples_directory):
		raise IOError("Examples directory does not exist: %s" % examples_directory)
	filelist = os.listdir(examples_directory)
	for file in filelist:
		if os.path.isfile(examples_directory + "/" + file) and file.endswith('.cfg-example'):
			template_name = file[:-12]
			template_parents = []
			template_friendly_name = ''
			result[template_name] = {'parents':template_parents, 'name':template_friendly_name}
	return result
	dummy_templates = {
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
	return dummy_templates


def get_hosts():
	""" Returns a list of available hosts """
	result = []
	hosts = Model.Host.objects.all
	for host in hosts:
		if host.get_shortname() not in result and host.get_shortname() is not None:
			result.append(host.get_shortname())
	return result

def get_groups():
	""" Returns a list of okconfig compatible groups """
	result = []
	servicegroups = Model.Servicegroup.objects.all
	for s in servicegroups:
		name = s.get_shortname()
		if name == None: continue
		try:
			Model.Contactgroup.objects.get_by_shortname(name)
			Model.Hostgroup.objects.get_by_shortname(name)
			result.append( name )
		except ValueError:
			continue
	return result
		
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

def check_agent(host_name):
	""" Checks a remote host if it has a valid okconfig client configuration
	
	Args:
		host_name -- hostname (or ip address of remote host)
	Returns:
		True/False, [ "List","of","messages" ]
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


def runCommand(command):
	'''runCommand: Runs command from the shell prompt.
	
	Arguments:
		command: string containing the command line to run
	Returns:
		stdout/stderr of the command run
	Raises:
		BaseException if returncode > 0
	'''
	proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE,)
	stdout, stderr = proc.communicate('through stdin to stdout')
	if proc.returncode > 0:
		error_string = "Could not run command (return code= %s)\n" % (proc.returncode)
		error_string += "Error: %s\n" % (stderr.strip())
		error_string += "Command: %s\n" % (command)
		if proc.returncode == 127: # File not found, lets print path
			path=getenv("PATH")
			error_string += "Check if your path is correct: %s" % (path)
		raise BaseException( error_string )
	else:
		return stdout


all_templates = get_templates()
if __name__ == '__main__':
	'This leaves room for some unit testing while being run from the command line'
	result = get_groups()
	print result
	print "done"
