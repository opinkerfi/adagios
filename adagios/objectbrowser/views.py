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
from django.http import HttpResponse, HttpResponseServerError,\
    HttpResponseRedirect
from django.utils import simplejson
from django.template import RequestContext
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
import sys
import os
from os.path import dirname

from pynag.Model import ObjectDefinition
from pynag import Model
from pynag.Model import EventHandlers
from forms import *

from log import *

try:
    # Hook up git event handler
    Model.eventhandlers.append(Model.EventHandlers.GitEventHandler(dirname(Model.cfg_file), 'adagios', 'tommi'))
except Exception, e:
    pass

def home(request):
    return redirect('adagios')

def list_objects( request, object_type=None, display_these_objects=None ):
    """Finds Pynag objects and returns them in a pretty list. search filter can be applied via querystring
    
    Arguments:
        object_type(str) : Only find pynag object of this type
        display_these_objects([ObjectDefinition]) : Instead of searching, simply return these objects
        
    """ 
    c = {'messages': [], 'objects': [],
         'object_type': object_type}                      # This hash is sent to our template
    # Validate any potential search terms sent via querystring
    search = {}
    for k,v in request.GET.items():
        k,v = str(k), str(v)
        if k == 'object_type':
            object_type = v
        if v == 'None':
            search[k] = None
        else:
            search[k] = v
    
    # If a non-existent object_type is requested, lets display a warning
    # Model.string_to_class contains a hash map that convert string value to its respective class definition
    Pynag = Model.string_to_class.get(object_type, Model.ObjectDefinition)
    
    # Lets decide if we want to get everything or apply a filter
    if display_these_objects is not None:
        c['objects'] = display_these_objects
    elif not len(search):
        c['objects'] = Pynag.objects.all
    else:
        c['objects'] = Pynag.objects.filter(**search)
    
    return render_to_response('list_objects.html', c, context_instance = RequestContext(request))

def list_object_types(request):
    """ Collects statistics about pynag objects and returns to template """
    c = {'object_types': []}
    for name,Class in Model.string_to_class.items():
        if name is not None:
            active = inactive = 0
            all_instances = Class.objects.all
            for i in all_instances:
                if i['register'] == "0":
                    inactive += 1
                else:
                    active += 1
            c['object_types'].append( { "name": name, "active": active, "inactive": inactive } )
    c['gitlog'] = gitlog(dirname(Model.cfg_file or Model.config.cfg_file))
    return render_to_response('list_object_types.html', c, context_instance = RequestContext(request))

def geek_edit( request, object_id ):
    """ Function handles POST requests for the geek edit form """
    c = {}
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = []

    # Get our object
    try:
        o = ObjectDefinition.objects.get_by_id(id=object_id)
        c['my_object'] = o
    except Exception, e:
        # Not raising, handled by template
        c['error_summary'] = 'Unable to find object'
        c['error'] = e
        return render_to_response('error.html', c, context_instance = RequestContext(request))

    
    if request.method == 'POST':
        # Manual edit of the form
        form = GeekEditObjectForm(data=request.POST, pynag_object=o)
        if form.is_valid():
            form.save()
            m.append("Object Saved manually to '%s'" % o['filename'])
        else:
            m.append( "Failed to save object")
    else:
        form = GeekEditObjectForm(initial={'definition':o['meta']['raw_definition'], })

    # Lets return the user to the general edit_object form
    return HttpResponseRedirect( reverse('objectbrowser.views.edit_object', kwargs={'object_id':o.get_id()} ) )

def advanced_edit(request, object_id):
    ''' Handles POST only requests for the "advanced" object edit form. '''
    c = {}
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = []
    # Get our object
    try:
        o = ObjectDefinition.objects.get_by_id(id=object_id)
    except Exception, e:
        c['error_summary'] = 'Unable to get object'
        c['error'] = e
        return render_to_response('error.html', c, context_instance = RequestContext(request))

    if request.method == 'POST':
        "User is posting data into our form "
        c['advanced_form'] = PynagForm( pynag_object=o,initial=o._original_attributes, data=request.POST, simple=True )
        if c['advanced_form'].is_valid():
            c['advanced_form'].save()
            m.append("Object Saved to %s" % o['filename'])
        else:
            c['errors'].append( "Problem reading form input")

    return HttpResponseRedirect( reverse('objectbrowser.views.edit_object', args=[o.get_id()] ) )

