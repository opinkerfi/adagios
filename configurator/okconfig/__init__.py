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
import socket

from sys import exit
from sys import argv
from sys import path
from pynag import Model
from os import getenv,putenv,environ

import os
import subprocess
import helper_functions
required_gateways = []



def is_valid():
	"""Checks if okconfig is installed and properly configured.
	
	Returns True/False
	
	See verify() for more details
	"""	
	checks = verify()
	for result in checks.values():
		if result is False: return False
	return True

def _is_in_path(command):
	''' Searches $PATH and returns true if command is found, and in path '''
	
	
	is_executable = lambda x: os.path.isfile(x) and os.access(x, os.X_OK)
	
	if command.startswith('/'):
		return is_executable(command)
	
	my_path = os.environ['PATH'].split(':')
	for possible_path in my_path:
		full_path = "%s/%s" % (possible_path,command)
		if is_executable(full_path): return True
	return False

def verify():
	"""Checks if okconfig is installed and properly configured.
	
	Returns dict of {'check_name':Boolean}
	
	Check if:
	1) cfg_file exists
	2) template_directory exists
	3) destination_directory exists (and is writable)
	"""
	results = {}
	
	# 1) cfg_file exists
	check = "Main configuration file %s is readable" % (cfg_file)
	results[check] = os.access(cfg_file, os.R_OK)

	# 2) template_directory exists
	check = "template_directory %s exists" % (template_directory)
	results[check] = os.access(template_directory, os.R_OK) and os.path.isdir(template_directory)
	
	# 3) destination_directory or parent exists (and is writable)
	for ddir in [destination_directory, "%s/.." % (destination_directory)]:
		ddir = os.path.dirname(ddir)
		check = "destination_directory %s is writable" % (ddir)
		results[check] = os.access(ddir, os.W_OK + os.R_OK) and os.path.isdir(ddir)
		if results[check] == True: break	
	
	# 4)
	# Should no longer be need
	# TODO: Remove this commented codeblock
	#okconfig_binaries = ('addhost','findhost','addgroup','addtemplate')
	#for command in okconfig_binaries:
	#	check = "'%s' command is in path" % command
	#	results[check] = _is_in_path(command)
	
	return results

def addhost(host_name, address=None, group_name=None, templates=[], use=None, force=False):
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
	if group_name is None or group_name is '': group_name = 'default'
	if templates is None: templates = []
	if address is None or address is '':
		try:
			address = socket.gethostbyname(host_name)
		except:
			raise OKConfigError("Could not resolve hostname '%s'" % (host_name))
	if use is None:
		if 'windows' in templates:
			use = 'windows-server'
		elif 'linux' in templates:
			use = 'linux-server'
		elif 'ciscoswitch' in templates:
			use = 'generic-switch'		
		else:
			use = 'default-host'
	okconfig_groups = get_groups()
	if len(okconfig_groups) == 0:
		addgroup(group_name='default',alias='OKconfig default group')
	arguments = {}
	arguments['PARENTHOST'] = use
	arguments['GROUP'] = group_name
	arguments['IPADDR'] = address
	arguments['HOSTNAME'] = host_name
	destination_file = "%s/%s/%s-host.cfg" % (destination_directory, group_name, host_name)
	if not force:
		if os.path.isfile(destination_file):
			raise OKConfigError("Destination file '%s' already exists." % (destination_file))
		if group_name not in get_groups():
			raise OKConfigError("Group %s does not exist" % (group_name))
		if host_name in get_hosts():
			filename = Model.Host.objects.get_by_shortname(host_name)._meta['filename']
			raise OKConfigError("Host named '%s' already exists in %s" % (host_name, filename))
	# Do sanity checking of all templates before we add anything
	all_templates = get_templates().keys()
	for i in templates:
		if i not in all_templates:
			raise OKConfigError("Template %s not found" % (i))
		
	result = _apply_template('host', destination_file, **arguments)
	for i in templates:
		result = result + addtemplate(host_name=host_name, template_name=i, group_name=group_name,force=force)
	return result
