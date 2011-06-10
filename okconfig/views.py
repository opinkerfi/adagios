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
import okconfig.forms

from configurator import okconfig

def addgroup(request):
    c = {}
    form = c['form'] = forms.AddGroupForm()
    if request.POST:
        # TODO: Do interesting submit stuff
        pass
    return render_to_response('addgroup.html', c, context_instance=RequestContext(request))

def addhost(request):
    c = {}
    form = c['form'] = forms.AddHostForm()
    if request.POST:
        # TODO: Do interesting submit stuff
        pass
    return render_to_response('addhost.html', c, context_instance=RequestContext(request))


def addtemplate(request):
    c = {}
    form = c['form'] = forms.AddTemplateForm()
    if request.POST:
        # TODO: Do interesting submit stuff
        pass
    return render_to_response('addtemplate.html', c, context_instance=RequestContext(request))


def scan_network(request):
    c = {}
    form = c['form'] = forms.ScanNetworkForm(initial={'network_address':'Just click submit'})
    
    if request.POST:
        form = c['form'] = forms.ScanNetworkForm(initial=request.POST)
        c['scan_results'] = True
    return render_to_response('scan_network.html', c, context_instance=RequestContext(request))