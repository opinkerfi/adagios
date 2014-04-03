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
from django.utils.translation import ugettext as _

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

from adagios.views import adagios_decorator, error_page


@adagios_decorator
def detail(request):
    """ Return status detail view for a single given host, hostgroup,service, contact, etc """
    host_name = request.GET.get('host_name')
    service_description = request.GET.get('service_description')
    contact_name = request.GET.get('contact_name')
    hostgroup_name = request.GET.get('hostgroup_name')
    contactgroup_name = request.GET.get('contactgroup_name')
    servicegroup_name = request.GET.get('servicegroup_name')
    if service_description:
        return service_detail(request, host_name=host_name, service_description=service_description)
    elif host_name:
        return host_detail(request, host_name=host_name)
    elif contact_name:
        return contact_detail(request, contact_name=contact_name)
    elif contactgroup_name:
        return contactgroup_detail(request, contactgroup_name=contactgroup_name)
    elif hostgroup_name:
        return hostgroup_detail(request, hostgroup_name=hostgroup_name)
    elif servicegroup_name:
        return servicegroup_detail(request, servicegroup_name=servicegroup_name)

    raise Exception("You have to provide an item via querystring so we know what to give you details for")


@adagios_decorator
def status_parents(request):
    """ Here for backwards compatibility """
    return network_parents(request)


@adagios_decorator
def network_parents(request):
    """ List of hosts that are network parents """
    c = {}
    c['messages'] = []
    authuser = request.GET.get('contact_name', None)
    livestatus = utils.livestatus(request)
    fields = "name childs state scheduled_downtime_depth address last_check last_state_change acknowledged downtimes services services_with_info".split()
    hosts = utils.get_hosts(request, 'Filter: childs !=', fields=fields, **request.GET)
    host_dict = {}
    map(lambda x: host_dict.__setitem__(x['name'], x), hosts)
    c['hosts'] = []

    for i in hosts:
        if i['childs']:

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


@adagios_decorator
def status(request):
    """ Compatibility layer around status.views.services
    """
    # return render_to_response('status.html', c, context_instance=RequestContext(request))
    # Left here for compatibility reasons:
    return services(request)


@adagios_decorator
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

@adagios_decorator
def services_js(request):
    """ This view handles list of services  """
    c = {}
    c['messages'] = []
    c['errors'] = []
    fields = [
        'host_name', 'description', 'plugin_output', 'last_check', 'host_state', 'state',
        'last_state_change', 'acknowledged', 'downtimes', 'host_downtimes', 'comments_with_info']
    c['services'] = json.dumps(utils.get_services(request, fields=fields, **request.GET))
    return render_to_response('status_services_js.html', c, context_instance=RequestContext(request))


@adagios_decorator
def status_dt(request):
    """ This view handles list of services  """
    c = {}
    return render_to_response('status_dt.html', c, context_instance=RequestContext(request))


@adagios_decorator
def snippets_services(request):
    """ Returns a html stub with only the services view """
    c = {}
    c['messages'] = []
    c['errors'] = []
    fields = [
        'host_name', 'description', 'plugin_output', 'last_check', 'host_state', 'state',
        'last_state_change', 'acknowledged', 'downtimes', 'host_downtimes', 'comments_with_info']
    c['services'] = utils.get_services(request, fields=fields, **request.GET)
    return render_to_response('snippets/status_servicelist_snippet.html', c, context_instance=RequestContext(request))

@adagios_decorator
def snippets_hosts(request):
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['hosts'] = utils.get_hosts(request, **request.GET)
    c['host_name'] = request.GET.get('detail', None)
    return render_to_response('snippets/status_hostlist_snippet.html', c, context_instance=RequestContext(request))


@adagios_decorator
def snippets_log(request):
    """ Returns a html stub with the  snippet_statehistory_snippet.html
    """
    host_name = request.GET.get('host_name')
    service_description = request.GET.get('service_description')
    hostgroup_name = request.GET.get('hostgroup_name')

    if service_description == "_HOST_":
        service_description = None

    l = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config)
    log = l.get_state_history(host_name=host_name, service_description=service_description)

    # If hostgroup_name was specified, lets get all log entries that belong to that hostgroup
    if host_name and service_description:
        object_type = 'service'
    elif hostgroup_name:
        object_type = "hostgroup"
        hg = pynag.Model.Hostgroup.objects.get_by_shortname(hostgroup_name)
        hosts = hg.get_effective_hosts()
        hostnames = map(lambda x: x.host_name, hosts)
        log = filter(lambda x: x['host_name'] in hostnames, log)
    elif host_name:
        object_type = "host"
    else:
        raise Exception("Need either a host_name or hostgroup_name parameter")

    c = {'log':log}
    c['object_type'] = object_type
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


