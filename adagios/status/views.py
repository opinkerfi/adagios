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
from django.http import HttpResponse

import time
from os.path import dirname
from collections import defaultdict
import json
import traceback

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.encoding import smart_str
from django.core.context_processors import csrf

import pynag.Model
import pynag.Utils
import pynag.Control
import pynag.Plugins
import pynag.Model.EventHandlers
from pynag.Parsers import ParserError

import adagios.settings
from adagios.pnp.functions import run_pnp
from adagios.status import utils
import adagios.status.rest
import adagios.status.forms
import adagios.businessprocess
from django.core.urlresolvers import reverse

state = defaultdict(lambda: "unknown")
state[0] = "ok"
state[1] = "warning"
state[2] = "critical"

from adagios.views import error_handler, error_page


@error_handler
def status_parents(request):
    c = {}
    c['messages'] = []
    authuser = request.GET.get('contact_name', None)
    livestatus = utils.livestatus(request)
    all_hosts = livestatus.get_hosts()
    host_dict = {}
    map(lambda x: host_dict.__setitem__(x['name'], x), all_hosts)
    c['hosts'] = []

    for i in all_hosts:
        if len(i['childs']) > 0:
            c['hosts'].append(i)
            ok = 0
            crit = 0
            i['child_hosts'] = []
            for x in i['childs']:
                i['child_hosts'].append(host_dict[x])
                if host_dict[x]['state'] == 0:
                    ok += 1
                else:
                    crit += 1
            total = float(len(i['childs']))
            i['health'] = float(ok) / total * 100.0
            i['percent_ok'] = ok / total * 100
            i['percent_crit'] = crit / total * 100

    return render_to_response('status_parents.html', c, context_instance=RequestContext(request))


@error_handler
def _status(request):
    """ Helper function for a lot of status views, handles fetching of objects, populating context, and filtering, etc.

    Returns:
        hash map with request context
    Examples:
        c = _status(request)
        return render_to_response('status_parents.html', c, context_instance=RequestContext(request))
    """
    c = {}
    c['messages'] = []
    from collections import defaultdict
    authuser = request.GET.get('contact_name', None)
    livestatus = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config, authuser=authuser)
    all_hosts = livestatus.get_hosts()
    all_services = livestatus.get_services()
    all_contacts = livestatus.get_contacts()
    c['contacts'] = all_contacts
    c['current_contact'] = authuser
    c['request'] = request

    services = defaultdict(list)
    hosts = []
    search_filter = request.GET.copy()
    q = None
    if 'q' in search_filter:
        q = search_filter['q']
        del search_filter['q']
    my_services = pynag.Utils.grep(all_services, **search_filter)

    for service in my_services:
        # Tag the service with tags such as problems and unhandled
        tags = []
        if service['state'] != 0:
            tags.append('problem')
            tags.append('problems')
            if service['acknowledged'] == 0 and service['downtimes'] == []:
                tags.append('unhandled')
                service['unhandled'] = "unhandled"
            else:
                tags.append('ishandled')
                service['handled'] = "handled"
        else:
            tags.append('ok')
        if service['acknowledged'] == 1:
            tags.append('acknowledged')
        if service['downtimes'] != []:
            tags.append('downtime')
        service['tags'] = ' '.join(tags)

        service['status'] = state[service['state']]

        if q is not None:  # Something is in the search box:
            if q not in service['host_name'] and q not in service['description'] and q not in service['tags']:
                continue
        services[service['host_name']].append(service)

    #    services[service['host_name']].append(service)
    for host in all_hosts:
        host['num_problems'] = host['num_services_crit'] + \
            host['num_services_warn'] + host['num_services_unknown']
        host['children'] = host['services_with_state']
        if len(services[host['name']]) > 0:
            host['status'] = state[host['state']]
            host['services'] = services[host['name']]
            hosts.append(host)
    # Sort by service status
    hosts.sort(reverse=True, cmp=lambda a, b:
               cmp(a['num_problems'], b['num_problems']))
    c['services'] = services
    c['hosts'] = hosts
    seconds_in_a_day = 60 * 60 * 24
    today = time.time() % seconds_in_a_day  # midnight of today
    c['objects'] = hosts
    if request.GET.get('view', None) == 'servicegroups':
        servicegroups = livestatus.query('GET servicegroups')
        for i in servicegroups:
            i['children'] = i['members_with_state']
        c['objects'] = servicegroups
    if request.GET.get('view', None) == 'hostgroups':
        groups = livestatus.query('GET hostgroups')
        for i in groups:
            i['children'] = i['members_with_state']
        c['objects'] = groups
    return c


@error_handler
def status(request):
    """ Compatibility layer around status.views.services
    """
    #c = _status(request)
    # return render_to_response('status.html', c, context_instance=RequestContext(request))
    # Left here for compatibility reasons:
    return services(request)


@error_handler
def services(request):
    """ This view handles list of services  """
    c = {}
    c['messages'] = []
    c['errors'] = []
    fields = [
        'host_name', 'description', 'plugin_output', 'last_check', 'host_state', 'state',
        'last_state_change', 'acknowledged', 'downtimes', 'host_downtimes', 'comments_with_info']
    c['services'] = utils.get_services(request, fields=fields, **request.GET)
    return render_to_response('status_services.html', c, context_instance=RequestContext(request))


