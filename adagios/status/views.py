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

from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse

from django.template import RequestContext
import os
import time

import pynag.Model
import pynag.Utils
import pynag.Control
import pynag.Plugins
import pynag.Model.EventHandlers
import os.path
from time import mktime
from datetime import datetime
from os.path import dirname
from subprocess import Popen, PIPE

import adagios.settings
from adagios import __version__
from collections import defaultdict

import pnp.functions
import json

state = defaultdict(lambda: "unknown")
state[0] = "ok"
state[1] = "warning"
state[2] = "critical"

def status_parents(request):
    c = {}
    c['messages'] = []
    from collections import defaultdict
    authuser = request.GET.get('contact_name', None)
    livestatus = pynag.Parsers.mk_livestatus(authuser=authuser)
    all_hosts = livestatus.get_hosts()
    all_services = livestatus.get_services()
    all_contacts = livestatus.get_contacts()
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
                i['child_hosts'].append( host_dict[x] )
                if host_dict[x]['state'] == 0:
                    ok += 1
                else:
                    crit += 1
            total = float(len(i['childs']))
            i['health'] = float(ok) / total * 100.0
            i['percent_ok'] = ok/total*100
            i['percent_crit'] = crit/total*100

    return render_to_response('status_parents.html', c, context_instance = RequestContext(request))


def _status(request):
    """ Helper function for a lot of status views, handles fetching of objects, populating context, and filtering, etc.

    Returns:
        hash map with request context
    Examples:
        c = _status(request)
        return render_to_response('status_parents.html', c, context_instance = RequestContext(request))
    """
    c = {}
    c['messages'] = []
    from collections import defaultdict
    authuser = request.GET.get('contact_name', None)
    livestatus = pynag.Parsers.mk_livestatus(authuser=authuser)
    all_hosts = livestatus.get_hosts()
    all_services = livestatus.get_services()
    all_contacts = livestatus.get_contacts()
    c['contacts'] = all_contacts
    c['current_contact'] = authuser
    c['request'] = request

    services = defaultdict(list)
    hosts = []
    for service in all_services:
        # Tag the service with tags such as problems and unhandled
        tags = []
        if service['state'] != 0:
            tags.append('problem')
            tags.append('problems')
            if service['acknowledged'] == 0 and service['downtimes'] == []:
                tags.append('unhandled')
        else:
            tags.append('ok')
        if service['acknowledged'] == 1:
            tags.append('acknowledged')
        if service['downtimes'] != []:
            tags.append('downtime')
        service['tags'] = ' '.join(tags)

        for k,v in request.GET.items():
            if k == 'q' and v is not None and v != '':
                q = str(v).lower()
                if q in service['description'].lower() or q in service['host_name'].lower() or q in service['tags']:
                    continue
                else:
                    break
            elif k in service:
                if type(service[k]) is type([]) and str(v) in service[k]:
                    continue
                elif str(service[k]) == str(v):
                    continue
                else:
                    break
            elif k.endswith('__isnot') and k[:-1*len("__isnot")] in service:
                if str(service[k[:-1*len("__isnot")]]) == str(v):
                    break
        else:
            service['status'] = state[service['state']]
            services[ service['host_name'] ].append(service)

    #    services[service['host_name']].append( service )
    for host in all_hosts:
        host['num_problems'] = host['num_services_crit'] +  host['num_services_warn'] +  host['num_services_unknown']
        host['children'] = host['services_with_state']
        if len(services[host['name']]) > 0:
            host['status'] = state[host['state']]
            host['services'] = services[host['name']]
            hosts.append( host )
    # Sort by service status
    hosts.sort(reverse=True, cmp=lambda a,b: cmp(a['num_problems'], b['num_problems']))
    c['services'] = services
    c['hosts'] = hosts
    seconds_in_a_day = 60*60*24
    today = time.time() % seconds_in_a_day # midnight of today
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

def status(request):
    c = _status(request)
    return render_to_response('status.html', c, context_instance = RequestContext(request))

