from django.shortcuts import render_to_response, redirect
from django.core import serializers
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
import okconfig

# For API methods
import json


xmlsupport = True
try:
	import xml.marshal.generic	
except Exception, e:
	xmlsupport = False

from doit import *

def test(request):
	return index(request)

def home(request):
	return redirect('adagios')

def index(request):
	parse()
	c = {}
	c['hosts'] = get_hosts()
	return render_to_response('configurator/index.html', c)


def list_contacts(request):
	parse()
	c = {}
	c['contacts'] = get_contacts()
	return render_to_response('configurator/list_contacts.html', c)


def host(request, host_name=None):
	parse()
	c = {}
	c['host'] = get_host( host_name )
	c['template'] = items_from_template = {}
	c['not_template'] = items_not_from_template = {}
	for k,v in c['host'].iteritems():
		if k == 'meta': continue
		if k in c['host']['meta']['template_fields']:
			items_from_template[k] = v
		else:
			items_not_from_template[k] = v
	c['from_template'] = from_template = {}
	c['attributes'] = attributes = [] 
	c['attributes_from_template'] = c['host']['meta']['template_fields']
	for attribute in c['host']['meta']['template_fields']:
		from_template[attribute] = True
	for attribute,value in c['host'].iteritems():
		from_template[attribute] = False
		attributes.append( attribute )
	c['services'] = get_host_services( host_name )
	
	return render_to_response('configurator/host.html', c)

def contact( request, contact_name=None):
        parse()
        c = {}
        c['contact'] = get_contact( contact_name )
        c['template'] = items_from_template = {}
        c['not_template'] = items_not_from_template = {}
        for k,v in c['contact'].iteritems():
                if k == 'meta': continue
                if k in c['contact']['meta']['template_fields']:
                        items_from_template[k] = v
                else:
                        items_not_from_template[k] = v
        c['from_template'] = from_template = {}
        c['attributes'] = attributes = []
        c['attributes_from_template'] = c['contact']['meta']['template_fields']
        for attribute in c['contact']['meta']['template_fields']:
                from_template[attribute] = True
        for attribute,value in c['contact'].iteritems():
                from_template[attribute] = False
                attributes.append( attribute )

	return render_to_response('configurator/contact.html', c)
def service( request, host_name=None, service_description=None):
	parse()
	c = {}
	c['host'] = get_host( host_name )
	c['not_template'] = items_not_from_template = {}
	c['template'] = items_from_template = {}
	c['service'] = nc.get_service(host_name, service_description)
	for k,v in c['service'].iteritems():
		if k == 'meta': continue
		if k in c['service']['meta']['template_fields']:
			items_from_template[k] = v
		else:
			items_not_from_template[k] = v
	return render_to_response('configurator/service.html', c)


def edit_service( request, host_name, service_description,field_name,new_value):
	parse()
	c = {}
	c['host'] = get_host( host_name )
	c['not_template'] = items_not_from_template = {}
	c['template'] = items_from_template = {}
	c['service'] = service = nc.get_service(host_name, service_description)
	print c['service']['meta']
	nc.edit_object(service, field_name, new_value)
	nc.commit()
	c['service'] = nc.get_service(host_name, service_description)
	for k,v in c['service'].iteritems():
		if k == 'meta': continue
		if k in c['service']['meta']['template_fields']:
			items_from_template[k] = v
		else:
			items_not_from_template[k] = v
	return render_to_response('configurator/service.html', c)

def stringify(data, ext):	
	if xmlsupport == False and ext == 'xml':
		return HttpResponse('<h1>XML not supported, missing xml.marshall', mimetype='text/html')

	if ext == 'xml':
		string = xml.marshal.generic.dumps(data)
		mime_type = 'text/xml'
	elif ext == 'html':
		return render_to_response('configurator/api/host.html', data)
	elif ext == 'json':
		string = json.dumps(data)
		mime_type = 'application/json'
	else:
		return HttpResponseServerError("Invalid extension")
	return HttpResponse(string, mimetype=mime_type)

def api_get_templates(request, ext='xml'):
	c = {}

	c['templates'] = okconfig.get_templates()
	return stringify(c, ext)

def api_host(request, host_name=None, ext='xml'):
	parse()
	c = {}
	if host_name != None:
		c['host'] = get_host( host_name )
		return stringify(c, ext)

	return NotImplementedError

def api_gethostbyname(request, host_name=None):
	import socket
	
	host = ''
	try:
		host = socket.gethostbyname(host_name)
	except:
		pass
	
	return HttpResponse(json.dumps({'host': host}), mimetype='application/json') 



def addhost(request):
	return render_to_response('configurator/addhost.html')