@error_handler
def snippets_log(request):
    """ Returns a html stub with the  snippet_statehistory_snippet.html
    """
    host_name = request.GET.get('host_name')
    service_description = request.GET.get('service_description')
    if not host_name:
        raise Exception("host_name is required")
    if not service_description or service_description == '_HOST_':
        # Get host logs
        log = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config).get_state_history(
            host_name=host_name, service_description=None)
    else:
        log = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config).get_state_history(
            host_name=host_name, service_description=service_description)

    c = {'log':log}
    # Create some state history progress bar from our logs:
    if len(c['log']) > 0:
        log = c['log']
        c['start_time'] = start_time = log[0]['time']
        c['end_time'] = end_time = log[-1]['time']
        now = time.time()

        total_duration = now - start_time
        state_hist = []
        start = start_time
        last_item = None
        css_hint = {}
        css_hint[0] = 'success'
        css_hint[1] = 'warning'
        css_hint[2] = 'danger'
        css_hint[3] = 'unknown'
        for i in log:
            i['duration_percent'] = 100 * i['duration'] / total_duration
            i['bootstrap_status'] = css_hint[i['state']]


    return render_to_response('snippets/status_statehistory_snippet.html', locals(), context_instance=RequestContext(request))



@error_handler
def status_detail(request, host_name=None, service_description=None):
    """ Displays status details for one host or service """
    c = {}
    c['messages'] = []
    c['errors'] = []

    host_name = request.GET.get('host_name')
    service_description = request.GET.get('service_description')
    livestatus = utils.livestatus(request)
    c['pnp_url'] = adagios.settings.pnp_url
    c['nagios_url'] = adagios.settings.nagios_url
    c['request'] = request
    now = time.time()
    seconds_in_a_day = 60 * 60 * 24
    seconds_passed_today = now % seconds_in_a_day
    today = now - seconds_passed_today  # midnight of today

    try:
        c['host'] = my_host = livestatus.get_host(host_name)
        my_host['object_type'] = 'host'
        my_host['short_name'] = my_host['name']
    except IndexError:
        c['errors'].append("Could not find any host named '%s'" % host_name)
        return error_page(request, c)

    if service_description is None:
        tmp = request.GET.get('service_description')
        if tmp is not None:
            return status_detail(request, host_name, service_description=tmp)
        primary_object = my_host
        c['service_description'] = '_HOST_'
        #c['log'] = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config).get_state_history(
        #    host_name=host_name, service_description=None)
    else:
        try:
            c['service'] = my_service = livestatus.get_service(
                host_name, service_description)
            my_service['object_type'] = 'service'
            c['service_description'] = service_description
            my_service['short_name'] = "%s/%s" % (
                my_service['host_name'], my_service['description'])
            primary_object = my_service
            #c['log'] = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config).get_state_history(
            #    host_name=host_name, service_description=service_description)
        except IndexError:
            c['errors'].append(
                "Could not find any service named '%s'" % service_description)
            return error_page(request, c)

    c['my_object'] = primary_object
    c['object_type'] = primary_object['object_type']

    # Friendly statusname (i.e. turn 2 into "critical")
    primary_object['status'] = state[primary_object['state']]

    # Plugin longoutput comes to us with special characters escaped. lets undo
    # that:
    primary_object['long_plugin_output'] = primary_object[
        'long_plugin_output'].replace('\\n', '\n')

    # Service list on the sidebar should be sorted
    my_host['services_with_info'] = sorted(
        my_host.get('services_with_info', []))
    c['host_name'] = host_name

    perfdata = primary_object['perf_data']
    perfdata = pynag.Utils.PerfData(perfdata)
    for i, datum in enumerate(perfdata.metrics):
        datum.i = i
        try:
            datum.status = state[datum.get_status()]
        except pynag.Utils.PynagError:
            datum.status = state[3]
    c['perfdata'] = perfdata.metrics

    # Get a complete list of network parents
    try:
        c['network_parents'] = reversed(_get_network_parents(host_name))
    except Exception, e:
        c['errors'].append(e)

    # Lets get some graphs
    try:
        tmp = run_pnp("json", host=host_name)
        tmp = json.loads(tmp)
    except Exception, e:
        tmp = []
        c['pnp4nagios_error'] = e
    c['graph_urls'] = tmp

    return render_to_response('status_detail.html', c, context_instance=RequestContext(request))


def _get_network_parents(host_name):
    """ Returns a list of hosts that are network parents (or grandparents) to host_name

     Every item in the list is a host dictionary from mk_livestatus

     Returns:
        List of lists

     Example:
        _get_network_parents('remotehost.example.com')
        [
            ['gateway.example.com', 'mod_gearman.example.com'],
            ['localhost'],
        ]
    """
    result = []
    livestatus = pynag.Parsers.mk_livestatus()
    if isinstance(host_name, unicode):
        host_name = smart_str(host_name)

    if isinstance(host_name, str):
        host = livestatus.get_host(host_name)
    elif isinstance(host_name, dict):
        host = host_name
    else:
        raise KeyError(
            'host_name must be str or dict (got %s)' % type(host_name))
    parent_names = host['parents']
    while len(parent_names) > 0:
        parents = map(lambda x: livestatus.get_host(x), parent_names)

        # generate a list of grandparent names:
        grand_parents = set()
        for i in parents:
            map(lambda x: grand_parents.add(x), i.get('parents'))
        result.append(parents)
        parent_names = list(grand_parents)
    return result