@adagios_decorator
def host_detail(request, host_name):
    """ Return status detail view for a single host """
    return service_detail(request, host_name=host_name, service_description=None)


@adagios_decorator
def service_detail(request, host_name, service_description):
    """ Displays status details for one host or service """
    c = {}
    c['messages'] = []
    c['errors'] = []

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
        c['network_parents'] = reversed(_get_network_parents(request, host_name))
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


def _get_network_parents(request, host_name):
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
    livestatus = adagios.status.utils.livestatus(request)
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


@adagios_decorator
def hostgroup_detail(request, hostgroup_name):
    """ Status detail for one specific hostgroup  """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['hostgroup_name'] = hostgroup_name
    c['object_type'] = 'hostgroup'
    livestatus = adagios.status.utils.livestatus(request)

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
    c['hostgroups'] = map(lambda x: livestatus.get_hostgroups('Filter: name = %s' % x)[0], subgroups)
    _add_statistics_to_hostgroups(c['hostgroups'])

    return render_to_response('status_hostgroup.html', c, context_instance=RequestContext(request))


@adagios_decorator
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


@adagios_decorator
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


@adagios_decorator
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


@adagios_decorator
def status_host(request):
    """ Here for backwards compatibility """
    return hosts(request)


@adagios_decorator
def hosts(request):
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['hosts'] = utils.get_hosts(request, **request.GET)
    c['host_name'] = request.GET.get('detail', None)
    return render_to_response('status_host.html', c, context_instance=RequestContext(request))


@adagios_decorator
def problems(request):
    c = {}
    c['messages'] = []
    c['errors'] = []
    search_filter = request.GET.copy()
    if 'state__isnot' not in search_filter and 'state' not in search_filter:
        search_filter['state__isnot'] = '0'
    c['hosts'] = utils.get_hosts(request, **search_filter)
    c['services'] = utils.get_services(request, **search_filter)
    return render_to_response('status_problems.html', c, context_instance=RequestContext(request))



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


@adagios_decorator
def status_index(request):
    c = adagios.status.utils.get_statistics(request)
    c['services'] = adagios.status.utils.get_services(request, 'unhandled')
    #c['top_alert_producers'] = adagios.status.rest.top_alert_producers(limit=5)

    return render_to_response('status_index.html', c, context_instance=RequestContext(request))


@adagios_decorator
def test_livestatus(request):
    """ This view is a test on top of mk_livestatus which allows you to enter your own queries """
    c = {}
    c['messages'] = []
    c['table'] = table = request.GET.get('table')

    livestatus = adagios.status.utils.livestatus(request)
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
    livestatus = adagios.status.utils.livestatus(request)
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


@adagios_decorator
def status_problems(request):
    return dashboard(request)


@adagios_decorator
def dashboard(request):

    # Get statistics
    c = adagios.status.utils.get_statistics(request)

    c['messages'] = []
    c['errors'] = []

    c['host_problems'] = utils.get_hosts(request, state='1', unhandled='', **request.GET)

    # Service problems
    c['service_problems'] = utils.get_services(request, host_state="0", unhandled='', **request.GET)

    # Sort problems by state and last_check as secondary sort field
    c['service_problems'].sort(
        reverse=True, cmp=lambda a, b: cmp(a['last_check'], b['last_check']))
    c['service_problems'].sort(
        reverse=True, cmp=lambda a, b: cmp(a['state'], b['state']))
    return render_to_response('status_dashboard.html', c, context_instance=RequestContext(request))


@adagios_decorator
def state_history(request):
    c = {}
    c['messages'] = []
    c['errors'] = []

    livestatus = adagios.status.utils.livestatus(request)
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


@adagios_decorator
def status_log(request):
    c = _status_log(request)
    c['request'] = request
    c['log'].reverse()
    return render_to_response('status_log.html', c, context_instance=RequestContext(request))


@adagios_decorator
def comment_list(request):
    """ Display a list of all comments """
    c = {}
    c['messages'] = []
    c['errors'] = []
    l = adagios.status.utils.livestatus(request)
    args = pynag.Utils.grep_to_livestatus(**request.GET)
    c['comments'] = l.query('GET comments', *args)
    return render_to_response('status_comments.html', c, context_instance=RequestContext(request))


@adagios_decorator
def downtime_list(request):
    """ Display a list of all comments """
    c = {}
    c['messages'] = []
    c['errors'] = []
    l = adagios.status.utils.livestatus(request)
    args = pynag.Utils.grep_to_livestatus(**request.GET)
    c['downtimes'] = l.query('GET downtimes', *args)
    return render_to_response('status_downtimes.html', c, context_instance=RequestContext(request))