def status_detail(request, host_name, service_description=None):
    """ Displays status details for one host or service """
    c = { }
    c['messages'] = []
    c['errors'] = []
    livestatus = pynag.Parsers.mk_livestatus()
    c['pnp_url'] = adagios.settings.pnp_url
    c['nagios_url'] = adagios.settings.nagios_url
    c['request'] = request
    now = time.time()
    seconds_in_a_day = 60*60*24
    seconds_passed_today = now % seconds_in_a_day
    today = now - seconds_passed_today # midnight of today

    try:
        c['host'] = my_host = livestatus.get_host(host_name)
        my_host['object_type'] = 'host'
        my_host['short_name'] = my_host['name']
    except IndexError:
        c['errors'].append("Could not find any host named '%s'"%host_name)
        return render_to_response('status_detail.html', c, context_instance = RequestContext(request))

    if service_description is None:
        primary_object = my_host
        c['service_description'] = '_HOST_'

        c['log'] = livestatus.query('GET log',
            'Filter: time >= %s' % today,
            'Limit: 50',
            'Filter: host_name = %s' % host_name,
        )
    else:
        try:
            c['service'] = my_service = livestatus.get_service(host_name,service_description)
            my_service['object_type'] = 'service'
            c['service_description'] = service_description
            my_service['short_name'] = "%s/%s" % (my_service['host_name'], my_service['description'])
            primary_object = my_service
            c['log'] = livestatus.query('GET log',
                'Filter: time >= %s' % today,
                'Filter: host_name = %s' % host_name,
                'Filter: service_description = %s' % service_description,
                'Limit: 50',
            )
        except IndexError:
            c['errors'].append("Could not find any service named '%s'"%service_description)
            return render_to_response('status_detail.html', c, context_instance = RequestContext(request))

    c['my_object'] = primary_object

    # Friendly statusname (i.e. turn 2 into "critical")
    primary_object['status'] = state[primary_object['state']]

    # Plugin longoutput comes to us with special characters escaped. lets undo that:
    primary_object['long_plugin_output'] = primary_object['long_plugin_output'].replace('\\n','\n')

    # Service list on the sidebar should be sorted
    my_host['services_with_info'] = sorted(my_host['services_with_info'])
    c['host_name'] = host_name

    perfdata = primary_object['perf_data']
    perfdata = pynag.Utils.PerfData(perfdata)
    for i,datum in enumerate(perfdata.metrics):
        datum.i = i
        datum.status = state[datum.get_status()]
    c['perfdata'] = perfdata.metrics

    # Create some state history progress bar from our logs:
    if len(c['log']) > 0:
        log = c['log']
        start_time = log[-1]['time']
        end_time = log[0]['time']
        now = time.time()

        duration = now - start_time
        state_hist = []
        start = start_time
        last_item = None
        css_hint = {}
        css_hint[0] = 'success'
        css_hint[1] = 'warning'
        css_hint[2] = 'danger'
        css_hint[3] = 'info'
        for i in reversed(log):
            if not i['class'] == 1:
                continue
            if not last_item is None:
                last_item['end_time'] = i['time']
                last_item['duration'] = d = last_item['end_time'] - last_item['time']
                last_item['duration_percent'] = 100*d/duration
            i['bootstrap_status'] = css_hint[i['state']]
            last_item = i
        if not last_item is None:
            last_item['end_time'] = now
            last_item['duration'] = d = last_item['end_time'] - last_item['time']
            last_item['duration_percent'] = 100*d/duration

    # Lets get some graphs
    try:
        tmp = pnp.functions.run_pnp("json", host=host_name)
        tmp = json.loads(tmp)
    except Exception, e:
        tmp = []
        c['errors'].append(e)
    c['graph_urls'] = tmp

    return render_to_response('status_detail.html', c, context_instance = RequestContext(request))

