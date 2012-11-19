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
import forms
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
state = defaultdict(lambda: "unknown")
state[0] = "ok"
state[1] = "warning"
state[2] = "critical"
def index(request):
    c = {}
    c['nagios_cfg'] = pynag.Model.config.cfg_file
    c['version'] = __version__
    return render_to_response('frontpage.html', c, context_instance = RequestContext(request))

def settings(request):
    c = {}
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = e = []
    if request.method == 'GET':
        form = forms.AdagiosSettingsForm(initial=request.GET)
        form.is_valid()
    elif request.method == 'POST':
        form = forms.AdagiosSettingsForm(data=request.POST)
        if form.is_valid():
            try:
                form.save()
                m.append("%s successfully saved." % form.adagios_configfile)
            except IOError, exc:
                e.append(exc)
    c['form'] = form
    return render_to_response('settings.html', c, context_instance = RequestContext(request))

def contact_us( request ):
    """ Bring a small form that has a "contact us" form on it """
    c={}
    c.update(csrf(request))
    if request.method == 'GET':
        form = forms.ContactUsForm(initial=request.GET)
    else:
        form = forms.ContactUsForm(data=request.POST)
        if form.is_valid():
            form.save()
            c['thank_you'] = True
            c['sender'] = form.cleaned_data['sender']
        
    c['form'] = form
    return render_to_response('contact_us.html', c,  context_instance = RequestContext(request))

def nagios(request):
    c = {}
    c['nagios_url'] = adagios.settings.nagios_url
    return render_to_response('nagios.html', c, context_instance = RequestContext(request))

def map(request):
    c = {}
    return render_to_response('map.html', c, context_instance = RequestContext(request))

def gitlog(request):
    """ View that displays a nice log of previous git commits in dirname(config.cfg_file) """
    c = { }
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = []
    nagiosdir = dirname( pynag.Model.config.cfg_file or '/etc/nagios/')
    c['nagiosdir'] = nagiosdir
    c['commits'] = result = []
    if request.method == 'POST':
        try:
            git = pynag.Model.EventHandlers.GitEventHandler(nagiosdir, 'adagios', 'adagios')
            if 'git_init' in request.POST:
                git._git_init()
            elif 'git_commit' in request.POST:
                filelist = []
                commit_message = request.POST.get('git_commit_message', "bulk commit by adagios")
                for i in request.POST:
                    if i.startswith('commit_'):
                        filename=i[len('commit_'):]
                        git._git_add(filename)
                        filelist.append( filename )
                if len(filelist) == 0:
                    raise Exception("No files selected.")
                git._git_commit(filename=None, message=commit_message, filelist=filelist)
                m.append("%s files successfully commited." % len(filelist))
        except Exception, e:
            c['errors'].append( e )
    # Check if nagiosdir has a git repo or not
    try:
        git = pynag.Model.EventHandlers.GitEventHandler(nagiosdir, 'adagios', 'adagios')
        c['uncommited_files'] = git.get_uncommited_files()
    except pynag.Model.EventHandlers.EventHandlerError, e:
        if e.errorcode == 128:
            c['no_git_repo_found'] = True


    # Show git history
    try:
        fh = Popen(["git", "log" ,"-20", "--pretty=%H:%an:%ae:%at:%s"], cwd=nagiosdir, stdin=None, stdout=PIPE )
        gitstring = fh.communicate()[0]

        for logline in gitstring.splitlines():
            hash,author, authoremail, authortime, comment = logline.split(":", 4)
            result.append( {
                "hash": hash,
                "author": author,
                "authoremail": authoremail,
                "authortime": datetime.fromtimestamp(float(authortime)),
                "comment": comment,
                })
        # If a single commit was named in querystring, also fetch the diff for that commit
        commit = request.GET.get('show', False)
        if commit != False:
            fh = Popen(["git", "show" , commit], cwd=nagiosdir, stdin=None, stdout=PIPE )
            c['diff'] = fh.communicate()[0]
    except Exception, e:
        c['errors'].append( e )
    return render_to_response('gitlog.html', c, context_instance = RequestContext(request))