@adagios_decorator
def acknowledgement_list(request):
    """ Display a list of all comments """
    c = {}
    c['messages'] = []
    c['errors'] = []
    l = adagios.status.utils.livestatus(request)
    args = pynag.Utils.grep_to_livestatus(**request.GET)
    c['acknowledgements'] = l.query('GET comments', 'Filter: entry_type = 4', *args)
    return render_to_response('status_acknowledgements.html', c, context_instance=RequestContext(request))


@adagios_decorator
def perfdata(request):
    """ Display a list of perfdata
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    fields = "host_name description perf_data state host_state scheduled_downtime_depth host_scheduled_downtime_depth host_acknowledged acknowledged downtimes host_downtimes".split()
    perfdata = utils.get_services(request, fields=fields, **request.GET)
    for i in perfdata:
        metrics = pynag.Utils.PerfData(i['perf_data']).metrics
        metrics = filter(lambda x: x.is_valid(), metrics)
        i['metrics'] = metrics

    c['perfdata'] = perfdata
    return render_to_response('status_perfdata.html', c, context_instance=RequestContext(request))


@adagios_decorator
def contact_list(request):
    """ Display a list of active contacts
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    l = adagios.status.utils.livestatus(request)
    c['contacts'] = l.query('GET contacts')
    c['contacts'] = pynag.Utils.grep(c['contacts'], **request.GET)
    c['contactgroups'] = l.query('GET contactgroups')
    return render_to_response('status_contacts.html', c, context_instance=RequestContext(request))


@adagios_decorator
def contact_detail(request, contact_name):
    """ Detailed information for one specific contact
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['contact_name'] = contact_name
    l = adagios.status.utils.livestatus(request)

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
    nagiosdir = dirname(adagios.settings.nagios_config or pynag.Model.config.guess_cfg_file())
    git = pynag.Utils.GitRepo(directory=nagiosdir)
    c['gitlog'] = git.log(author_name=contact_name)
    return render_to_response('status_contact.html', c, context_instance=RequestContext(request))


@adagios_decorator
def map_view(request):
    c = {}
    livestatus = adagios.status.utils.livestatus(request)
    c['hosts'] = livestatus.get_hosts()
    c['map_center'] = adagios.settings.map_center
    c['map_zoom'] = adagios.settings.map_zoom

    return render_to_response('status_map.html', c, context_instance=RequestContext(request))


@adagios_decorator
def servicegroup_detail(request, servicegroup_name):
    """ Detailed information for one specific servicegroup """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['servicegroup_name'] = servicegroup_name

    c['services'] = adagios.status.utils.get_services(request, groups__has_field=servicegroup_name)
    return render_to_response('status_services.html', c, context_instance=RequestContext(request))

@adagios_decorator
def contactgroups(request):
    """ Display a list of active contacts
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    l = adagios.status.utils.livestatus(request)
    c['contactgroups'] = l.get_contactgroups(**request.GET)
    return render_to_response('status_contactgroups.html', c, context_instance=RequestContext(request))


@adagios_decorator
def contactgroup_detail(request, contactgroup_name):
    """ Detailed information for one specific contactgroup
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c['contactgroup_name'] = contactgroup_name
    l = adagios.status.utils.livestatus(request)

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



@adagios_decorator
def perfdata2(request):
    """ Just a test method, feel free to remove it
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    columns = 'Columns: host_name description perf_data state host_state'
    l = adagios.status.utils.livestatus(request)

    # User can specify from querystring a filter of which services to fetch
    # we convert querystring into livestatus filters.
    # User can also specify specific metrics to watch, so we extract from
    # querystring as well
    querystring = request.GET.copy()
    interesting_metrics = querystring.pop('metrics', [''])[0].strip(',')
    arguments = pynag.Utils.grep_to_livestatus(**querystring)
    if not arguments:
        services = []
    else:
        services = l.query('GET services', columns, *arguments)

    # If no metrics= was specified on querystring, we take the string
    # from first service in our search result
    if not interesting_metrics and services:
        metric_set = set()
        for i in services:
            perfdata = pynag.Utils.PerfData(i.get('perf_data', ''))
            map(lambda x: metric_set.add(x.label), perfdata.metrics)
        interesting_metrics = sorted(list(metric_set))
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


def acknowledge(request):
    """ Acknowledge

    """
    if request.method != 'POST':
        raise Exception("Only use POST to this url")

    sticky = request.POST.get('sticky', 1)
    persistent = request.POST.get('persistent', 0)
    author = request.META.get('REMOTE_USER', 'anonymous')
    comment = request.POST.get('comment', 'acknowledged by Adagios')

    hostlist = request.POST.getlist('host', [])
    servicelist = request.POST.getlist('service', [])


@adagios_decorator
def status_hostgroup(request, hostgroup_name):
    """ Here for backwards compatibility """
    return hostgroup_detail(request, hostgroup_name=hostgroup_name)

@adagios_decorator
def status_detail(request):
    """ Here for backwards compatibility """
    return detail(request)