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

from django.shortcuts import render_to_response, redirect, HttpResponse, Http404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
import os
from os.path import dirname

from pynag.Model import ObjectDefinition, string_to_class
from pynag import Model
from pynag.Parsers import status
import pynag.Utils
from collections import defaultdict, namedtuple
import pynag.Model

from adagios import settings
from adagios.objectbrowser.forms import *
from adagios.views import adagios_decorator


@adagios_decorator
def home(request):
    return redirect('adagios')


@adagios_decorator
def list_object_types(request):
    """ Collects statistics about pynag objects and returns to template """
    c = {}
    return render_to_response('list_object_types.html', c, context_instance=RequestContext(request))


@adagios_decorator
def geek_edit(request, object_id):
    """ Function handles POST requests for the geek edit form """
    c = {}
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = []

    # Get our object
    try:
        o = ObjectDefinition.objects.get_by_id(id=object_id)
    except Exception, e:
        # This is an ugly hack. If unknown object ID was specified and it so happens to
        # Be the same as a brand new empty object definition we will assume that we are
        # to create a new object definition instead of throwing error because ours was
        # not found.
        for i in Model.string_to_class.values():
            if i().get_id() == object_id:
                o = i()
                break
        else:
            c['error_summary'] = _('Unable to find object')
            c['error'] = e
            return render_to_response('error.html', c, context_instance=RequestContext(request))
    c['my_object'] = o
    if request.method == 'POST':
        # Manual edit of the form
        form = GeekEditObjectForm(pynag_object=o, data=request.POST)
        if form.is_valid():
            try:
                form.save()
                m.append("Object Saved manually to '%s'" % o['filename'])
            except Exception, e:
                c['errors'].append(e)
                return render_to_response('edit_object.html', c, context_instance=RequestContext(request))
        else:
            c['errors'].append(_("Problem with saving object"))
            return render_to_response('edit_object.html', c, context_instance=RequestContext(request))
    else:
        form = GeekEditObjectForm(
            initial={'definition': o['meta']['raw_definition'], })

    c['geek_edit'] = form
    # Lets return the user to the general edit_object form
    return HttpResponseRedirect(reverse('edit_object', kwargs={'object_id': o.get_id()}))


@adagios_decorator
def advanced_edit(request, object_id):
    """ Handles POST only requests for the "advanced" object edit form. """
    c = {}
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = []
    # Get our object
    try:
        o = ObjectDefinition.objects.get_by_id(id=object_id)
        c['my_object'] = o
    except Exception, e:
        # This is an ugly hack. If unknown object ID was specified and it so happens to
        # Be the same as a brand new empty object definition we will assume that we are
        # to create a new object definition instead of throwing error because ours was
        # not found.
        for i in Model.string_to_class.values():
            if i().get_id() == object_id:
                o = i()
                break
        else:
            c['error_summary'] = _('Unable to get object')
            c['error'] = e
            return render_to_response('error.html', c, context_instance=RequestContext(request))

    if request.method == 'POST':
        # User is posting data into our form
        c['advanced_form'] = AdvancedEditForm(
            pynag_object=o, initial=o._original_attributes, data=request.POST)
        if c['advanced_form'].is_valid():
            try:
                c['advanced_form'].save()
                m.append(_("Object Saved to %(filename)s") % o)
            except Exception, e:
                c['errors'].append(e)
                return render_to_response('edit_object.html', c, context_instance=RequestContext(request))
    else:
            c['errors'].append(_("Problem reading form input"))
            return render_to_response('edit_object.html', c, context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('edit_object', args=[o.get_id()]))


