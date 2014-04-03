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
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.utils import simplejson
from django.core.context_processors import csrf
from django.template import RequestContext
from django.utils.translation import ugettext as _
from adagios.views import adagios_decorator

from django.core.urlresolvers import reverse

from adagios.okconfig_ import forms

import okconfig
import okconfig.network_scan
from pynag import Model


@adagios_decorator
def addcomplete(request, c=None):
    """ Landing page when a new okconfig group has been added
    """
    if not c:
        c = {}
    return render_to_response('addcomplete.html', c, context_instance=RequestContext(request))


@adagios_decorator
def addgroup(request):
    """ Add a new okconfig group

    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    # If there is a problem with the okconfig setup, lets display an error
    if not okconfig.is_valid():
        return verify_okconfig(request)

    if request.method == 'GET':
        f = forms.AddGroupForm(initial=request.GET)
    elif request.method == 'POST':
        f = forms.AddGroupForm(request.POST)
        if f.is_valid():
            group_name = f.cleaned_data['group_name']
            alias = f.cleaned_data['alias']
            #description = f.cleaned_data['description']
            force = f.cleaned_data['force']
            try:
                c['filelist'] = okconfig.addgroup(
                    group_name=group_name, alias=alias, force=force)
                c['group_name'] = group_name
                return addcomplete(request, c)
            except Exception, e:
                c['errors'].append("error adding group: %s" % e)
        else:
            c['errors'].append('Could not validate input')
    c['form'] = f
    return render_to_response('addgroup.html', c, context_instance=RequestContext(request))


@adagios_decorator
def addhost(request):
    """ Add a new host from an okconfig template
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    # If there is a problem with the okconfig setup, lets display an error
    if not okconfig.is_valid():
        return verify_okconfig(request)

    if request.method == 'GET':
        f = forms.AddHostForm(initial=request.GET)
    elif request.method == 'POST':
        f = forms.AddHostForm(request.POST)
        if f.is_valid():
            host_name = f.cleaned_data['host_name']
            group_name = f.cleaned_data['group_name']
            address = f.cleaned_data['address']
            templates = f.cleaned_data['templates']
            #description = f.cleaned_data['description']
            force = f.cleaned_data['force']
            try:
                c['filelist'] = okconfig.addhost(host_name=host_name, group_name=group_name, address=address,
                                                 force=force, templates=templates)
                c['host_name'] = host_name
                return addcomplete(request, c)
            except Exception, e:
                c['errors'].append("error adding host: %s" % e)
        else:
            c['errors'].append('Could not validate input')
    c['form'] = f
    return render_to_response('addhost.html', c, context_instance=RequestContext(request))