def status_hostgroup(request, hostgroup_name=None):
    c = { }
    c['messages'] = []
    c['errors'] = []
    livestatus = pynag.Parsers.mk_livestatus()
    hostgroups = livestatus.get_hostgroups()
    c['hostgroup_name'] = hostgroup_name
    c['request'] = request

    # Lets establish a good list of all hostgroups and parentgroups
    all_hostgroups = pynag.Model.Hostgroup.objects.all
    all_subgroups = set() # all hostgroups that belong in some other hostgroup
    hostgroup_parentgroups = defaultdict(set) # "subgroup":['master1','master2']
    hostgroup_childgroups = pynag.Model.ObjectRelations.hostgroup_hostgroups

    for hostgroup,subgroups in hostgroup_childgroups.items():
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
        my_hostgroup = pynag.Model.Hostgroup.objects.get_by_shortname(hostgroup_name)
        subgroups = my_hostgroup.hostgroup_members or ''
        subgroups = subgroups.split(',')
        # Strip out any group that is not a subgroup of hostgroup_name
        right_hostgroups = []
        for group in hostgroups:
            if group.get('name','') in subgroups:
                right_hostgroups.append(group)
        c['hostgroups'] = right_hostgroups

        # If a hostgroup was specified lets also get all the hosts for it
        c['hosts'] = livestatus.query('GET hosts', 'Filter: host_groups >= %s' % hostgroup_name)
    for host in c['hosts']:
        ok = host.get('num_services_ok')
        warn = host.get('num_services_warn')
        crit = host.get('num_services_crit')
        pending = host.get('num_services_pending')
        unknown = host.get('num_services_unknown')
        total = ok + warn + crit +pending + unknown
        host['total'] = total
        host['problems'] = warn + crit + unknown
        try:
            total = float(total)
            host['health'] = float(ok) / total * 100.0
            host['percent_ok'] = ok/total*100
            host['percent_warn'] = warn/total*100
            host['percent_crit'] = crit/total*100
            host['percent_unknown'] = unknown/total*100
            host['percent_pending'] = pending/total*100
        except ZeroDivisionError:
            host['health'] = 'n/a'
    # Extra statistics for our hostgroups
    for hg in c['hostgroups']:
        ok = hg.get('num_services_ok')
        warn = hg.get('num_services_warn')
        crit = hg.get('num_services_crit')
        pending = hg.get('num_services_pending')
        unknown = hg.get('num_services_unknown')
        total = ok + warn + crit +pending + unknown
        hg['total'] = total
        hg['problems'] = warn + crit + unknown
        try:
            total = float(total)
            hg['health'] = float(ok) / total * 100.0
            hg['health'] = float(ok) / total * 100.0
            hg['percent_ok'] = ok/total*100
            hg['percent_warn'] = warn/total*100
            hg['percent_crit'] = crit/total*100
            hg['percent_unknown'] = unknown/total*100
            hg['percent_pending'] = pending/total*100
        except ZeroDivisionError:
            pass
    return render_to_response('status_hostgroup.html', c, context_instance = RequestContext(request))

def status_tiles(request, object_type="host"):
    """
    """
    c = _status(request)
    return render_to_response('status_tiles.html', c, context_instance = RequestContext(request))

def status_host(request):
    c =  _status(request)
    c['host_name'] = request.GET.get('detail', None)
    for host in c['hosts']:
        ok = host.get('num_services_ok')
        warn = host.get('num_services_warn')
        crit = host.get('num_services_crit')
        pending = host.get('num_services_pending')
        unknown = host.get('num_services_unknown')
        total = ok + warn + crit +pending + unknown
        host['total'] = total
        host['problems'] = warn + crit + unknown
        try:
            total = float(total)
            host['health'] = float(ok) / total * 100.0
            host['percent_ok'] = ok/total*100
            host['percent_warn'] = warn/total*100
            host['percent_crit'] = crit/total*100
            host['percent_unknown'] = unknown/total*100
            host['percent_pending'] = pending/total*100
        except ZeroDivisionError:
            host['health'] = 'n/a'
    return render_to_response('status_host.html', c, context_instance = RequestContext(request))
def status_boxview(request):
    c = _status(request)

    return render_to_response('status_boxview.html', c, context_instance = RequestContext(request))

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

    livestatus = pynag.Parsers.mk_livestatus()
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

    return render_to_response('status_paneview.html', c, context_instance = RequestContext(request))