@adagios_decorator
def edit_object(request, object_id=None):
    """ Brings up an edit dialog for one specific object.

        If an object_id is specified, bring us to that exact object.

        Otherwise we expect some search arguments to have been provided via querystring
    """
    c = {}
    c.update(csrf(request))
    c['messages'] = []
    c['errors'] = []
    my_object = None  # This is where we store our item that we are editing

    # If object_id was not provided, lets see if anything was given to us in a querystring
    if not object_id:
        objects = pynag.Model.ObjectDefinition.objects.filter(**request.GET)
        if len(objects) == 1:
            my_object = objects[0]
        else:
            return search_objects(request)
    else:
        try:
            my_object = pynag.Model.ObjectDefinition.objects.get_by_id(object_id)
        except KeyError:
            c['error_summary'] = _('Could not find any object with id="%(object_id)s" :/') % {'object_id': object_id}
            c['error_type'] = _("object not found")
            return render_to_response('error.html', c, context_instance=RequestContext(request))

    if request.method == 'POST':
        # User is posting data into our form
        c['form'] = PynagForm(
            pynag_object=my_object,
            initial=my_object._original_attributes,
            data=request.POST
        )
        if c['form'].is_valid():
            try:
                c['form'].save()
                c['messages'].append(_("Object Saved to %(filename)s") % my_object)
                return HttpResponseRedirect(reverse('edit_object', kwargs={'object_id': my_object.get_id()}))
            except Exception, e:
                c['errors'].append(e)
        else:
            c['errors'].append(_("Could not validate form input"))
    if 'form' not in c:
        c['form'] = PynagForm(pynag_object=my_object, initial=my_object._original_attributes)
    c['my_object'] = my_object
    c['geek_edit'] = GeekEditObjectForm(
        initial={'definition': my_object['meta']['raw_definition'], })
    c['advanced_form'] = AdvancedEditForm(
        pynag_object=my_object, initial=my_object._original_attributes)

    try:
        c['effective_hosts'] = my_object.get_effective_hosts()
    except KeyError, e:
        c['errors'].append(_("Could not find host: %(error)s") % {'error': str(e)})
    except AttributeError:
        pass

    try:
        c['effective_parents'] = my_object.get_effective_parents(cache_only=True)
    except KeyError, e:
        c['errors'].append(_("Could not find parent: %(error)s") % {'error': str(e)})

    # Every object type has some special treatment, so lets resort
    # to appropriate helper function
    if False:
        pass
    elif my_object['object_type'] == 'servicegroup':
        return _edit_servicegroup(request, c)
    elif my_object['object_type'] == 'hostdependency':
        return _edit_hostdependency(request, c)
    elif my_object['object_type'] == 'service':
        return _edit_service(request, c)
    elif my_object['object_type'] == 'contactgroup':
        return _edit_contactgroup(request, c)
    elif my_object['object_type'] == 'hostgroup':
        return _edit_hostgroup(request, c)
    elif my_object['object_type'] == 'host':
        return _edit_host(request, c)
    elif my_object['object_type'] == 'contact':
        return _edit_contact(request, c)
    elif my_object['object_type'] == 'command':
        return _edit_command(request, c)
    elif my_object['object_type'] == 'servicedependency':
        return _edit_servicedependency(request, c)
    elif my_object['object_type'] == 'timeperiod':
        return _edit_timeperiod(request, c)
    else:
        return render_to_response('edit_object.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_contact(request, c):
    """ This is a helper function to edit_object """
    try:
        c['effective_contactgroups'] = c[
            'my_object'].get_effective_contactgroups()
    except KeyError, e:
        c['errors'].append(_("Could not find contact: %(error)s") % {'error': str(e)})

    return render_to_response('edit_contact.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_service(request, c):
    """ This is a helper function to edit_object """
    service = c['my_object']
    try:
        c['command_line'] = service.get_effective_command_line()
    except KeyError:
        c['command_line'] = None
    try:
        c['object_macros'] = service.get_all_macros()
    except KeyError:
        c['object_macros'] = None
    # Get the current status from Nagios
    try:
        s = status()
        s.parse()
        c['status'] = s.get_servicestatus(
            service['host_name'], service['service_description'])
        current_state = c['status']['current_state']
        if current_state == "0":
            c['status']['text'] = 'OK'
            c['status']['css_label'] = 'label-success'
        elif current_state == "1":
            c['status']['text'] = 'Warning'
            c['status']['css_label'] = 'label-warning'
        elif current_state == "2":
            c['status']['text'] = 'Critical'
            c['status']['css_label'] = 'label-important'
        else:
            c['status']['text'] = 'Unknown'
            c['status']['css_label'] = 'label-inverse'
    except Exception:
        pass

    try:
        c['effective_servicegroups'] = service.get_effective_servicegroups()
    except KeyError, e:
        c['errors'].append(_("Could not find servicegroup: %(error)s") % {'error': str(e)})

    try:
        c['effective_contacts'] = service.get_effective_contacts()
    except KeyError, e:
        c['errors'].append(_("Could not find contact: %(error)s") % {'error': str(e)})

    try:
        c['effective_contactgroups'] = service.get_effective_contact_groups()
    except KeyError, e:
        c['errors'].append(_("Could not find contact_group: %(error)s") % {'error': str(e)})

    try:
        c['effective_hostgroups'] = service.get_effective_hostgroups()
    except KeyError, e:
        c['errors'].append(_("Could not find hostgroup: %(error)s") % {'error': str(e)})

    try:
        c['effective_command'] = service.get_effective_check_command()
    except KeyError, e:
        if service.check_command is not None:
            c['errors'].append(_("Could not find check_command: %(error)s") % {'error': str(e)})
        elif service.register != '0':
            c['errors'].append(_("You need to define a check command"))

    # For the check_command editor, we inject current check_command and a list
    # of all check_commands
    c['check_command'] = (service.check_command or '').split("!")[0]
    c['command_names'] = map(
        lambda x: x.get("command_name", ''), Model.Command.objects.all)
    if c['check_command'] in (None, '', 'None'):
        c['check_command'] = ''

    if service.hostgroup_name and service.hostgroup_name != 'null':
        c['errors'].append(_("This Service is applied to every host in hostgroup %(hostgroup_name)s") % {'hostgroup_name': service.hostgroup_name})
    host_name = service.host_name or ''
    if ',' in host_name:
        c['errors'].append(_("This Service is applied to multiple hosts"))
    return render_to_response('edit_service.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_contactgroup(request, c):
    """ This is a helper function to edit_object """
    try:
        c['effective_contactgroups'] = c[
            'my_object'].get_effective_contactgroups()
    except KeyError, e:
        c['errors'].append(_("Could not find contact_group: %(error)s") % {'error': str(e)})

    try:
        c['effective_contacts'] = c['my_object'].get_effective_contacts()
    except KeyError, e:
        c['errors'].append("Could not find contact: %s" % str(e))

    try:
        c['effective_memberof'] = Model.Contactgroup.objects.filter(
            contactgroup_members__has_field=c['my_object'].contactgroup_name)
    except Exception, e:
        c['errors'].append(e)
    return render_to_response('edit_contactgroup.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_hostgroup(request, c):
    """ This is a helper function to edit_object """
    hostgroup = c['my_object']
    try:
        c['effective_services'] = sorted(
            hostgroup.get_effective_services(), key=lambda x: x.get_description())
    except KeyError, e:
        c['errors'].append(_("Could not find service: %(error)s") % {'error': str(e)})
    try:
        c['effective_memberof'] = Model.Hostgroup.objects.filter(
            hostgroup_members__has_field=c['my_object'].hostgroup_name)
    except Exception, e:
        c['errors'].append(e)
    return render_to_response('edit_hostgroup.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_servicegroup(request, c):
    """ This is a helper function to edit_object """
    try:
        c['effective_memberof'] = Model.Servicegroup.objects.filter(
            servicegroup_members__has_field=c['my_object'].servicegroup_name)
    except Exception, e:
        c['errors'].append(e)
    return render_to_response('edit_servicegroup.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_command(request, c):
    """ This is a helper function to edit_object """
    return render_to_response('edit_command.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_hostdependency(request, c):
    """ This is a helper function to edit_object """
    return render_to_response('edit_hostdepedency.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_servicedependency(request, c):
    """ This is a helper function to edit_object """
    return render_to_response('_edit_servicedependency.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_timeperiod(request, c):
    """ This is a helper function to edit_object """
    return render_to_response('edit_timeperiod.html', c, context_instance=RequestContext(request))


@pynag.Utils.cache_only
def _edit_host(request, c):
    """ This is a helper function to edit_object """
    host = c['my_object']
    try:
        c['command_line'] = host.get_effective_command_line()
    except KeyError:
        c['command_line'] = None
    try:
        c['object_macros'] = host.get_all_macros()
    except KeyError:
        c['object_macros'] = None

    if not 'errors' in c:
        c['errors'] = []

    try:
        c['effective_services'] = sorted(
            host.get_effective_services(), key=lambda x: x.get_description())
    except KeyError, e:
        c['errors'].append(_("Could not find service: %(error)s") % {'error': str(e)})

    try:
        c['effective_hostgroups'] = host.get_effective_hostgroups()
    except KeyError, e:
        c['errors'].append(_("Could not find hostgroup: %(error)s") % {'error': str(e)})

    try:
        c['effective_contacts'] = host.get_effective_contacts()
    except KeyError, e:
        c['errors'].append(_("Could not find contact: %(error)s") % {'error': str(e)})

    try:
        c['effective_contactgroups'] = host.get_effective_contact_groups()
    except KeyError, e:
        c['errors'].append(_("Could not find contact_group: %(error)s") % {'error': str(e)})

    try:
        c['effective_command'] = host.get_effective_check_command()
    except KeyError, e:
        if host.check_command is not None:
            c['errors'].append(_("Could not find check_command: %(error)s") % {'error': str(e)})
        elif host.register != '0':
            c['errors'].append(_("You need to define a check command"))
    try:
        s = status()
        s.parse()
        c['status'] = s.get_hoststatus(host['host_name'])
        current_state = c['status']['current_state']
        if int(current_state) == 0:
            c['status']['text'] = 'UP'
            c['status']['css_label'] = 'label-success'
        else:
            c['status']['text'] = 'DOWN'
            c['status']['css_label'] = 'label-important'
    except Exception:
        pass

    return render_to_response('edit_host.html', c, context_instance=RequestContext(request))


@adagios_decorator
def config_health(request):
    """ Display possible errors in your nagios config
    """
    c = dict()
    c['messages'] = []
    c['object_health'] = s = {}
    c['booleans'] = {}
    services_no_description = Model.Service.objects.filter(
        register="1", service_description=None)
    hosts_without_contacts = []
    hosts_without_services = []
    objects_with_invalid_parents = []
    services_without_contacts = []
    services_using_hostgroups = []
    services_without_icon_image = []
    c['booleans'][
        _('Nagios Service has been reloaded since last configuration change')] = not Model.config.needs_reload()
    c['booleans'][
        _('Adagios configuration cache is up-to-date')] = not Model.config.needs_reparse()
    for i in Model.config.errors:
        if i.item:
            Class = Model.string_to_class[i.item['meta']['object_type']]
            i.model = Class(item=i.item)
    c['parser_errors'] = Model.config.errors
    try:
        import okconfig
        c['booleans'][
            _('OKConfig is installed and working')] = okconfig.is_valid()
    except Exception:
        c['booleans'][_('OKConfig is installed and working')] = False
    s['Parser errors'] = Model.config.errors
    s['Services with no "service_description"'] = services_no_description
    s['Hosts without any contacts'] = hosts_without_contacts
    s['Services without any contacts'] = services_without_contacts
    s['Objects with invalid "use" attribute'] = objects_with_invalid_parents
    s['Services applied to hostgroups'] = services_using_hostgroups
    s['Services without a logo'] = services_without_icon_image
    s['Hosts without Service Checks'] = hosts_without_services
    if request.GET.has_key('show') and s.has_key(request.GET['show']):
        objects = s[request.GET['show']]
        return search_objects(request, objects=objects)
    else:
        return render_to_response('suggestions.html', c, context_instance=RequestContext(request))


@adagios_decorator
def show_plugins(request):
    """ Finds all command_line arguments, and shows missing plugins """
    c = {}
    missing_plugins = []
    existing_plugins = []
    finished = []
    services = Model.Service.objects.all
    common_interpreters = ['perl', 'python', 'sh', 'bash']
    for s in services:
        if not 'check_command' in s._defined_attributes:
            continue
        check_command = s.check_command.split('!')[0]
        if check_command in finished:
            continue
        finished.append(check_command)
        try:
            command_line = s.get_effective_command_line()
        except KeyError:
            continue
        if command_line is None:
            continue
        command_line = command_line.split()
        command_name = command_line.pop(0)
        if command_name in common_interpreters:
            command_name = command_line.pop(0)
        if os.path.exists(command_name):
            existing_plugins.append((check_command, command_name))
        else:
            missing_plugins.append((check_command, command_name))
    c['missing_plugins'] = missing_plugins
    c['existing_plugins'] = existing_plugins
    return render_to_response('show_plugins.html', c, context_instance=RequestContext(request))


@adagios_decorator
def edit_nagios_cfg(request):
    """ This views is made to make modifications to nagios.cfg
    """
    from pynag.Model.all_attributes import main_config
    c = {'filename': Model.config.cfg_file}
    c['content'] = []

    for conf in sorted(main_config):
        values = []
        Model.config.parse_maincfg()
        for k, v in Model.config.maincfg_values:
            if conf == k:
                values.append(v)
        c['content'].append({
            'doc': main_config[conf]['doc'],
            'title': main_config[conf]['title'],
            'examples': main_config[conf]['examples'],
            'format': main_config[conf]['format'],
            'options': main_config[conf]['options'],
            'key': conf,
            'values': values
        })

    for key, v in Model.config.maincfg_values:
        if key not in main_config:
            c['content'].append({
                'title': _('No documentation found'),
                'key': key,
                'values': [v],
                'doc': _('This seems to be an undefined option and no documentation was found for it. Perhaps it is'
                       'mispelled.')
            })
    c['content'] = sorted(c['content'], key=lambda cfgitem: cfgitem['key'])
    return render_to_response('edit_configfile.html', c, context_instance=RequestContext(request))


@adagios_decorator
def bulk_edit(request):
    """ Edit multiple objects with one post """
    c = {}
    c.update(csrf(request))
    c['messages'] = []
    c['errors'] = []
    c['objects'] = objects = []

    # Newer, alternative way to input items from the post data is in the form of
    # object_type=shortname
    # i.e. timeperiod=24x7, timeperiod=workhours
    for i in _querydict_to_objects(request):
        objects.append(i)

    if request.method == 'GET':
        if len(objects) == 1:
            return HttpResponseRedirect(reverse('edit_object', kwargs={'object_id': objects[0].get_id()}), )
        c['form'] = BulkEditForm(objects=objects)
    if request.method == "POST":
        c['form'] = BulkEditForm(objects=objects, data=request.POST)
        c['objects'] = c['form'].all_objects
        if c['form'].is_valid():
            try:
                c['form'].save()
                for i in c['form'].changed_objects:
                    c['messages'].append(
                        _("saved changes to %(object_type)s '%(description)s'") % {'object_type': i.object_type,
                                                                                   'description': i.get_description(),
                                                                                    })
                c['success'] = "success"
            except IOError, e:
                c['errors'].append(e)

    return render_to_response('bulk_edit.html', c, context_instance=RequestContext(request))

@adagios_decorator
def bulk_delete(request):
    """ Edit delete multiple objects with one post """
    c = {}
    c.update(csrf(request))
    c['messages'] = []
    c['errors'] = []
    c['objects'] = objects = []
    c['form'] = BulkDeleteForm(objects=objects)

    # Newer, alternative way to input items from the post data is in the form of
    # object_type=shortname
    # i.e. timeperiod=24x7, timeperiod=workhours
    for i in _querystring_to_objects(request.GET or request.POST):
        try:
            obj = pynag.Model.string_to_class[i.object_type].objects.get_by_shortname(i.description)
            if obj not in objects:
                objects.append(obj)
        except KeyError:
            c['errors'].append(_("Could not find %(object_type)s '%(description)s' "
                                 "Maybe it has already been deleted.") % {'object_type': i.object_type, 
                                                                          'description': i.description})
    if request.method == "GET" and len(objects) == 1:
        return HttpResponseRedirect(reverse('delete_object', kwargs={'object_id': objects[0].get_id()}), )

    if request.method == "POST":
        # Post items starting with "hidden_" will be displayed on the resulting web page
        # Post items starting with "change_" will be modified
        for i in request.POST.keys():
            if i.startswith('change_'):
                my_id = i[len('change_'):]
                my_obj = ObjectDefinition.objects.get_by_id(my_id)
                if my_obj not in objects:
                    objects.append(my_obj)

        c['form'] = BulkDeleteForm(objects=objects, data=request.POST)
        if c['form'].is_valid():
            try:
                c['form'].delete()
                c['success'] = "Success"
                for i in c['form'].changed_objects:
                    c['messages'].append(
                        "Deleted %s %s" % (i.object_type, i.get_description()))
            except IOError, e:
                c['errors'].append(e)

    return render_to_response('bulk_delete.html', c, context_instance=RequestContext(request))

@adagios_decorator
def bulk_copy(request):
    """ Copy multiple objects with one post """
    c = {}
    c.update(csrf(request))
    c['messages'] = []
    c['errors'] = []
    c['objects'] = objects = []
    c['form'] = BulkCopyForm(objects=objects)

    # Newer, alternative way to input items from the post data is in the form of
    # object_type=shortname
    # i.e. timeperiod=24x7, timeperiod=workhours
    for i in _querystring_to_objects(request.GET or request.POST):
        try:
            obj = pynag.Model.string_to_class[i.object_type].objects.get_by_shortname(i.description)
            if obj not in objects:
                objects.append(obj)
        except KeyError:
            c['errors'].append(_("Could not find %(object_type)s '%(description)s'") % {'object_type': i.object_type,
                                                                                        'description': i.description,
                                                                                       })
    if request.method == "GET" and len(objects) == 1:
        return HttpResponseRedirect(reverse('copy_object', kwargs={'object_id': objects[0].get_id()}), )
    elif request.method == "POST":
        # Post items starting with "hidden_" will be displayed on the resulting web page
        # Post items starting with "change_" will be modified
        for i in request.POST.keys():
            if i.startswith('change_'):
                my_id = i[len('change_'):]
                my_obj = ObjectDefinition.objects.get_by_id(my_id)
                if my_obj not in objects:
                    objects.append(my_obj)

        c['form'] = BulkCopyForm(objects=objects, data=request.POST)
        if c['form'].is_valid():
            try:
                c['form'].save()
                c['success'] = "Success"
                for i in c['form'].changed_objects:
                    c['messages'].append(
                        _("Successfully copied %(object_type)s %(description)s") % {'object_type': i.object_type,
                                                                                    'description': i.get_description()})
            except IOError, e:
                c['errors'].append(e)

    return render_to_response('bulk_copy.html', c, context_instance=RequestContext(request))

@adagios_decorator
def delete_object_by_shortname(request, object_type, shortname):
    """ Same as delete_object() but uses object type and shortname instead of object_id
    """
    obj_type = Model.string_to_class[object_type]
    my_obj = obj_type.objects.get_by_shortname(shortname)
    return delete_object(request, object_id=my_obj.get_id())

@adagios_decorator
def delete_object(request, object_id):
    """ View to Delete a single object definition """
    c = {}
    c.update(csrf(request))
    c['messages'] = []
    c['errors'] = []
    c['object'] = my_obj = Model.ObjectDefinition.objects.get_by_id(object_id)
    c['form'] = DeleteObjectForm(pynag_object=my_obj, initial=request.GET)
    if request.method == 'POST':
        try:
            c['form'] = f = DeleteObjectForm(
                pynag_object=my_obj, data=request.POST)
            if f.is_valid():
                f.delete()
            return HttpResponseRedirect(reverse('objectbrowser') + "#" + my_obj.object_type)
        except Exception, e:
            c['errors'].append(e)
    return render_to_response('delete_object.html', c, context_instance=RequestContext(request))


@adagios_decorator
def copy_object(request, object_id):
    """ View to Copy a single object definition """
    c = {}
    c.update(csrf(request))
    c['messages'] = []
    c['errors'] = []
    c['object'] = my_obj = Model.ObjectDefinition.objects.get_by_id(object_id)

    if request.method == 'GET':
        c['form'] = CopyObjectForm(pynag_object=my_obj, initial=request.GET)
    elif request.method == 'POST':
        c['form'] = f = CopyObjectForm(pynag_object=my_obj, data=request.POST)
        if f.is_valid():
            try:
                f.save()
                c['copied_objects'] = f.copied_objects
                c['success'] = 'success'
            except IndexError, e:
                c['errors'].append(e)
    return render_to_response('copy_object.html', c, context_instance=RequestContext(request))


@adagios_decorator
def add_object(request, object_type):
    """ Friendly wizard on adding a new object of any particular type
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['object_type'] = object_type

    if request.method == 'GET' and object_type == 'template':
        c['form'] = AddTemplateForm(initial=request.GET)
    elif request.method == 'GET':
        c['form'] = AddObjectForm(object_type, initial=request.GET)
    elif request.method == 'POST' and object_type == 'template':
        c['form'] = AddTemplateForm(data=request.POST)
    elif request.method == 'POST':
        c['form'] = AddObjectForm(object_type, data=request.POST)
    else:
        c['errors'].append(_("Something went wrong while calling this form"))

    # This is what happens in post regardless of which type of form it is
    if request.method == 'POST' and 'form' in c:
        # If form is valid, save object and take user to edit_object form.
        if c['form'].is_valid():
            c['form'].save()
            object_id = c['form'].pynag_object.get_id()
            return HttpResponseRedirect(reverse('edit_object', kwargs={'object_id': object_id}), )
        else:
            c['errors'].append(_('Could not validate form input'))

    return render_to_response('add_object.html', c, context_instance=RequestContext(request))


def _querystring_to_objects(dictionary):
    """ Finds all nagios objects in a querystring and returns a list of objects

    >>> dictionary = {'host':('localhost1', 'localhost2'),}
    >>> print _querystring_to_objects
    {'host':('localhost1','localhost2')}
    """
    result = []
    Object = namedtuple('Object', 'object_type description')
    for object_type in string_to_class.keys():
        objects = dictionary.getlist(object_type)
        for i in objects:
            obj = (Object(object_type, i))
            result.append(obj)
    return result


def _querydict_to_objects(request, raise_on_not_found=False):
    """ Finds all object specifications in a querydict and returns a list of pynag objects

    Typically this is used to name specific objects from the querystring.

    Valid input in the request is either id=object_id or object_type=short_name

    Arguments:
        request  - A django request object. Usually the data is in a querystring or POST data
                 - Example: host=localhost,service=localhost/Ping
        raise_on_not_found - Raise ValueError if some object is not found
    Returns:
        List of pynag objects
    """
    result = []
    mydict = request.GET or request.POST

    # Find everything in the querystring in the form of id=[object_ids]
    for object_id in mydict.getlist('id'):
        try:
            my_object = ObjectDefinition.objects.get_by_id(object_id)
            result.append(my_object)
        except Exception, e:
            if raise_on_not_found is True:
                raise e

    # Find everything in querystring in the form of object_type=[shortnames]
    for object_type,Class in string_to_class.items():
        objects = mydict.getlist(object_type)
        for shortname in objects:
            try:
                my_object = Class.objects.get_by_shortname(shortname)
                result.append(my_object)
            except Exception, e:
                # If a service was not found, check if it was registered in
                # some unusual way
                if object_type == 'service' and '/' in shortname:
                    host_name,service_description = shortname.split('/', 1)
                    result.append(_find_service(host_name, service_description))
                if raise_on_not_found is True:
                    raise e
    return result


def _find_service(host_name, service_description):
    """ Returns pynag.Model.Service matching our search filter """
    result = pynag.Model.Service.objects.filter(host_name__has_field=host_name, service_description=service_description)

    if not result:
        host = pynag.Model.Host.objects.get_by_shortname(host_name, cache_only=True)
        for i in host.get_effective_services():
            if i.service_description == service_description:
                result = [i]
                break
    return result[0]


@adagios_decorator
def add_to_group(request, group_type=None, group_name=''):
    """ Add one or more objects into a group
    """

    c = {}
    messages = []
    errors = []
    if not group_type:
        raise Exception(_("Please include group type"))
    if request.method == 'GET':
        objects = _querystring_to_objects(request.GET)
    elif request.method == 'POST':
        objects = _querystring_to_objects(request.GET)
        for i in objects:
            try:
                obj = pynag.Model.string_to_class[i.object_type].objects.get_by_shortname(i.description)
                if group_type == 'contactgroup':
                    obj.add_to_contactgroup(group_name)
                elif group_type == 'hostgroup':
                    obj.add_to_hostgroup(group_name)
                elif group_type == 'servicegroup':
                    obj.add_to_servicegroup(group_name)
                return HttpResponse("Success")
            except Exception, e:
                errortype = e.__dict__.get('__name__') or str(type(e))
                error = str(e)
                return HttpResponse(_("Failed to add object: %(errortype)s %(error)s ") % {'errortype': errortype,
                                                                                           'error': error,
                                                                                           })

    return render_to_response('add_to_group.html', locals(), context_instance=RequestContext(request))


@adagios_decorator
def edit_all(request, object_type, attribute_name):
    """  Edit many objects at once, changing only a single attribute

    Example:
        Edit notes_url of all services
    """
    messages = []
    errors = []
    objects = Model.string_to_class.get(object_type).objects.all
    objects = map(lambda x: (x.get_shortname, x.get(attribute_name)), objects)
    return render_to_response('edit_all.html', locals(), context_instance=RequestContext(request))



@adagios_decorator
def search_objects(request, objects=None):
    """ Displays a list of pynag objects, search parameters can be entered via querystring

        Arguments:
            objects -- List of pynag objects to show. If it is not set,
                    -- We will use querystring instead as search arguments
        example:
         /adagios/objectbrowser/search?object_type=host&host_name__startswith=foo


    """
    messages = []
    errors = []
    if not objects:
        objects = pynag.Model.ObjectDefinition.objects.filter(**request.GET)

    # A special case, if no object was found, lets check if user was looking for a service
    # With its host_name / service_description pair, and the service is applied to hostgroup instead
    if not objects and request.GET.get('object_type') == 'service':
        host_name = request.GET.get('host_name')
        service_description = request.GET.get('service_description')
        shortname = request.GET.get('shortname')

        # If shortname was provided instead of host_name / service_description
        if not host_name and not service_description and shortname:
            host_name, service_description = shortname.split('/')

        # If at this point we have found some objects, then lets do a special workaround
        services = [_find_service(host_name, service_description)]
        errors.append(_('be careful'))

    return render_to_response('search_objects.html', locals(), context_instance=RequestContext(request))


@adagios_decorator
def copy_and_edit_object(request, object_id):
    """ Create a new object, and open up an edit dialog for it.

    If object_id is provided, that object will be copied into this one.
    """
    kwargs = {}
    for k, v in request.GET.items():
        if v in ('', None, 'None'):
            v = None
        kwargs[k] = v
    o = pynag.Model.ObjectDefinition.objects.get_by_id(object_id)
    o = o.copy(**kwargs)
    o = pynag.Model.ObjectDefinition.objects.filter(shortname=o.get_shortname(), object_type=o.object_type)[0]

    return HttpResponseRedirect(reverse('edit_object', kwargs={'object_id': o.get_id()}))


