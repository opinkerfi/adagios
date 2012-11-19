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
from django.template import RequestContext
import os

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

livestatus = pynag.Parsers.mk_livestatus()
livestatus.test()

state = defaultdict(lambda: "unknown")
state[0] = "ok"
state[1] = "warning"
state[2] = "critical"

def status(request):
    c = {}
    c['messages'] = []
    from collections import defaultdict
    livestatus = pynag.Parsers.mk_livestatus()
    all_hosts = livestatus.get_hosts()

    #from pynag import Parsers
    #s = Parsers.status()
    #s.parse()
    #all_hosts = s.data['hoststatus']
    #all_services = s.data['servicestatus']
    services = defaultdict(list)
    hosts = []
    all_services = livestatus.get_services()
    for service in all_services:
    #    service['status'] = state[service['state']]
        for k,v in request.GET.items():
            if k in service:
                if str(service[k]) == str(v):
                    continue
                else:
                    break
            elif k.endswith('__isnot') and k[:-1*len("__isnot")] in service:
                print "got here"
                if str(service[k[:-1*len("__isnot")]]) == str(v):
                    break
        else:
            service['status'] = state[service['state']]
            services[ service['host_name'] ].append(service)
    #    services[service['host_name']].append( service )
    for host in all_hosts:
        if len(services[host['name']]) > 0:
            host['status'] = state[host['state']]
            host['services'] = services[host['name']]
            hosts.append( host )
    hosts.sort()
    c['services'] = services
    c['hosts'] = hosts
    return render_to_response('status.html', c, context_instance = RequestContext(request))

def status_detail(request, host_name, service_description=None):
    """ Displays status details for one host or service """
    c = { }
    c['messages'] = []
    c['errors'] = []
    livestatus = pynag.Parsers.mk_livestatus()

    try:
        c['host'] = my_host = livestatus.get_host(host_name)
    except IndexError:
        c['errors'].append("Could not find any host named '%s'"%host_name)
        return render_to_response('status_detail.html', c, context_instance = RequestContext(request))

    if service_description is None:
        primary_object = my_host
    else:
        try:
            c['service'] = my_service = livestatus.get_service(host_name,service_description)
            primary_object = my_service
        except IndexError:
            c['errors'].append("Could not find any service named '%s'"%service_description)
            return render_to_response('status_detail.html', c, context_instance = RequestContext(request))

    c['my_object'] = primary_object

    # Friendly statusname (i.e. turn 2 into "critical")
    primary_object['status'] = state[primary_object['state']]

    # Service list on the sidebar should be sorted
    my_host['services_with_info'] = sorted(my_host['services_with_info'])
    c['host_name'] = host_name
    c['service_description'] = service_description

    perfdata = primary_object['perf_data']
    perfdata = pynag.Utils.PerfData(perfdata)
    for i in perfdata.metrics:
        i.status = state[i.get_status()]
    c['perfdata'] = perfdata.metrics

    # Get the event log
    c['log'] = livestatus.query('GET log', 'Limit: 50', 'Filter: host_name = %s' % host_name)


    return render_to_response('status_detail.html', c, context_instance = RequestContext(request))

def status_hostgroup(request, hostgroup_name=None):
    c = { }
    c['messages'] = []
    hostgroups = livestatus.get_hostgroups()
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
    return render_to_response('status_hostgroup.html', c, context_instance = RequestContext(request))

def test_livestatus(request):
    """ This view is a test on top of mk_livestatus which allows you to enter your own queries """
    c = { }
    c['messages'] = []
    livestatus = pynag.Parsers.mk_livestatus()
    query = request.GET.get('q') or 'GET hostgroups'
    c['query'] = query

    c['results'] = livestatus.query(query)
    c['header'] = c['results'][0].keys()
    return render_to_response('test_livestatus.html', c, context_instance = RequestContext(request))