@error_handler
def status_hostgroup(request, hostgroup_name):
    """ Status detail for one specific hostgroup  """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['hostgroup_name'] = hostgroup_name
    c['object_type'] = 'hostgroup'
    livestatus = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)

    my_hostgroup = pynag.Model.Hostgroup.objects.get_by_shortname(
        hostgroup_name)
    c['my_hostgroup'] = livestatus.get_hostgroups(
        'Filter: name = %s' % hostgroup_name)[0]

    _add_statistics_to_hostgroups([c['my_hostgroup']])
    # Get information about child hostgroups
    subgroups = my_hostgroup.hostgroup_members or ''
    subgroups = subgroups.split(',')
    if subgroups == ['']:
        subgroups = []
    c['hostgroups'] = map(
        lambda x: livestatus.get_hostgroups('Filter: name = %s' % x)[0], subgroups)
    _add_statistics_to_hostgroups(c['hostgroups'])

    # Get hosts that belong in this hostgroup
    c['hosts'] = livestatus.query(
        'GET hosts', 'Filter: host_groups >= %s' % hostgroup_name)
    _add_statistics_to_hosts(c['hosts'])
    # Sort by service status
    c['hosts'].sort(cmp=lambda a, b: cmp(a['percent_ok'], b['percent_ok']))

    # Get services that belong in this hostgroup
    c['services'] = livestatus.query(
        'GET services', 'Filter: host_groups >= %s' % hostgroup_name)
    c['services'] = pynag.Utils.grep(c['services'], **request.GET)
    # Get recent log entries for this hostgroup
    l = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config)
    all_history = l.get_state_history()
    c['log'] = filter(lambda x: x['host_name']
                      in c['my_hostgroup']['members'], all_history)

    # Create some state history progress bar from our logs:
    if len(c['log']) > 0:
        log = c['log']
        c['start_time'] = start_time = log[0]['time']
        c['end_time'] = end_time = log[-1]['time']
        now = time.time()

        total_duration = now - start_time
        state_hist = []
        start = start_time
        last_item = None
        css_hint = {}
        css_hint[0] = 'success'
        css_hint[1] = 'warning'
        css_hint[2] = 'danger'
        css_hint[3] = 'info'
        for i in log:
            i['duration_percent'] = 100 * i['duration'] / total_duration
            i['bootstrap_status'] = css_hint[i['state']]

    return render_to_response('status_hostgroup.html', c, context_instance=RequestContext(request))


@error_handler
def _add_statistics_to_hostgroups(hostgroups):
    """ Enriches a list of hostgroup dicts with information about subgroups and parentgroups
    """
    # Lets establish a good list of all hostgroups and parentgroups
    all_hostgroups = pynag.Model.Hostgroup.objects.all
    all_subgroups = set()  # all hostgroups that belong in some other hostgroup
    # "subgroup":['master1','master2']
    hostgroup_parentgroups = defaultdict(set)
    hostgroup_childgroups = pynag.Model.ObjectRelations.hostgroup_hostgroups

    for hostgroup, subgroups in hostgroup_childgroups.items():
        map(lambda x: hostgroup_parentgroups[x].add(hostgroup), subgroups)

    for i in hostgroups:
        i['child_hostgroups'] = hostgroup_childgroups[i['name']]
        i['parent_hostgroups'] = hostgroup_parentgroups[i['name']]

    # Extra statistics for our hostgroups
    for hg in hostgroups:
        ok = hg.get('num_services_ok')
        warn = hg.get('num_services_warn')
        crit = hg.get('num_services_crit')
        pending = hg.get('num_services_pending')
        unknown = hg.get('num_services_unknown')
        total = ok + warn + crit + pending + unknown
        hg['total'] = total
        hg['problems'] = warn + crit + unknown
        try:
            total = float(total)
            hg['health'] = float(ok) / total * 100.0
            hg['health'] = float(ok) / total * 100.0
            hg['percent_ok'] = ok / total * 100
            hg['percent_warn'] = warn / total * 100
            hg['percent_crit'] = crit / total * 100
            hg['percent_unknown'] = unknown / total * 100
            hg['percent_pending'] = pending / total * 100
        except ZeroDivisionError:
            pass


@error_handler
def status_servicegroups(request):
    c = {}
    c['messages'] = []
    c['errors'] = []
    servicegroup_name = None
    livestatus = utils.livestatus(request)
    servicegroups = livestatus.get_servicegroups()
    c['servicegroup_name'] = servicegroup_name
    c['request'] = request
    c['servicegroups'] = servicegroups
    return render_to_response('status_servicegroups.html', c, context_instance=RequestContext(request))