@adagios_decorator
def addtemplate(request, host_name=None):
    """ Add a new okconfig template to a host

    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    # If there is a problem with the okconfig setup, lets display an error
    if not okconfig.is_valid():
        return verify_okconfig(request)

    c['form'] = forms.AddTemplateForm(initial=request.GET)
    if request.method == 'POST':
        c['form'] = f = forms.AddTemplateForm(request.POST)
        if f.is_valid():
            try:
                f.save()
                c['host_name'] = host_name = f.cleaned_data['host_name']
                c['filelist'] = f.filelist
                c['messages'].append(
                    "Template was successfully added to host.")
                return HttpResponseRedirect(reverse('adagios.okconfig_.views.edit', args=[host_name]))
            except Exception, e:
                c['errors'].append(e)
        else:
            c['errors'].append("Could not validate form")
    return render_to_response('addtemplate.html', c, context_instance=RequestContext(request))


@adagios_decorator
def addservice(request):
    """ Create a new service derived from an okconfig template
    """
    c = {}
    c.update(csrf(request))
    c['form'] = forms.AddServiceToHostForm()
    c['messages'] = []
    c['errors'] = []
    c['filename'] = Model.config.cfg_file
    if request.method == 'POST':
        c['form'] = form = forms.AddServiceToHostForm(data=request.POST)
        if form.is_valid():
            host_name = form.cleaned_data['host_name']
            host = Model.Host.objects.get_by_shortname(host_name)
            service = form.cleaned_data['service']
            new_service = Model.Service()
            new_service.host_name = host_name
            new_service.use = service
            new_service.set_filename(host.get_filename())
            # new_service.reload_object()
            c['my_object'] = new_service

            # Add custom macros if any were specified
            for k, v in form.data.items():
                if k.startswith("_") or k.startswith('service_description'):
                    new_service[k] = v
            try:
                new_service.save()
                return HttpResponseRedirect(reverse('edit_object', kwargs={'object_id': new_service.get_id()}))
            except IOError, e:
                c['errors'].append(e)
        else:
            c['errors'].append("Could not validate form")
    return render_to_response('addservice.html', c, context_instance=RequestContext(request))


@adagios_decorator
def verify_okconfig(request):
    """ Checks if okconfig is properly set up. """
    c = {}
    c['errors'] = []
    c['okconfig_checks'] = okconfig.verify()
    for i in c['okconfig_checks'].values():
        if i == False:
            c['errors'].append(
                'There seems to be a problem with your okconfig installation')
            break
    return render_to_response('verify_okconfig.html', c, context_instance=RequestContext(request))


@adagios_decorator
def install_agent(request):
    """ Installs an okagent on a remote host """
    c = {}
    c['errors'] = []
    c['messages'] = []
    c['form'] = forms.InstallAgentForm(initial=request.GET)
    c['nsclient_installfiles'] = okconfig.config.nsclient_installfiles
    if request.method == 'POST':
        c['form'] = f = forms.InstallAgentForm(request.POST)
        if f.is_valid():
            f.clean()
            host = f.cleaned_data['remote_host']
            user = f.cleaned_data['username']
            passw = f.cleaned_data['password']
            method = f.cleaned_data['install_method']
            domain = f.cleaned_data['windows_domain']
            try:
                status, out, err = okconfig.install_okagent(
                    remote_host=host, domain=domain, username=user, password=passw, install_method=method)
                c['exit_status'] = status
                c['stderr'] = err
                # Do a little cleanup in winexe stdout, it is irrelevant
                out = out.split('\n')
                c['stdout'] = []
                for i in out:
                    if i.startswith('Unknown parameter encountered:'):
                        continue
                    elif i.startswith('Ignoring unknown parameter'):
                        continue
                    elif 'NT_STATUS_LOGON_FAILURE' in i:
                        c['hint'] = "NT_STATUS_LOGON_FAILURE usually means there is a problem with username or password. Are you using correct domain ?"
                    elif 'NT_STATUS_DUPLICATE_NAME' in i:
                        c['hint'] = "The security settings on the remote windows host might forbid logins if the host name specified does not match the computername on the server. Try again with either correct hostname or the ip address of the server."
                    elif 'NT_STATUS_ACCESS_DENIED' in i:
                        c['hint'] = "Please make sure that %s is a local administrator on host %s" % (
                            user, host)
                    elif i.startswith('Error: Directory') and i.endswith('not found'):
                        c['hint'] = "No nsclient copy found "
                    c['stdout'].append(i)
                c['stdout'] = '\n'.join(c['stdout'])
            except Exception, e:
                c['errors'].append(e)
        else:
            c['errors'].append('invalid input')

    return render_to_response('install_agent.html', c, context_instance=RequestContext(request))


@adagios_decorator
def edit(request, host_name):
    """ Edit all the Service "__MACROS" for a given host """

    c = {}
    c['errors'] = []
    c['messages'] = []
    c.update(csrf(request))
    c['hostname'] = host_name
    c['host_name'] = host_name
    c['forms'] = myforms = []

    try:
        c['myhost'] = Model.Host.objects.get_by_shortname(host_name)
    except KeyError, e:
        c['errors'].append("Host %s not found" % e)
        return render_to_response('edittemplate.html', c, context_instance=RequestContext(request))
    # Get all services of that host that contain a service_description
    services = Model.Service.objects.filter(
        host_name=host_name, service_description__contains='')

    if request.method == 'GET':
        for service in services:
            myforms.append(forms.EditTemplateForm(service=service))
    elif request.method == 'POST':
        # All the form fields have an id of HOST::SERVICE::ATTRIBUTE
        for service in services:
            form = forms.EditTemplateForm(service=service, data=request.POST)
            myforms.append(form)
            if form.is_valid():
                try:
                    if form.changed_data != []:
                        form.save()
                        c['messages'].append(
                            "'%s' successfully saved." % service.get_description())
                except Exception, e:
                    c['errors'].append(
                        "Failed to save service %s: %s" % (service.get_description(), e))
            else:
                c['errors'].append(
                    'invalid data in %s' % service.get_description())
        c['forms'] = myforms
    return render_to_response('edittemplate.html', c, context_instance=RequestContext(request))


@adagios_decorator
def choose_host(request):
    """Simple form that lets you choose one host to edit"""
    c = {}
    c.update(csrf(request))
    if request.method == 'GET':
        c['form'] = forms.ChooseHostForm(initial=request.GET)
    elif request.method == 'POST':
        c['form'] = forms.ChooseHostForm(data=request.POST)
        if c['form'].is_valid():
            host_name = c['form'].cleaned_data['host_name']
            return HttpResponseRedirect(reverse("adagios.okconfig_.views.edit", args=[host_name]))
    return render_to_response('choosehost.html', c, context_instance=RequestContext(request))


@adagios_decorator
def scan_network(request):
    """ Scan a single network and show hosts that are alive
    """
    c = {}
    c['errors'] = []
    if not okconfig.is_valid():
        return verify_okconfig(request)
    if request.method == 'GET':
            if request.GET.has_key('network_address'):
                initial = request.GET
            else:
                my_ip = okconfig.network_scan.get_my_ip_address()
                network_address = "%s/28" % my_ip
                initial = {'network_address': network_address}
            c['form'] = forms.ScanNetworkForm(initial=initial)
    elif request.method == 'POST':
        c['form'] = forms.ScanNetworkForm(request.POST)
        if not c['form'].is_valid():
            c['errors'].append("could not validate form")
        else:
            network = c['form'].cleaned_data['network_address']
            try:
                c['scan_results'] = okconfig.network_scan.get_all_hosts(
                    network)
                for i in c['scan_results']:
                    i.check()
            except Exception, e:
                c['errors'].append("Error running scan")
    return render_to_response('scan_network.html', c, context_instance=RequestContext(request))