def status_index(request):
    c = _status_combined(request)
    top_alert_producers = defaultdict(int)
    top_alert_producers['test'] = 5
    for i in c['log']:
        top_alert_producers[i['host_name']] += 1
    top_alert_producers = top_alert_producers.items()
    top_alert_producers.sort(cmp=lambda a,b: cmp(a[1],b[1]), reverse=True)
    c['top_alert_producers'] = top_alert_producers
    return render_to_response('status_index.html', c, context_instance = RequestContext(request))
def test_livestatus(request):
    """ This view is a test on top of mk_livestatus which allows you to enter your own queries """
    c = { }
    c['messages'] = []
    c['table'] = table = request.GET.get('table')

    livestatus = pynag.Parsers.mk_livestatus()
    if table is not None:
        columns = livestatus.query('GET columns', 'Filter: table = %s' % table)
        c['columns'] = columns

        columns = ""
        limit = request.GET.get('limit')
        run_query = False
        for k,v in request.GET.items():
            if k == "submit":
                run_query = True
            if k.startswith('check_'):
                columns += " " + k[len("check_"):]
        # Any columns checked means we return a query
        query = ['GET %s' % table]
        if len(columns) > 0:
            query.append("Columns: %s" % columns)
        if limit != '' and limit > 0:
            query.append( "Limit: %s" % limit )
        if run_query == True:
            c['results'] = livestatus.query(*query)
            c['query'] = livestatus.last_query
            c['header'] = c['results'][0].keys()

    return render_to_response('test_livestatus.html', c, context_instance = RequestContext(request))

def _status_combined(request):
    """ Returns a combined status of network outages, host problems and service problems
    """
    c = {}
    livestatus = pynag.Parsers.mk_livestatus()
    hosts = livestatus.get_hosts()
    services = livestatus.get_services()
    hosts_that_are_down = []
    hostnames_that_are_down = []
    service_status = [0,0,0,0]
    host_status = [0,0,0,0]
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
        if len(host['childs']) == 0:
            host_problems.append(host)
        else:
            network_problems.append(host)
    for service in services:
        service_status[service["state"]] += 1
        if service['state'] != 0 and service['acknowledged'] == 0 and len(service['downtimes']) == 0 and not service['host_name'] in hostnames_that_are_down:
            service_problems.append(service)
    c['network_problems'] = network_problems
    c['host_problems'] = host_problems
    c['service_problems'] = service_problems
    c['hosts'] = hosts
    c['services'] = services
    c['parents'] = parents
    service_totals = float(sum(service_status))
    host_totals = float(sum(host_status))
    c['service_status'] = map(lambda x: 100*x/service_totals, service_status)
    c['host_status'] = map(lambda x: 100*x/host_totals, host_status)
    seconds_in_a_day = 60*60*24
    today = time.time() % seconds_in_a_day # midnight of today
    c['log'] = livestatus.query('GET log',
        'Filter: time >= %s' % today,
        'Filter: type ~ ALERT',
        'Limit: 100',
    )
    return c

def status_problems(request):
    #c = _status(request)
    c = _status_combined(request)
    return render_to_response('status_problems.html', c, context_instance = RequestContext(request))


def _parse_nagios_logline(line):
    ''' Parse one nagios logline and return hashmap
    '''
    import re
    m = re.search('^\[(.*?)\] (.*?): (.*)', line)
    if m is None:
        return {}
    timestamp, logtype, message = m.groups()

    result = {}
    if logtype in ('CURRENT HOST STATE', 'CURRENT SERVICE STATE', 'SERVICE ALERT', 'HOST ALERT'):
        result['time'] = int(timestamp)
        result['type'] = logtype
        result['message'] = message
        if logtype.find('HOST') > -1:
            # This matches host current state:
            m = re.search('(.*?);(.*?);(.*);(.*?);(.*)', message)
            host, state, hard, check_attempt, plugin_output = m.groups()
            service_description=None
        if logtype.find('SERVICE') > -1:
            m = re.search('(.*?);(.*?);(.*?);(.*?);(.*?);(.*)', message)
            host,service_description,state,hard,check_attempt,plugin_output = m.groups()
        result['host_name'] = host
        result['service_description'] = service_description
        result['state'] = int( pynag.Plugins.state[state] )
        result['check_attempt'] = check_attempt
        result['plugin_output'] = plugin_output

    return result