@error_handler
def status_hostgroups(request):
    c = {}
    c['messages'] = []
    c['errors'] = []
    hostgroup_name = None
    livestatus = utils.livestatus(request)
    hostgroups = livestatus.get_hostgroups()
    c['hostgroup_name'] = hostgroup_name
    c['request'] = request

    # Lets establish a good list of all hostgroups and parentgroups
    all_hostgroups = pynag.Model.Hostgroup.objects.all
    all_subgroups = set()  # all hostgroups that belong in some other hostgroup
    # "subgroup":['master1','master2']
    hostgroup_parentgroups = defaultdict(set)
    hostgroup_childgroups = pynag.Model.ObjectRelations.hostgroup_hostgroups

    for hostgroup, subgroups in hostgroup_childgroups.items():
        map(lambda x: hostgroup_parentgroups[x].add(hostgroup), subgroups)

    for i in hostgroups:
        i['child_hostgroups'] = hostgroup_childgroups[i['name']]
        i['parent_hostgroups'] = hostgroup_parentgroups[i['name']]

    if hostgroup_name is None:
        # If no hostgroup was specified. Lets only show "root hostgroups"
        c['hosts'] = livestatus.get_hosts()
        my_hostgroups = []
        for i in hostgroups:
            if len(i['parent_hostgroups']) == 0:
                my_hostgroups.append(i)
        my_hostgroups.sort()
        c['hostgroups'] = my_hostgroups

    else:
        my_hostgroup = pynag.Model.Hostgroup.objects.get_by_shortname(
            hostgroup_name)
        subgroups = my_hostgroup.hostgroup_members or ''
        subgroups = subgroups.split(',')
        # Strip out any group that is not a subgroup of hostgroup_name
        right_hostgroups = []
        for group in hostgroups:
            if group.get('name', '') in subgroups:
                right_hostgroups.append(group)
        c['hostgroups'] = right_hostgroups

        # If a hostgroup was specified lets also get all the hosts for it
        c['hosts'] = livestatus.query(
            'GET hosts', 'Filter: host_groups >= %s' % hostgroup_name)
    for host in c['hosts']:
        ok = host.get('num_services_ok')
        warn = host.get('num_services_warn')
        crit = host.get('num_services_crit')
        pending = host.get('num_services_pending')
        unknown = host.get('num_services_unknown')
        total = ok + warn + crit + pending + unknown
        host['total'] = total
        host['problems'] = warn + crit + unknown
        try:
            total = float(total)
            host['health'] = float(ok) / total * 100.0
            host['percent_ok'] = ok / total * 100
            host['percent_warn'] = warn / total * 100
            host['percent_crit'] = crit / total * 100
            host['percent_unknown'] = unknown / total * 100
            host['percent_pending'] = pending / total * 100
        except ZeroDivisionError:
            host['health'] = 'n/a'
    # Extra statistics for our hostgroups
    for hg in c['hostgroups']:
        ok = hg.get('num_services_ok')
        warn = hg.get('num_services_warn')
        crit = hg.get('num_services_crit')
        pending = hg.get('num_services_pending')
        unknown = hg.get('num_services_unknown')
        total = ok + warn + crit + pending + unknown
        hg['total'] = total
        hg['problems'] = warn + crit + unknown
        try:
            total = float(total)
            hg['health'] = float(ok) / total * 100.0
            hg['health'] = float(ok) / total * 100.0
            hg['percent_ok'] = ok / total * 100
            hg['percent_warn'] = warn / total * 100
            hg['percent_crit'] = crit / total * 100
            hg['percent_unknown'] = unknown / total * 100
            hg['percent_pending'] = pending / total * 100
        except ZeroDivisionError:
            pass
    return render_to_response('status_hostgroups.html', c, context_instance=RequestContext(request))


@error_handler
def status_tiles(request, object_type="host"):
    """
    """
    c = _status(request)
    return render_to_response('status_tiles.html', c, context_instance=RequestContext(request))


@error_handler
def status_host(request):
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['hosts'] = utils.get_hosts(request, **request.GET)
    c['host_name'] = request.GET.get('detail', None)
    return render_to_response('status_host.html', c, context_instance=RequestContext(request))


@error_handler
def status_boxview(request):
    c = _status(request)

    return render_to_response('status_boxview.html', c, context_instance=RequestContext(request))


def get_related_objects(object_id):
    my_object = pynag.Model.ObjectDefinition.objects.get_by_id(object_id)
    result = []
    if my_object.register == '0':
        result += my_object.get_effective_children()
        return result
    if my_object.object_type == 'hostgroup':
        result += my_object.get_effective_hostgroups()
        result += my_object.get_effective_hosts()
    if my_object.object_type == 'contactgroup':
        result += my_object.get_effective_contactgroups()
        result += my_object.get_effective_contacts()
    if my_object.object_type == 'host':
        result += my_object.get_effective_network_children()
        result += my_object.get_effective_services()
    return result


