# -*- coding: utf-8 -*-
#
# Copyright 2010, Pall Sigurdsson <palli@opensource.is>
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

## DEPRECATED for list_objects
def list_hosts(request):
        c = {}
	c['hosts'] = Host.objects.all
        return render_to_response('configurator/index.html', c)
## Deprecated for list_objects
def list_contacts(request):
	c = {}
	c['contacts'] = Contact.objects.all
        return render_to_response('configurator/list_contacts.html', c)


def list_objects( request, object_type=None, attribute_name=None, attribute_value=None, attribute2_name=None, attribute2_value=None, attribute3_name=None, attribute3_value=None ):
    c = {}
    c['messages'] = m = []
    c['objects'] = objects = []
    
    search = tmp = {}
    if attribute_name != None:
        search = {attribute_name:attribute_value}
    if attribute2_name != None:
        search[attribute2_name]=attribute2_value
    if attribute3_name != None:
        search[attribute3_name]=attribute3_value
    
    for k,v in search.items():
        if k == 'object_type':
            object_type = v
        elif v == 'None':
            search[k] = None
    # If a non-existent object_type is requested, lets display a warning
    if not Model.string_to_class.has_key(object_type):
            m.append('Model does not have any objects of type %s, valid types are %s' % (object_type, Model.string_to_class.keys()))
            return list_object_types(request)
            return render_to_response('objectbrowser/list_object_types.html', c)
    else:
        myClass = Model.string_to_class[object_type]
    # Lets decide if we want to get everything or apply a filter
    if attribute_name is None:
        c['objects'] = myClass.objects.all
    else:
        c['objects'] = myClass.objects.filter(**search)
        m.append("I used the filter %s=%s" % (search.keys(), search.values()))
    m.append( "Found %s objects of type %s" % (len(c['objects']), object_type))
    return render_to_response('objectbrowser/list_objects.html', c)

def list_object_types(request):
    c = {}
    c['object_types'] = t = []
    for name,Class in Model.string_to_class.items():
        if name != None:
            active = inactive = 0
            all_instances = Class.objects.all
            for i in all_instances:
                if i['register'] == "0":
                    inactive += 1
                else:
                    active += 1
            c['object_types'].append( (name, active, inactive) )
    return render_to_response('objectbrowser/list_object_types.html', c)

def view_object( request, object_id):
    c = {}
    c['messages'] = m = []
    o = ObjectDefinition.objects.filter(id=object_id)[0]
    #o = ObjectDefinition.objects.get_by_id(id=object_id)
    c['my_object'] = o
    c['attr_val'] = o.get_attribute_tuple()
    return render_to_response('objectbrowser/view_object.html', c)



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