def _get_state_history(start_time=None, end_time=None, host=None, service_description=None):
    """ Parses nagios logfiles and returns state history  """
    log_file = pynag.Model.config.get_cfg_value('log_file')
    log_archive_path = pynag.Model.config.get_cfg_value('log_archive_path')

    # First, lets peek in the logfiles and see how many files we have to read:
    result = []
    for line in open(log_file).readlines():
        parsed_line = _parse_nagios_logline( line )
        if parsed_line !=  {}:
            result.append(parsed_line)
    return result
def state_history(request):
    c = {}
    c['messages'] = []
    c['errors'] = []

    livestatus = pynag.Parsers.mk_livestatus()
    start_time = request.GET.get('start_time', None)
    end_time = request.GET.get('end_time', None)
    if end_time is None:
        end_time = time.time()
    end_time = int(end_time)
    if start_time is None:
        #start_time = livestatus.query('GET status')[0]['last_log_rotation']
        #print start_time
        seconds_in_a_day = 60*60*24
        seconds_today = end_time % seconds_in_a_day # midnight of today
        start_time = end_time - seconds_today
    start_time = int(start_time)
    c['log'] = log = _get_state_history()
    #start_time = c['log'][0]['time']
    #c['log'] = log = livestatus.query('GET log',
    #    'Filter: time >= %s' % start_time,
    #    'Filter: type ~ CURRENT',
    #)
    #log.reverse()
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
        short_name = "%s/%s" % (i['host_name'],i['service_description'])
        for k,v in request.GET.items():
            if k in i.keys() and i[k] != v:
                print k, "found in ", short_name
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
            services[short_name]['worst_logfile_state'] = max(services[short_name]['worst_logfile_state'], i['state'])
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
                last_item['duration'] = duration = last_item['end_time']  - last_item['time']
                last_item['duration_percent'] = 100 * float(duration) / total_duration
                service['duration'] += last_item['duration_percent']
                if last_item['state'] == 0:
                    service['sla'] += last_item['duration_percent']
                else:
                    service['num_problems'] += 1
            last_item = i
        if not last_item is None:
            last_item['end_time'] = end_time
            last_item['duration'] = duration = last_item['end_time']  - last_item['time']
            last_item['duration_percent'] = 100 * duration / total_duration
            service['duration'] += last_item['duration_percent']
            if last_item['state'] == 0:
                service['sla'] += last_item['duration_percent']
            else:
                service['num_problems'] += 1


    c['services'] = services
    c['start_time'] = start_time
    c['end_time'] = end_time
    return render_to_response('state_history.html', c, context_instance = RequestContext(request))


def _status_log(request):
    """ Helper function to any status view that requires log access """
    c = {}
    c['messages'] = []
    c['errors'] = []
    livestatus = pynag.Parsers.mk_livestatus()
    start_time = request.GET.get('start_time', None)
    end_time = request.GET.get('end_time', None)
    host_name = request.GET.get('host_name', None)
    service_description = request.GET.get('service_description', None)
    limit = request.GET.get('limit', None)
    log_class = request.GET.get('class', None)

    if end_time is None:
        end_time = int(time.time())
    end_time = int(end_time)

    if start_time is None:
        seconds_in_a_day = 60*60*24
        seconds_today = end_time % seconds_in_a_day # midnight of today
        start_time = end_time - seconds_today
    start_time = int(start_time)

    if limit is None:
        limit = 500
    query = ['GET log']
    if start_time is not None:
        query.append('Filter: time >= %s' % start_time)
    #if end_time is not None:
    #    query.append('Filter: time <= %s' % end_time)
    if log_class is not None:
        query.append('Filter: class = %s' % log_class)
    if limit is not None:
        query.append('Limit: %s' % limit)
    if host_name is not None:
        query.append('Filter: host_name = %s' % host_name)
    if service_description is not None:
        query.append('Filter: service_description = %s' % service_description)
    c['log'] = log = livestatus.query(*query)

    return c

def status_log(request):
    c = _status_log(request)
    c['request'] = request
    return render_to_response('status_log.html', c, context_instance = RequestContext(request))