@error_handler
def status_paneview(request):
    #c = _status(request)
    c = {}
    c['messages'] = []
    c['errors'] = []
    import pynag.Model
    c['pane1_id'] = pane1 = request.GET.get('pane1')
    c['pane2_id'] = pane2 = request.GET.get('pane2')
    c['pane3_id'] = pane3 = request.GET.get('pane3')
    c['view'] = view = request.GET.get('view', 'hostgroups')

    pane1_object = None
    pane2_object = None
    pane3_object = None
    pane1_objects = []
    pane2_objects = []
    pane3_objects = []

    if pane1 is None or pane1 == 'None':
        pane1 = None
        if view == 'servicetemplates':
            pane1_objects = pynag.Model.Service.objects.filter(register=0)
        elif view == 'hostgroups':
            pane1_objects = pynag.Model.Hostgroup.objects.all
        elif view == 'contactgroups':
            pane1_objects = pynag.Model.Contactgroup.objects.all
        elif view == 'hosttemplates':
            pane1_objects = pynag.Model.Host.objects.filter(register=0)
        elif view == 'hosts':
            pane1_objects = pynag.Model.Host.objects.filter(register=1)
        elif view == 'networkparents':
            hosts = pynag.Model.Host.objects.filter(register=1)
            parents = []
            for i in hosts:
                if len(i.get_effective_network_children()) > 0:
                    parents.append(i)
            pane1_objects = parents
    if pane1 is not None:
        pane1_object = pynag.Model.ObjectDefinition.objects.get_by_id(pane1)
        pane1_objects = get_related_objects(pane1)
    if pane2 is not None:
        pane2_object = pynag.Model.ObjectDefinition.objects.get_by_id(pane2)
        pane2_objects = get_related_objects(pane2)
    if pane3 is not None:
        pane3_object = pynag.Model.ObjectDefinition.objects.get_by_id(pane3)
        pane3_objects = get_related_objects(pane3)

    livestatus = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    hosts = livestatus.get_hosts()
    services = livestatus.get_services()

    for i in pane1_objects + pane2_objects + pane3_objects:
        if i.object_type == 'host':
            i['tag'] = 'H'
            for x in hosts:
                if x['name'] == i.host_name:
                    i['state'] = x.get('state', None)
        elif i.object_type == 'service':
            i['tag'] = 'S'
            for x in services:
                if x['description'] == i.service_description and x['host_name'] == i.host_name:
                    i['state'] = x.get('state', None)
        elif i.object_type == 'contact':
            i['tag'] = 'C'
        elif i.object_type == 'contactgroup':
            i['tag'] = 'CG'
        elif i.object_type == 'hostgroup':
            i['tag'] = 'HG'
        elif i.object_type == 'servicegroup':
            i['tag'] = 'SG'
    c['request'] = request
    c['pane1_objects'] = pane1_objects
    c['pane2_objects'] = pane2_objects
    c['pane3_objects'] = pane3_objects
    c['pane1_object'] = pane1_object
    c['pane2_object'] = pane2_object
    c['pane3_object'] = pane3_object

    return render_to_response('status_paneview.html', c, context_instance=RequestContext(request))


def _add_statistics_to_hosts(hosts):
    """ Takes a list of dict hosts, and adds to the list statistics
     Following is an example of attributes added to the dicts:
     num_services_ok
     num_services_warn
     problems (number of problems)
     health (percent of services ok)
     percent_problems
    """
    for host in hosts:
        ok = host.get('num_services_ok')
        warn = host.get('num_services_warn')
        crit = host.get('num_services_crit')
        pending = host.get('num_services_pending')
        unknown = host.get('num_services_unknown')
        total = ok + warn + crit + pending + unknown
        host['total'] = total
        host['problems'] = warn + crit + unknown
        host['num_problems'] = warn + crit + unknown
        try:
            total = float(total)
            host['health'] = float(ok) / total * 100.0
            host['percent_ok'] = ok / total * 100
            host['percent_warn'] = warn / total * 100
            host['percent_crit'] = crit / total * 100
            host['percent_unknown'] = unknown / total * 100
            host['percent_pending'] = pending / total * 100
        except ZeroDivisionError:
            host['health'] = 'n/a'
            host['percent_ok'] = 0
            host['percent_warn'] = 0
            host['percent_crit'] = 0
            host['percent_unknown'] = 0
            host['percent_pending'] = 0


@error_handler
def status_index(request):
    c = adagios.status.utils.get_statistics(request)
    c['services'] = adagios.status.utils.get_services(request, 'unhandled')
    #c['top_alert_producers'] = adagios.status.rest.top_alert_producers(limit=5)

    return render_to_response('status_index.html', c, context_instance=RequestContext(request))


@error_handler
def test_livestatus(request):
    """ This view is a test on top of mk_livestatus which allows you to enter your own queries """
    c = {}
    c['messages'] = []
    c['table'] = table = request.GET.get('table')

    livestatus = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    if table is not None:
        columns = livestatus.query('GET columns', 'Filter: table = %s' % table)
        c['columns'] = columns

        columns = ""
        limit = request.GET.get('limit')
        run_query = False
        for k, v in request.GET.items():
            if k == "submit":
                run_query = True
            if k.startswith('check_'):
                columns += " " + k[len("check_"):]
        # Any columns checked means we return a query
        query = ['GET %s' % table]
        if len(columns) > 0:
            query.append("Columns: %s" % columns)
        if limit != '' and limit > 0:
            query.append("Limit: %s" % limit)
        if run_query is True:
            c['results'] = livestatus.query(*query)
            c['query'] = livestatus.last_query
            c['header'] = c['results'][0].keys()

    return render_to_response('test_livestatus.html', c, context_instance=RequestContext(request))