def addtemplate(host_name, template_name, group_name=None,force=False):
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
	hostfile = findhost(host_name)
	if group_name is None: group_name="default"
	if hostfile is None:
		raise OKConfigError("Host '%s' was not found" % host_name)
	if template_name not in get_templates().keys():
		raise OKConfigError("Template '%s' was not found" % template_name)
	hostdir = os.path.dirname(hostfile)	
	# Check if host has the required "default service"
	helper_functions.add_defaultservice_to_host(host_name)
	
	# Lets do some templating
	newfile = "%s/%s-%s.cfg" % (hostdir, host_name,template_name)
	if not force:
		'Do some basic sanity checking'
		if os.path.exists(newfile):
			raise OKConfigError("Destination file '%s' already exists." % (newfile))
	
	return _apply_template(template_name,newfile, HOSTNAME=host_name, GROUP=group_name)

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
	newfile = "%s/%s.cfg" % (destination_directory, group_name)
	
	if not force:
		'Do some sanity checking'
		if os.path.exists(newfile):
			raise OKConfigError("Destination file '%s' already exists" % newfile)
		groups = helper_functions.group_exists(group_name)
		if groups != False:
			raise OKConfigError("We already have groups with name = %s" % (group_name))
	
	return _apply_template(template_name="group",destination_file=newfile, GROUP=group_name, ALIAS=alias)

def findhost(host_name):
	"""Returns the filename which defines a specied host. Returns None on failure.
	
	Args:
	 host_name -- Name of the host to find
	
	Examples:
	>>> print findhost("host.example.com")
	"/etc/okconfig/hosts/default/host.example.com-host.cfg"
	"""
	try:
		my_host = Model.Host.objects.get_by_shortname(host_name)
		filename = my_host['meta']['filename']
		return filename
	except ValueError:
		return None

def get_templates():
	""" Returns a list of available templates """
	result = {}
	if not os.path.isdir(examples_directory):
		raise OKConfigError("Examples directory does not exist: %s" % examples_directory)
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
	Model.Servicegroup.objects.reload_cache()
	servicegroups = Model.Servicegroup.objects.all
	for s in servicegroups:
		name = s.get_shortname()
		if name == None: continue
		try:
			Model.Contactgroup.objects.reload_cache()
			Model.Hostgroup.objects.reload_cache()
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
	raise NotImplementedError()

def check_agent(host_name):
	""" Checks a remote host if it has a valid okconfig client configuration
	
	Args:
		host_name -- hostname (or ip address of remote host)
	Returns:
		True/False, [ "List","of","messages" ]
	"""
	raise NotImplementedError()

def install_nrpe(remote_host, username, password=None):
	""" Logs into remote (unix) host and install nrpe-client.
	
	Args:
	 remote_host -- Hostname/IPAddress of remote host
	 username -- Username to use
	 password -- Password to use. If None, try to use ssh keys
	
	Returns:
	 True if operation was successful.
	"""
	raise NotImplementedError()


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
			error_string += "Check if y/our path is correct: %s" % (path)
		raise BaseException( error_string )
	else:
		return stdout

def _apply_template(template_name,destination_file, **kwargs):
	''' Applies okconfig template to filename, doing replacements from kwargs in the meantime
    
    Arguments:
        template_name - name of the template to use
        destination_file - full path to file to be written to
        kwargs key/value pair of string to search and replacement to make
    
    Example:
        _apply_template('host','/etc/nagios/okconfig/hosts/newhost.cfg', HOSTNAME='newhost',ADDRESS='0.0.0.0',GROUP='default')
    Returns:
        List of filenames that have been written to
    '''
	sourcefile = "%s/%s.cfg-example" % (examples_directory,template_name)
	
	if not os.path.isfile(sourcefile):
		raise OKConfigError('Template %s cannot be found' % (template_name))

	dirname = os.path.dirname(destination_file)
	if not os.path.exists(dirname): os.makedirs(dirname)  
	
	file = open(sourcefile).read()
	for old_string,new_string in kwargs.items():
		file = file.replace(old_string,new_string)
	open(destination_file,'w').write( file )
	return [destination_file]


class OKConfigError(Exception):
	pass

#all_templates = get_templates()
if __name__ == '__main__':
	'This leaves room for some unit testing while being run from the command line'
	print addhost('mbl.is', address=None, group_name=None, templates=['windows'], use=None, force=True)