def edit_object( request, object_id=None, object_type=None, shortname=None):
    """ View details about one specific pynag object """
    c = {}
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = []
    # Get our object
    if object_id is not None:
        # If object id was specified
        try:
            o = ObjectDefinition.objects.get_by_id(id=object_id)
        except Exception, e:
            # Not raising, handled by template
            c['error_summary'] = 'Unable to get object'
            c['error'] = e
            return render_to_response('error.html', c, context_instance = RequestContext(request))
    elif object_type is not None and shortname is None:
        # Specifying only object_type indicates this is a new object
        otype = Model.string_to_class.get(object_type, Model.ObjectDefinition)
        o = otype()
    elif object_type is not None and shortname is not None:
        # Its also valid to specify object type and shortname
        # TODO: if multiple objects are found, display a list
        try:
            otype = Model.string_to_class.get(object_type, Model.ObjectDefinition)
            o = otype.objects.get_by_shortname(shortname)
        except Exception, e:
            # Not raising, handled by template
            c['error_summary'] = 'Unable to get object'
            c['error'] = e
            return render_to_response('error.html', c, context_instance = RequestContext(request))
    else:
        raise ValueError("Object not found")

    if request.method == 'POST':
        # User is posting data into our form
        c['form'] = PynagForm( pynag_object=o,initial=o._original_attributes, data=request.POST )
        if c['form'].is_valid():
            c['form'].save()
            m.append("Object Saved to %s" % o['filename'])
            return HttpResponseRedirect( reverse('objectbrowser.views.edit_object', kwargs={'object_id':o.get_id()} ) )
        else:
            c['errors'].append( "Could not validate form input")
    else:
        c['form'] = PynagForm( pynag_object=o, initial=o._original_attributes )

    c['form'] = PynagForm( pynag_object=o, initial=o._original_attributes )
    c['my_object'] = o
    c['geek_edit'] = GeekEditObjectForm(initial={'definition':o['meta']['raw_definition'], })
    c['advanced_form'] = PynagForm( pynag_object=o, initial=o._original_attributes, simple=True )

    # Some type of objects get a little special treatment:
    if o['object_type'] == 'host':
        return _edit_host(request, c)
    elif o['object_type'] == 'service':
        return _edit_service(request, c)
    elif o['object_type'] == 'contact':
        return _edit_contact(request, c)

    # Here we have all sorts of extra information that can be stuffed into the template,
    # Some of these do not apply for every type of object, hence the try/except
    try: c['command_line'] = o.get_effective_command_line()
    except: pass
    try: c['object_macros'] = o.get_all_macros()
    except: pass
    try: c['effective_hostgroups'] = o.get_effective_hostgroups()
    except: pass
    try: c['effective_contacts'] = o.get_effective_contacts()
    except: pass
    try: c['effective_contactgroups'] = o.get_effective_contact_groups()
    except: pass
    try: c['effective_contactgroups'] = o.get_effective_contactgroups()
    except: pass
    try: c['effective_members'] = o.get_effective_members()
    except: pass

    return render_to_response('edit_object.html', c, context_instance = RequestContext(request))

def _edit_contactgroup( request, c):
    """ This is a helper function to edit_object """
    try: c['effective_members'] = c['my_object'].get_effective_members()
    except: pass
    return render_to_response('edit_contactgroup.html', c, context_instance = RequestContext(request))
def _edit_contact( request, c):
    """ This is a helper function to edit_object """
    try: c['effective_contactgroups'] = c['my_object'].get_effective_contactgroups()
    except: pass
    return render_to_response('edit_contact.html', c, context_instance = RequestContext(request))

