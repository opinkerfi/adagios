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
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
from django.core.context_processors import csrf
from django.template import RequestContext

from okconfig import forms
#import okconfig.forms

from configurator import okconfig
import configurator.okconfig.network_scan

def addcomplete(request, c={}):
    return render_to_response('addcomplete.html', c)

def addgroup(request):
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
                msg = okconfig.addgroup(group_name=group_name,alias=alias,force=force)
                c['messages'].append( msg  )
                c['group_name'] = group_name
                return addcomplete(request, c)
            except BaseException, e:
                c['errors'].append( "error adding group: %s" % e ) 
        else:
            c['errors'].append( 'Could not validate input')
    c['form'] = f
    return render_to_response('addgroup.html', c, context_instance=RequestContext(request))

def addhost(request):
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
            #description = f.cleaned_data['description']
            force = f.cleaned_data['force']
            try:
                msg = okconfig.addhost(host_name=host_name,group_name=group_name,address=address,force=force)
                c['messages'].append( msg  )
                c['host_name'] = host_name
                return addcomplete(request, c)
            except BaseException, e:
                c['errors'].append( "error adding host: %s" % e ) 
        else:
            c['errors'].append( 'Could not validate input')
    c['form'] = f
    return render_to_response('addhost.html', c, context_instance=RequestContext(request))


def addtemplate(request, host_name=None):
    c = {}
    c['messages'] = []
    c['errors'] = []
    # If there is a problem with the okconfig setup, lets display an error
    if not okconfig.is_valid():
        return verify_okconfig(request)

    c['form'] = forms.AddTemplateForm(initial=request.GET )
    if request.method == 'POST':
        f = forms.AddTemplateForm(request.POST)
        if f.is_valid():
            host_name = f.cleaned_data['host_name']
            template_name = f.cleaned_data['template_name']
            force =f.cleaned_data['force']
            try:
                msg = okconfig.addtemplate(host_name=host_name, template_name=template_name,force=force)
                c['messages'].append( msg )
                c['host_name'] = host_name
                return addcomplete(request, c)
            except BaseException, e:
                c['errors'] = e
        else:
            c['errors'].append( 'Could not validate input' ) 
    return render_to_response('addtemplate.html', c, context_instance=RequestContext(request))

def verify_okconfig(request):
    ''' Checks if okconfig is properly set up. '''
    c = {}
    c['errors'] = []
    c['okconfig_checks'] = okconfig.verify()
    for i in c['okconfig_checks'].values():
        if i == False:
            c['errors'].append('There seems to be a problem with your okconfig installation')
            break
    return render_to_response('verify_okconfig.html', c, context_instance=RequestContext(request))

def scan_network(request):
    c = {}
    c['errors'] = []
    if not okconfig.is_valid():
        return verify_okconfig(request)
    if request.method == 'GET':
            if request.GET.has_key('network_address'):
                initial = request.GET
            else:
                my_ip = configurator.okconfig.network_scan.get_my_ip_address()
                network_address = "%s/29" % my_ip
                initial = { 'network_address':network_address }
            c['form'] = forms.ScanNetworkForm(initial=initial)
    elif request.method == 'POST':
        c['form'] = forms.ScanNetworkForm(request.POST)
        if not c['form'].is_valid():
            c['errors'].append( "could not validate form")
        else:
            network = c['form'].cleaned_data['network_address']
            c['scan_results'] =  configurator.okconfig.network_scan.get_all_hosts(network)
            for i in c['scan_results']: i.check()
    return render_to_response('scan_network.html', c, context_instance=RequestContext(request))