def nagios_service(request):
    """ View to restart / reload nagios service """
    c = {}
    c['errors'] = []
    c['messages'] = []
    nagios_bin = adagios.settings.nagios_binary
    nagios_init=adagios.settings.nagios_init_script
    nagios_cfg=adagios.settings.nagios_config
    if request.method == 'GET':
        form = forms.NagiosServiceForm(initial=request.GET)
    else:
        form = forms.NagiosServiceForm(data=request.POST)
        if form.is_valid():
            form.save()
            c['stdout'] = form.stdout
            c['stderr'] = form.stderr
    c['form'] = form
    service = pynag.Control.daemon(nagios_bin=nagios_bin, nagios_cfg=nagios_cfg, nagios_init=nagios_init)
    c['status'] = service.status()
    if pynag.Model.config.needs_reload() == True:
        c['messages'].append('Nagios Service Needs to be reloaded to apply latest configuration changes. Click Reload to reload Nagios Service now.')
    return render_to_response('nagios_service.html', c, context_instance = RequestContext(request))



def pnp4nagios(request):
    """ View to handle integration with pnp4nagios """
    c = {}
    c['errors'] = e=  []
    c['messages'] =m= []

    c['broker_module'] = forms.PNPBrokerModuleForm(initial=request.GET)
    c['templates_form'] = forms.PNPTemplatesForm(initial=request.GET)
    c['action_url'] = forms.PNPActionUrlForm(initial=request.GET)
    c['pnp_templates'] = forms.PNPTemplatesForm(initial=request.GET)

    try:
        c['npcd_config'] = forms.PNPConfigForm(initial=request.GET)
    except Exception, e:
        c['errors'].append(e)
    #c['interesting_objects'] = form.interesting_objects
    if request.method == 'POST' and 'save_broker_module' in request.POST:
        c['broker_module'] = broker_form = forms.PNPBrokerModuleForm(data=request.POST)
        if broker_form.is_valid():
            broker_form.save()
            m.append("Broker Module updated in nagios.cfg")
    elif request.method == 'POST' and 'save_action_url' in request.POST:
        c['action_url'] = forms.PNPActionUrlForm(data=request.POST)
        if c['action_url'].is_valid():
            c['action_url'].save()
            m.append('Action_url updated for %s services' % c['action_url'].total_services)
            if c['action_url'].error_services  > 0:
                e.append("%s services could not be updated (check permissions?)" % c['action_url'].error_services)
    elif request.method == 'POST' and 'save_npcd_config' in request.POST:
        c['npcd_config'] = forms.PNPConfigForm(data=request.POST)
        if c['npcd_config'].is_valid():
            c['npcd_config'].save()
            m.append("npcd.cfg updated")


    return render_to_response('pnp4nagios.html', c, context_instance = RequestContext(request))

def status(request):
    c = {}
    c['messages'] = []
    from collections import defaultdict
    state = defaultdict(lambda: "info")
    state["0"] = "success"
    state["1"] = "warning"
    state["2"] = "danger"
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

def edit_file(request, filename):
    c = {}
    c['messages'] = []
    c['errors'] = []
    try:
        c['form'] = forms.EditFileForm(filename=filename,initial=request.GET)
        c['filename'] = filename
        if request.method == 'POST':
            c['form'] = forms.EditFileForm(filename=filename,data=request.POST)
            if c['form'].is_valid():
                c['form'].save()
    except Exception, e:
        c['errors'].append(e)
    return render_to_response('editfile.html', c, context_instance = RequestContext(request))
def status_host(request, host_name, service_description=None):
    c = { }
    c['messages'] = []
    livestatus = pynag.Parsers.mk_livestatus()

    c['services'] = services = []
    all_services = livestatus.get_services()
    all_hosts = livestatus.get_hosts()
    for service in all_services:
        service['status'] = state[service['state']]
        if service['host_name'] == host_name:
            services.append(service)
            if service['description'] == service_description:
                c['service'] = service
    for i in all_hosts:
        if i['name'] == host_name:
            c['host'] = host = i
    c['host_name'] = host_name
    c['service_description'] = service_description
    host['status'] = state[host['state']]
    if service_description:
        from pynag import Model
        perfdata = c['service']['perf_data']
        perfdata = pynag.Utils.PerfData(perfdata)
        for i in perfdata.metrics:
            i.status = state[i.get_status()]
        c['perfdata'] = perfdata.metrics

        # Temp hack for livestatus troubleshooting
        livestatus_keys = []
        for k,v in service.items():
            livestatus_keys.append("<tr><td>%s</td><td>%s</td></tr>" % (k,v) )
        c['livestatus_keys'] = livestatus_keys

    return render_to_response('status_host.html', c, context_instance = RequestContext(request))

def status_hostgroup(request, hostgroup_name=None):
    c = { }
    c['messages'] = []
    livestatus = pynag.Parsers.mk_livestatus()
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