def _edit_service( request, c):
    """ This is a helper function to edit_object """
    service = c['my_object']
    try: c['command_line'] = service.get_effective_command_line()
    except: c['errors'].append( "Configuration error while looking up command_line")

    #try: c['effective_servicegroups'] = service.get_effective_servicegroups()
    #except: c['errors'].append( "Configuration error while looking up servicegroups")

    try: c['effective_contacts'] = service.get_effective_contacts()
    except: c['errors'].append( "Configuration error while looking up contacts")

    try: c['effective_contactgroups'] = service.get_effective_contact_groups()
    except: c['errors'].append( "Configuration error while looking up contact_groups")

    try: c['object_macros'] = service.get_all_macros()
    except: c['errors'].append( "Configuration error while looking up macros")
    return render_to_response('edit_service.html', c, context_instance = RequestContext(request))
def _edit_host( request, c):
    """ This is a helper function to edit_object """
    host = c['my_object']
    if not c.has_key('errors'): c['errors'] = []

    try: c['effective_services'] = host.get_effective_services()
    except: c['errors'].append( "Configuration error while looking up services")

    try: c['command_line'] = host.get_effective_command_line()
    except: c['errors'].append( "Configuration error while looking up command_line")

    try: c['effective_hostgroups'] = host.get_effective_hostgroups()
    except: c['errors'].append( "Configuration error while looking up hostgroups")

    try: c['effective_contacts'] = host.get_effective_contacts()
    except: c['errors'].append( "Configuration error while looking up contacts")

    try: c['effective_contactgroups'] = host.get_effective_contact_groups()
    except: c['errors'].append( "Configuration error while looking up contact_groups")

    try: c['object_macros'] = host.get_all_macros()
    except: c['errors'].append( "Configuration error while looking up macros")

    return render_to_response('edit_host.html', c, context_instance = RequestContext(request))

def config_health( request  ):
    c = dict()
    c['messages'] = m = []
    c['object_health'] = s = {}
    c['booleans'] = {}
    services_no_description = Model.Service.objects.filter(register="1", service_description=None)
    hosts_without_contacts = []
    hosts_without_services =[]
    objects_with_invalid_parents = []
    services_without_contacts = []
    services_using_hostgroups = []
    services_without_icon_image = []
    for i in Model.ObjectDefinition.objects.all:
        continue
        try:
            i.get_parents()
        except ValueError:
            objects_with_invalid_parents.append(i)
    for i in Model.Host.objects.filter(register="1"):
            if i['contacts'] is None and i['contact_groups'] is None:
                hosts_without_contacts.append(i)
            try:
                if i.get_effective_services() == []:
                    hosts_without_services.append(i)
            except:
                pass
    for i in Model.Service.objects.filter(register="1"):
            if i['contacts'] is None and i['contact_groups'] is None:
                services_without_contacts.append(i)
            if i['hostgroups'] is not None:
                services_using_hostgroups.append(i)
            if i['icon_image'] is None:
                services_without_icon_image.append(i)
    c['booleans']['Nagios Service has been reloaded since last configuration change'] = not Model.config.needs_reload()
    c['booleans']['Adagios configuration cache is up-to-date'] = not Model.config.needs_reparse()
    c['errors'] = Model.config.errors
    import okconfig
    c['booleans']['OKConfig is installed and working'] = okconfig.is_valid()
    s['Parser errors'] = Model.config.errors
    s['Services with no "service_description"'] = services_no_description
    s['Hosts without any contacts'] = hosts_without_contacts
    s['Services without any contacts'] = services_without_contacts
    s['Objects with invalid "use" attribute'] = objects_with_invalid_parents
    s['Services applied to hostgroups'] = services_using_hostgroups
    s['Services without a logo'] = services_without_icon_image
    s['Hosts without Service Checks'] = hosts_without_services
    if request.GET.has_key('show') and s.has_key( request.GET['show'] ):
        objects =  s[request.GET['show']]
        return list_objects(request,display_these_objects=objects )
    else:
        return render_to_response('suggestions.html', c, context_instance = RequestContext(request))

