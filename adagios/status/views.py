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
            for x in i['childs']:
                if host_dict[x]['state'] == 0:
                    ok += 1
                else:
                    crit += 1
            total = float(len(i['childs']))
            i['health'] = float(ok) / total * 100.0
            i['percent_ok'] = ok/total*100
            i['percent_crit'] = crit/total*100

    return render_to_response('status_parents.html', c, context_instance = RequestContext(request))


def status(request):
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
        for k,v in request.GET.items():
            if k == 'q' and v is not None and v != '':
                q = str(v).lower()
                if q in service['description'].lower() or q in service['host_name'].lower():
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

    #    services[service['host_name']].append( service )
    for host in all_hosts:
        if len(services[host['name']]) > 0:
            host['status'] = state[host['state']]
            host['services'] = services[host['name']]
            hosts.append( host )
    hosts.sort()
    c['services'] = services
    c['hosts'] = hosts
    seconds_in_a_day = 60*60*24
    today = time.time() % seconds_in_a_day # midnight of today

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
    seconds_in_a_day = 60*60*24
    today = time.time() % seconds_in_a_day # midnight of today

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
                'Filter: time >= %s' % time.time(),
                'Filter: host_name = %s' % host_name,
                'Limit: 50',
                'Filter: service_description = %s' % service_description,
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

def status_treeview(request, hostgroup_name=None):
    c = { }
    c['messages'] = []
    livestatus = pynag.Parsers.mk_livestatus()
    c['all_hostgroups'] = hostgroups = livestatus.get_hostgroups()

    c['hostgroup_name'] = hostgroup_name

    if hostgroup_name is None:
        c['hostgroups'] = hostgroups
        c['hosts'] = livestatus.get_hosts()
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
    return render_to_response('status_treeview.html', c, context_instance = RequestContext(request))

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
        query = []
        query.append( 'GET %s' % table )
        if len(columns) > 0:
            query.append("Columns: %s" % columns)
        if limit != '' and limit > 0:
            query.append( "Limit: %s" % limit )
        if run_query == True:
            c['results'] = livestatus.query(*query)
            c['query'] = livestatus.last_query
            c['header'] = c['results'][0].keys()

    return render_to_response('test_livestatus.html', c, context_instance = RequestContext(request))