def _status_combined(request, optimized=False):
    """ Returns a combined status of network outages, host problems and service problems

    If optimized is True, fewer attributes are loaded it, makes it run faster but with less data
    """
    c = {}
    livestatus = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    if optimized == True:
        hosts = livestatus.get_hosts(
            'Columns: name state acknowledged downtimes childs parents')
        services = livestatus.get_services(
            'Columns: host_name description state acknowledged downtimes host_state')
    else:
        hosts = livestatus.get_hosts()
        services = livestatus.get_services()
    hosts_that_are_down = []
    hostnames_that_are_down = []
    service_status = [0, 0, 0, 0]
    host_status = [0, 0, 0, 0]
    parents = []
    for host in hosts:
        host_status[host["state"]] += 1
        if len(host['childs']) > 0:
            parents.append(host)
        if host['state'] != 0 and host['acknowledged'] == 0 and host['downtimes'] == []:
            hostnames_that_are_down.append(host['name'])
            hosts_that_are_down.append(host)

    network_problems = []
    host_problems = []
    service_problems = []

    # Do nothing if host parent is also down.
    for host in hosts_that_are_down:
        for i in host['parents']:
            if i in hostnames_that_are_down:
                break
        else:
            if len(host['childs']) == 0:
                host_problems.append(host)
            else:
                network_problems.append(host)
    for service in services:
        service_status[service["state"]] += 1
        if service['state'] != 0 and service['acknowledged'] == 0 and len(service['downtimes']) == 0 and service['host_state'] == 0:
            service_problems.append(service)
    c['network_problems'] = network_problems
    c['host_problems'] = host_problems
    c['service_problems'] = service_problems
    c['hosts'] = hosts
    c['services'] = services
    c['parents'] = parents
    service_totals = float(sum(service_status))
    host_totals = float(sum(host_status))
    if service_totals == 0:
        c['service_status'] = 0
    else:
        c['service_status'] = map(
            lambda x: 100 * x / service_totals, service_status)
    if host_totals == 0:
        c['host_status'] = 0
    else:
        c['host_status'] = map(lambda x: 100 * x / host_totals, host_status)
    #l = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config)
    #c['log'] = reversed(l.get_state_history())
    return c


@error_handler
def status_problems(request):
    return dashboard(request)


@error_handler
def dashboard(request):

    # Get statistics
    c = adagios.status.utils.get_statistics(request)

    c['messages'] = []
    c['errors'] = []

    all_down_hosts = utils.get_hosts(request, state__isnot='0', **request.GET)
    hostnames_that_are_down = map(lambda x: x.get('name'), all_down_hosts)
    # Discover network outages,

    # Remove acknowledgements and also all hosts where all parent hosts are
    # down
    c['host_problems'] = []  # Unhandled host problems
    c['network_problems'] = []  # Network outages
    for i in all_down_hosts:
        if i.get('acknowledged') != 0:
            continue
        if i.get('scheduled_downtime_depth') != 0:
            continue

        # Do nothing if parent of this host is also down
        for parent in i.get('parents'):
            if parent in hostnames_that_are_down:
                parent_is_down = True
                break
        else:
            parent_is_down = False

        if parent_is_down == True:
            continue

        # If host has network childs, put them in the network outages box
        if i.get('childs') == []:
            c['host_problems'].append(i)
        else:
            c['network_problems'].append(i)
    #
    c['hosts'] = c['network_problems'] + c['host_problems']
    # Service problems
    c['service_problems'] = utils.get_services(request,
                                               state__isnot="0",
                                               acknowledged="0",
                                               scheduled_downtime_depth="0",
                                               host_state="0",
                                               **request.GET
                                               )
    # Sort problems by state and last_check as secondary sort field
    c['service_problems'].sort(
        reverse=True, cmp=lambda a, b: cmp(a['last_check'], b['last_check']))
    c['service_problems'].sort(
        reverse=True, cmp=lambda a, b: cmp(a['state'], b['state']))
    return render_to_response('status_dashboard.html', c, context_instance=RequestContext(request))


