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
state = defaultdict(lambda: "info")
state["0"] = "success"
state["1"] = "warning"
state["2"] = "danger"
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
    return render_to_response('nagios_service.html', c, context_instance = RequestContext(request))



def pnp4nagios(request):
    """ View to handle integration with pnp4nagios """
    c = {}
    c['errors'] = e=  []
    c['messages'] =m= []

    c['form'] = form = forms.EditAllForm('service','action_url', '/new_url', initial=request.GET)
    c['interesting_objects'] = form.interesting_objects
    return render_to_response('pnp4nagios.html', c, context_instance = RequestContext(request))

def status(request):
    c = {}
    c['messages'] = []
    from collections import defaultdict
    state = defaultdict(lambda: "info")
    state["0"] = "success"
    state["1"] = "warning"
    state["2"] = "danger"
    from pynag import Parsers
    s = Parsers.status()
    s.parse()
    all_hosts = s.data['hoststatus']
    all_services = s.data['servicestatus']
    services = defaultdict(list)
    hosts = []
    for service in all_services:
        service['status'] = state[service['current_state']]
        for k,v in request.GET.items():
            if k.startswith('not__'):
                k = k[len('not__'):]
                if k in service and service[k] == v:
                    break
                continue
            if k in service and service[k] != v:
                break
        else:
            services[service['host_name']].append( service )
    for host in all_hosts:
        if len(services[host['host_name']]) > 0:
            host['status'] = state[host['current_state']]
            host['services'] = services[host['host_name']]
            hosts.append( host )
    hosts.sort()
    c['services'] = services
    c['hosts'] = hosts
    return render_to_response('status.html', c, context_instance = RequestContext(request))

def status_host(request, host_name, service_description=None):
    c = { }
    c['messages'] = []
    f = forms.PerfDataForm(initial=request.GET)
    from pynag import Parsers
    s = Parsers.status()
    s.parse()
    c['services'] = services = []
    all_services = s.data['servicestatus']
    for service in all_services:
        if service['host_name'] == host_name:
            service['status'] = state[service['current_state']]
            services.append(service)
    host = c['host'] = s.get_hoststatus(host_name)
    c['host_name'] = host_name
    c['service_description'] = service_description
    host['status'] = state[host['current_state']]
    if service_description:
        c['service'] = i = s.get_servicestatus(host_name, service_description)
        from pynag import Model
        perfdata = i.get('performance_data', 'a=1')
        perfdata = Model.PerfData(perfdata)
        for i in perfdata.metrics:
            if i.status == "ok":
                i.csstag = "success"
            elif i.status == "warning":
                i.csstag = "warning"
            elif i.status == "critical":
                i.csstag = "danger"
            else:
                i.csstag = "info"
        c['perfdata'] = perfdata.metrics

    return render_to_response('status_host.html', c, context_instance = RequestContext(request))
