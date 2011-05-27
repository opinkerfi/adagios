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


def list_objects( request, object_type=None, attribute_name=None, attribute_value=None ):
    c = {}
    c['messages'] = m = []
    c['objects'] = objects = []
    if attribute_name=='object_type':
        object_type=attribute_value
    if not Model.string_to_class.has_key(object_type):
        m.append('Model does not have any objects of type %s, valid types are %s' % (object_type, Model.string_to_class.keys()))
    else:
        myClass = Model.string_to_class[object_type]
        if attribute_name is None:
            c['objects'] = myClass.objects.all
        else:
            tmp = {attribute_name:attribute_value}
            c['objects'] = myClass.objects.filter(**tmp)
            m.append("I used the filter %s=%s" % (attribute_name, attribute_value))
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

def view_objects( request, object_type,  attribute_name=None, attribute_value=None ):
    c = {}
    c['messages'] = m = []
    c['objects'] = objects = []
    if not Model.string_to_class.has_key(object_type):
        m.append('Model does not have any objects of type %s, valid types are %s' % (object_type, Model.string_to_class.keys()))
    else:
        myClass = Model.string_to_class[object_type]
        if attribute_name is None:
            c['objects'] = myClass.objects.all
        else:
            tmp = {attribute_name:attribute_value}
            c['objects'] = myClass.objects.filter(**tmp)
            m.append("I used the filter %s=%s" % (attribute_name, attribute_value))
    m.append( "Found %s objects of type %s" % (len(c['objects']), object_type))
    attributes = []
    c['first_object'] = c['objects'][0]
    c['first_object'].data = ["1","2"]
    for tmp in c['objects']:
        for k in tmp.keys():
            if k not in attributes: attributes.append( k )
    for i in c['objects']:
        i.my_data = "test"
    attr_val = []
    for i in attributes:
        if c['first_object']._defined_attributes.has_key(i):
            defined_attr = c['first_object']._defined_attributes[i]
        else:
            defined_attr = ""
        if i in c['first_object']._inherited_attributes:
            inherited_attr = c['first_object']._inherited_attributes[i]
        else:
            inherited_attr = ""
        if None != inherited_attr or None != defined_attr:
            attr_val.append( [i, defined_attr, inherited_attr ] )
    c['attr_val'] = attr_val
    c['attr_val'] = c['first_object'].get_attribute_tuple()
    m.append( "id=%s" % c['first_object'].get_id())
    c['first_object'].id = c['first_object'].get_id()
    return render_to_response('objectbrowser/view_object.html', c)

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


