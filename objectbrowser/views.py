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
from django.core.context_processors import csrf

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


def list_objects( request, object_type=None ):
    c = {}
    c['messages'] = m = []
    c['objects'] = objects = []
    
    search = tmp = {}
    for k,v in request.GET.items():
        k,v = str(k), str(v)
        if k == 'object_type':
            object_type = v
        if v == 'None':
            search[k] = None
        else:
            search[k] = v
    # If a non-existent object_type is requested, lets display a warning
    if not Model.string_to_class.has_key(object_type):
            m.append('Model does not have any objects of type %s, valid types are %s' % (object_type, Model.string_to_class.keys()))
            #return list_object_types(request)
            #return render_to_response('objectbrowser/list_object_types.html', c)
    else:
        myClass = Model.string_to_class[object_type]
    # Lets decide if we want to get everything or apply a filter
    if len(search) == 0:
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
    c.update(csrf(request))
    return render_to_response('objectbrowser/view_object.html', c)

def suggestions( request ):
    c = {}
    c['messages'] = m = []
    c['suggestions'] = s = {}
    # active_hosts_with_no_shortname
    services_no_description = Service.objects.filter(register="1", service_description=None)
    s['services_no_description'] = len(services_no_description)
    return render_to_response('objectbrowser/suggestions.html', c)
    
    
    
    
    