@error_handler
def state_history(request):
    c = {}
    c['messages'] = []
    c['errors'] = []

    livestatus = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    start_time = request.GET.get('start_time', None)
    end_time = request.GET.get('end_time', None)
    if end_time is None:
        end_time = time.time()
    end_time = int(end_time)
    if start_time is None:
        seconds_in_a_day = 60 * 60 * 24
        seconds_today = end_time % seconds_in_a_day  # midnight of today
        start_time = end_time - seconds_today
    start_time = int(start_time)
    l = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config)
    c['log'] = log = l.get_state_history()
    total_duration = end_time - start_time
    c['total_duration'] = total_duration
    css_hint = {}
    css_hint[0] = 'success'
    css_hint[1] = 'warning'
    css_hint[2] = 'danger'
    css_hint[3] = 'info'
    last_item = None

    services = {}
    for i in log:
        short_name = "%s/%s" % (i['host_name'], i['service_description'])
        for k, v in request.GET.items():
            if k in i.keys() and i[k] != v:
                break
        else:
            if short_name not in services:
                s = {}
                s['host_name'] = i['host_name']
                s['service_description'] = i['service_description']
                s['log'] = []
                s['worst_logfile_state'] = 0
                #s['log'] = [{'time':start_time,'state':3, 'plugin_output':'Unknown value here'}]
                services[short_name] = s

            services[short_name]['log'].append(i)
            services[short_name]['worst_logfile_state'] = max(
                services[short_name]['worst_logfile_state'], i['state'])
    for service in services.values():
        last_item = None
        service['sla'] = float(0)
        service['num_problems'] = 0
        service['duration'] = 0
        for i in service['log']:
            i['bootstrap_status'] = css_hint[i['state']]
            if i['time'] < start_time:
                i['time'] = start_time
            if last_item is not None:
                last_item['end_time'] = i['time']
                #last_item['time'] = max(last_item['time'], start_time)
                last_item['duration'] = duration = last_item[
                    'end_time'] - last_item['time']
                last_item['duration_percent'] = 100 * float(
                    duration) / total_duration
                service['duration'] += last_item['duration_percent']
                if last_item['state'] == 0:
                    service['sla'] += last_item['duration_percent']
                else:
                    service['num_problems'] += 1
            last_item = i
        if not last_item is None:
            last_item['end_time'] = end_time
            last_item['duration'] = duration = last_item[
                'end_time'] - last_item['time']
            last_item['duration_percent'] = 100 * duration / total_duration
            service['duration'] += last_item['duration_percent']
            if last_item['state'] == 0:
                service['sla'] += last_item['duration_percent']
            else:
                service['num_problems'] += 1

    c['services'] = services
    c['start_time'] = start_time
    c['end_time'] = end_time
    return render_to_response('state_history.html', c, context_instance=RequestContext(request))


def _status_log(request):
    """ Helper function to any status view that requires log access """
    c = {}
    c['messages'] = []
    c['errors'] = []
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    host_name = request.GET.get('host_name', '')
    service_description = request.GET.get('service_description', '')
    limit = request.GET.get('limit', '')

    if end_time == '':
        end_time = None
    else:
        end_time = float(end_time)

    if start_time == '':
        now = time.time()
        seconds_in_a_day = 60 * 60 * 24
        seconds_today = now % seconds_in_a_day  # midnight of today
        start_time = now - seconds_today
    else:
        start_time = float(start_time)

    if limit == '':
        limit = 2000
    else:
        limit = int(limit)

    # Any querystring parameters we will treat as a search string to get_log_entries, but we need to massage them
    # a little bit first
    kwargs = {}
    for k, v in request.GET.items():
        if k == 'search':
            k = 'search'
        elif k in (
            'start_time', 'end_time', 'start_time_picker', 'end_time_picker', 'limit',
            'start_hours', 'end_hours'):
            continue
        elif v is None or len(v) == 0:
            continue
        k = str(k)
        v = str(v)
        kwargs[k] = v
    l = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config)
    c['log'] = l.get_log_entries(
        start_time=start_time, end_time=end_time, **kwargs)[-limit:]
    c['log'].reverse()
    c['logs'] = {'all': []}
    for line in c['log']:
        if line['class_name'] not in c['logs'].keys():
            c['logs'][line['class_name']] = []
        c['logs'][line['class_name']].append(line)
        c['logs']['all'].append(line)
    c['start_time'] = start_time
    c['end_time'] = end_time
    return c


@error_handler
def status_log(request):
    c = _status_log(request)
    c['request'] = request
    c['log'].reverse()
    return render_to_response('status_log.html', c, context_instance=RequestContext(request))


@error_handler
def comment_list(request):
    """ Display a list of all comments """
    c = {}
    c['messages'] = []
    c['errors'] = []
    l = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    comments = l.query('GET comments')
    downtimes = l.query('GET downtimes')
    args = request.GET.copy()
    c['comments'] = grep_dict(comments, **args)
    c['acknowledgements'] = grep_dict(comments, entry_type=4)
    c['downtimes'] = grep_dict(downtimes, **args)
    return render_to_response('status_comments.html', c, context_instance=RequestContext(request))


@error_handler
def downtime_list(request):
    """ Display a list of all comments """
    c = {}
    c['messages'] = []
    c['errors'] = []
    l = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    comments = l.query('GET comments')
    downtimes = l.query('GET downtimes')
    args = request.GET.copy()
    c['comments'] = grep_dict(comments, **args)
    c['acknowledgements'] = grep_dict(comments, entry_type=4)
    c['downtimes'] = grep_dict(downtimes, **args)
    return render_to_response('status_downtimes.html', c, context_instance=RequestContext(request))


def grep_dict(array, **kwargs):
    """  Returns all the elements from array that match the keywords in **kwargs

    TODO: Refactor pynag.Model.ObjectDefinition.objects.filter() and reuse it here.
    Arguments:
        array -- a list of dict that is to be searched
        kwargs -- Any search argument provided will be checked against every dict
    Examples:
    array = [
    {'host_name': 'examplehost', 'state':0},
    {'host_name': 'example2', 'state':1},
    ]
    grep_dict(array, state=0)
    # should return [{'host_name': 'examplehost', 'state':0},]

    """
    result = []
    for current_item in array:
        # Iterate through every keyword provided:
        for k, v in kwargs.items():
            if type(v) == type([]):
                v = v[0]
            if str(v) != str(current_item.get(k, None)):
                break
        else:
            # If we get here, none of the search arguments are invalid
            result.append(current_item)
    return result