def show_plugins(request):
    """ Finds all command_line arguments, and shows missing plugins """
    c = {}
    missing_plugins = []
    existing_plugins = []
    finished = []
    services = Model.Service.objects.all
    common_interpreters = ['perl','python','sh','bash']
    for s in services:
        if not 'check_command' in s._defined_attributes: continue
        check_command = s.check_command.split('!')[0]
        if check_command in finished: continue
        finished.append( check_command )
        try:
            command_line = s.get_effective_command_line()
        except KeyError:
            continue
        if command_line is None: continue
        command_line = command_line.split()
        command_name = command_line.pop(0)
        if command_name in common_interpreters: command_name = command_line.pop(0)
        if os.path.exists(command_name):
            existing_plugins.append( (check_command, command_name) )
        else:
            missing_plugins.append( (check_command, command_name) )
    c['missing_plugins'] = missing_plugins
    c['existing_plugins'] = existing_plugins
    return render_to_response('show_plugins.html', c, context_instance = RequestContext(request))

def view_parents(request):
    c = {}
    parents = {}
    hosts = Host.objects.all
    for h in hosts:
        for parent in h.get_parents():
            name = parent.name
            if not parents.has_key( name ):
                parents[ name ] = {'children':[], 'num_children':0, 'name':name}
            parents[name]['children'].append ( h )
            parents[name]['num_children'] += 1
    c['parents'] = []
    for i in parents.keys():
        c['parents'].append( parents[i] )
    return render_to_response('parents.html', c, context_instance = RequestContext(request))
def view_nagios_cfg(request):
    c = {'filename': Model.config.cfg_file, 'content': Model.config.maincfg_values}
    c['content'].sort()
    return render_to_response('edit_configfile.html', c, context_instance = RequestContext(request))

def add_service(request):
    c = {}
    c.update(csrf(request))
    c['form'] = AddServiceToHostForm()
    c['messages'] = []
    c['errors'] = []
    c['filename'] = Model.config.cfg_file
    if request.method == 'POST':
        c['form'] = form = AddServiceToHostForm(data=request.POST)
        if form.is_valid():
            host_name =  form.cleaned_data['host_name']
            host = Model.Host.objects.get_by_shortname(host_name)
            service = form.cleaned_data['service']
            new_service = Model.Service()
            new_service.host_name = host_name
            new_service.use = service
            new_service.set_filename(host.get_filename())
            new_service.reload_object()
            new_service.save()
            #Model.Service.objects.clean_cache()
            #Model.config = None
            #Model.Service.objects.get_by_id(new_service.get_id())
            c['my_object'] = new_service
            return HttpResponseRedirect( reverse('objectbrowser.views.edit_object', args=[new_service.get_id()] ) )

    return render_to_response('add_service.html', c,context_instance = RequestContext(request))

def edit_many(request):
    """ Edit multiple objects with one post """
    c = {}
    c.update(csrf(request))
    c['messages'] = []
    c['errors'] = []
    c['objects'] = objects = []
    c['form'] = EditManyForm(objects=objects)

    if request.method == 'GET':
        # We only call get when we are testing stuff
        c['objects'] = Model.Timeperiod.objects.all
    if request.method == "POST":
        # Post items starting with "hidden_" will be displayed on the resulting web page
        # Post items starting with "change_" will be modified
        for i in request.POST.keys():
            if i.startswith('change_'):
                my_id = i[ len('change_'): ]
                my_obj = ObjectDefinition.objects.get_by_id( my_id )
                objects.append( my_obj )
        c['form'] = EditManyForm(objects=objects,data=request.POST)
        if c['form'].is_valid():
            c['form'].save()
            for i in c['form'].changed_objects:
                c['messages'].append( "saved changes to %s %s" % (i.object_type, i.get_shortname() ))

    return render_to_response('edit_many.html', c, context_instance = RequestContext(request))

def delete_object(request, object_id):
    ''' View to Delete a single object definition '''
    c = {}
    c.update(csrf(request))
    c['messages'] = []
    c['errors'] = []
    c['object'] = my_obj = Model.ObjectDefinition.objects.get_by_id(object_id)
    if request.method == 'POST':
        my_obj.delete()
        print "my_obj deleted"
        return HttpResponseRedirect( reverse('objectbrowser.views.list_object_types' ) )
    return render_to_response('delete_object.html', c, context_instance = RequestContext(request))


def delete_many(request, object_ids):
    return NotImplementedError
