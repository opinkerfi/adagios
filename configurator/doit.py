import sys

sys.path.insert(1, '/opt/pynag')
from pynag.Parsers import config
nc = config('/etc/nagios/nagios.cfg')
nc.parse()

def parse():
	global nc
	nc = config('/etc/nagios/nagios.cfg')	
	nc.parse()
def get_hosts():
	## Create the plugin option
	hosts = nc['all_host']
	return hosts

def get_contacts():
	contacts = nc['all_contact']
	return contacts
def get_contact(contact_name):
	contact = nc.get_contact( contact_name )
	return contact
def get_host(host_name):
	host = nc.get_host( host_name )
	return host


def get_host_services(host_name):
	all_services = nc.data['all_service']
	this_host_services = []
	for service in all_services:
		if not service.has_key('host_name'): continue
		if service['host_name'] == host_name:
			this_host_services.append( service )
	return this_host_services

if __name__ == '__main__':
	service = nc.get_service('pall.sigurdsson.is','Ping')
	nc.edit_object2(service, 'name', 'Debug2')