@error_handler
def perfdata(request):
    """ Display a list of perfdata
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    fields = "host_name description perf_data state host_state scheduled_downtime_depth host_scheduled_downtime_depth host_acknowledged acknowledged downtimes host_downtimes".split()
    perfdata = utils.get_services(None, fields=fields, **request.GET)
    for i in perfdata:
        metrics = pynag.Utils.PerfData(i['perf_data']).metrics
        metrics = filter(lambda x: x.is_valid(), metrics)
        i['metrics'] = metrics

    c['perfdata'] = perfdata
    return render_to_response('status_perfdata.html', c, context_instance=RequestContext(request))


@error_handler
def contact_list(request):
    """ Display a list of active contacts
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    l = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    c['contacts'] = l.query('GET contacts')
    c['contacts'] = pynag.Utils.grep(c['contacts'], **request.GET)
    c['contactgroups'] = l.query('GET contactgroups')
    return render_to_response('status_contacts.html', c, context_instance=RequestContext(request))


@error_handler
def contact_detail(request, contact_name):
    """ Detailed information for one specific contact
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['contact_name'] = contact_name
    l = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)

    # Fetch contact and basic information
    result = l.query("GET contacts", "Filter: name = %s" % contact_name)
    if result == []:
        c['errors'].append("Contact named '%s' was not found." % contact_name)
        if contact_name != 'anonymous':
            return render_to_response('status_error.html', c, context_instance=RequestContext(request))
    else:
        contact = result[0]
        c['contact'] = contact

    # Active comments
    c['comments'] = l.query(
        'GET comments', 'Filter: comment ~ %s' % contact_name,)
    for i in c['comments']:
        if i.get('type') == 1:
            i['state'] = i['host_state']
        else:
            i['state'] = i['service_state']

    # Services this contact can see
    c['services'] = l.query(
        'GET services', "Filter: contacts >= %s" % contact_name)

    # Activity log
    c['log'] = pynag.Parsers.LogFiles(
        maincfg=adagios.settings.nagios_config).get_log_entries(search=str(contact_name))

    # Contact groups
    c['groups'] = l.query(
        'GET contactgroups', 'Filter: members >= %s' % contact_name)

    # Git audit logs
    nagiosdir = dirname(adagios.settings.nagios_config)
    git = pynag.Utils.GitRepo(directory=nagiosdir)
    c['gitlog'] = git.log(author_name=contact_name)
    return render_to_response('status_contact.html', c, context_instance=RequestContext(request))


@error_handler
def contactgroup_detail(request, contactgroup_name):
    """ Detailed information for one specific contactgroup
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['contactgroup_name'] = contactgroup_name
    l = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)

    # Fetch contact and basic information
    result = l.query("GET contactgroups", "Filter: name = %s" %
                     contactgroup_name)
    if result == []:
        c['errors'].append(
            "Contactgroup named '%s' was not found." % contactgroup_name)
    else:
        contactgroup = result[0]
        c['contactgroup'] = contactgroup

    # Services this contact can see
    c['services'] = l.query(
        'GET services', "Filter: contact_groups >= %s" % contactgroup_name)

    # Services this contact can see
    c['hosts'] = l.query(
        'GET hosts', "Filter: contact_groups >= %s" % contactgroup_name)

    # Contact groups
    #c['contacts'] = l.query('GET contacts', 'Filter: contactgroup_ >= %s' % contact_name)

    return render_to_response('status_contactgroup.html', c, context_instance=RequestContext(request))


@error_handler
def perfdata2(request):
    """ Just a test method, feel free to remove it
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    columns = 'Columns: host_name description perf_data state host_state'
    l = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)

    # User can specify from querystring a filter of which services to fetch
    # we convert querystring into livestatus filters.
    # User can also specify specific metrics to watch, so we extract from
    # querystring as well
    querystring = request.GET.copy()
    interesting_metrics = querystring.pop('metrics', [''])[0]
    arguments = pynag.Utils.grep_to_livestatus(**querystring)
    services = l.query('GET services', columns, *arguments)
    # If no metrics= was specified on querystring, we take the string
    # from first service in our search result
    if not interesting_metrics and services:
        perfdata = pynag.Utils.PerfData(services[0]['perf_data'])
        interesting_metrics = map(lambda x: x.label, perfdata.metrics)
    else:
        interesting_metrics = interesting_metrics.split(',')

    # Iterate through all the services and parse perfdata
    for service in services:
        perfdata = pynag.Utils.PerfData(service['perf_data'])
        null_metric = pynag.Utils.PerfDataMetric()
        metrics = map(lambda x: perfdata.get_perfdatametric(
            x) or null_metric, interesting_metrics)
        #metrics = filter(lambda x: x.is_valid(), metrics)
        service['metrics'] = metrics

    c['metrics'] = interesting_metrics
    c['services'] = services

    return render_to_response('status_perfdata2.html', c, context_instance=RequestContext(request))
