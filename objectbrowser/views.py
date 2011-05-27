from django.shortcuts import render_to_response, redirect
from django.core import serializers
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson

import sys
sys.path.insert(1, '/opt/pynag')


from pynag.Model import *
from pynag import Model

def test(request):
        return index(request)

def home(request):
        return redirect('adagios')

def index(request):
	return list_hosts(request)

def list_hosts(request):
        c = {}
	c['hosts'] = Host.objects.all
        return render_to_response('configurator/index.html', c)

def list_contacts(request):
	c = {}
	c['contacts'] = Contact.objects.all
        return render_to_response('configurator/list_contacts.html', c)

def list_objects( request, object_type ):
    c = {}
    c['messages'] = m = []
    c['objects'] = objects = []
    if not Model.string_to_class.has_key(object_type):
        m.append('Model does not have any objects of type %s, valid types are %s' % (object_type, Model.string_to_class.keys()))
    else:
        myClass = Model.string_to_class[object_type]
        c['objects'] = myClass.objects.all
    m.append( "Found %s objects of type %s" % (len(c['objects']), object_type))
    return render_to_response('objectbrowser/list_objects.html', c)

'''
    c['hostname'] = 'palli'
    c['object_type'] = object_type
    print c['object_type']
    print type(object_type), object_type
    myClass = Model.string_to_class[object_type]
    o = myClass.objects.all
    c['objects'] = o
    c['objecttype'] = "object_type"
    hostn = 'palli'
'''

def view_object( request, object_type, object_name ):
	c = {}
	c['object_type'] = object_type
	o = ObjectDefinition(object_type)
	return render_to_response('objectbrowser/view_object.html')

def get_contact(request, contact_name=None):
    c = {}
    c['messages'] = []
    c['contact'] = Contact.objects.filter(contact_name=contact_name)[0]
    #c['messages'].append( "found %s objects" % (len(c['contact'])))
    c['messages'].append(  contact_name ) 
    c['template'] = {}
    c['not_template'] = {}
    c['from_template'] = {}
    c['attributes_from_template'] = {}
    c['attributes'] = {}
    return render_to_response('configurator/contact.html', c)
def get_host(request, host_name):
	pass


