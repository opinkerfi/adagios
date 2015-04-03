# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Pall Sigurdsson <palli@opensource.is>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Create your views here.
from django.shortcuts import render_to_response, redirect, render
from django.core import serializers
from django.http import HttpResponse, HttpResponseServerError
import json
#from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.template import RequestContext
from django.core.urlresolvers import resolve
from adagios.views import adagios_decorator

import inspect
from django import forms
import os
my_module = None
import adagios.rest.urls

def _load(module_path):
    #global my_module
    # if not my_module:
    my_module = __import__(module_path, None, None, [''])
    return my_module


@csrf_exempt
@adagios_decorator
def handle_request(request, module_name, module_path, attribute, format):
    m = _load(module_path)
    # TODO: Only allow function calls if method == POST
    members = {}
    for k, v in inspect.getmembers(m):
        members[k] = v
    item = members[attribute]
    docstring = inspect.getdoc(item)
    if request.method == 'GET':
        if format == 'help':
            result = inspect.getdoc(item)
        elif not inspect.isfunction(item):
            result = item
        else:
            arguments = request.GET
            c = {}
            c['function_name'] = attribute
            c['form'] = CallFunctionForm(function=item, initial=request.GET)
            c['docstring'] = docstring
            c['module_name'] = module_name
            if not request.GET.items():
                return render_to_response('function_form.html', c, context_instance=RequestContext(request))
            # Handle get parameters
            arguments = {}
            for k, v in request.GET.items():
                # TODO: Is it safe to turn all digits to int ?
                #if str(v).isdigit(): v = int(float(v))
                arguments[k.encode('utf-8')] = v.encode('utf-8')
            # Here is a special hack, if the method we are calling has an argument
            # called "request" we will not let the remote user ship it in.
            # instead we give it a django request object
            if 'request' in inspect.getargspec(item)[0]:
                arguments['request'] = request
            result = item(**arguments)
    elif request.method == 'POST':
        item = members[attribute]
        if not inspect.isfunction(item):
            result = item
        else:
            arguments = {}  # request.POST.items()
            for k, v in request.POST.items():
                arguments[k.encode('utf-8')] = v.encode('utf-8')
            # Here is a special hack, if the method we are calling has an argument
            # called "request" we will not let the remote user ship it in.
            # instead we give it a django request object
            if 'request' in inspect.getargspec(item)[0]:
                arguments['request'] = request
            result = item(**arguments)
    else:
        raise BaseException(_("Unsupported operation: %s") % (request.method, ))
    # Everything below is just about formatting the results
    if format == 'json':
        result = json.dumps(
            result, ensure_ascii=False, sort_keys=True, skipkeys=True, indent=4)
        content_type = 'application/javascript'
    elif format == 'xml':
            # TODO: For some reason Ubuntu does not have this module. Where is
            # it? Should we use lxml instead ?
        import xml.marshal.generic
        result = xml.marshal.generic.dumps(result)
        content_type = 'application/xml'
    elif format == 'txt':
        result = str(result)
        content_type = 'text/plain'
    else:
        raise BaseException(
            _("Unsupported format: '%s'. Valid formats: json xml txt") %
            format)
    return HttpResponse(result, content_type=content_type)


@adagios_decorator
def list_modules(request):
    """ List all available modules and their basic info

    """
    rest_modules = adagios.rest.urls.rest_modules
    return render_to_response('list_modules.html', locals(), context_instance=RequestContext(request))


@adagios_decorator
def index(request, module_name, module_path):
    """ This view is used to display the contents of a given python module
    """
    m = _load(module_path)
    gets, puts = [], []
    blacklist = ('argv', 'environ', 'exit', 'path', 'putenv', 'getenv', )
    for k, v in inspect.getmembers(m):
        if k.startswith('_'):
            continue
        if k in blacklist:
            continue
        if inspect.ismodule(v):
            continue
        elif inspect.isfunction(v):
            puts.append(k)
        else:
            gets.append(k)
    c = {}
    c['module_path'] = module_path
    c['gets'] = gets
    c['puts'] = puts
    c['module_documenation'] = inspect.getdoc(m)
    return render_to_response('index.html', c, context_instance=RequestContext(request))


def javascript(request, module_name, module_path):
    """ Create a javascript library that will wrap around module_path module """
    m = _load(module_path)
    variables, functions = [], []
    blacklist = ('argv', 'environ', 'exit', 'path', 'putenv', 'getenv', )
    members = {}
    for k, v in inspect.getmembers(m):
        if k.startswith('_'):
            continue
        if k in blacklist:
            continue
        if inspect.ismodule(v):
            continue
        if inspect.isfunction(v):
            functions.append(k)
            members[k] = v
        else:
            variables.append(k)
    c = {}
    c['module_path'] = module_path
    c['module_name'] = module_name
    c['gets'] = variables
    c['puts'] = functions
    c['module_documenation'] = inspect.getdoc(m)
    current_url = request.get_full_path()
    baseurl = current_url.replace('.js', '')
    # Find every function, prepare what is needed so template can
    for i in functions:
        argspec = inspect.getargspec(members[i])
        args, varargs, varkw, defaults = argspec
        docstring = inspect.getdoc(members[i])
        if defaults is None:
            defaults = []
        else:
            defaults = list(defaults)
            # Lets create argstring, for the javascript needed
        tmp = [] + args
        argstring = []
        for num, default in enumerate(reversed(defaults)):
            argstring.append('%s=%s' % (tmp.pop(), default))
        argstring.reverse()
        argstring = tmp + argstring
        members[i] = {}
        members[i]['args'] = args
        members[i]['argstring'] = ','.join(args)
        members[i]['varargs'] = varargs
        members[i]['varkw'] = varkw
        members[i]['defaults'] = defaults
        members[i]['docstring'] = docstring
        members[i]['url'] = baseurl + "/json/" + i
        args, varargs, varkw, defaults = argspec
    c['functions'] = members

    return render(request, 'javascript.html', c,
                  content_type="text/javascript",
                  context_instance=RequestContext(request))


class CallFunctionForm(forms.Form):

    def __init__(self, function, *args, **kwargs):
        super(CallFunctionForm, self).__init__(*args, **kwargs)
        # We will create a field for every function_paramater
        function_paramaters = {}
        # If any paramaters were past via querystring, lets generate fields for
        # them
        if kwargs.has_key('initial'):
            for k, v in kwargs['initial'].items():
                function_paramaters[k] = v
        # Generate fields which resemble our functions default arguments
        argspec = inspect.getargspec(function)
        args, varargs, varkw, defaults = argspec
        self.show_kwargs = varkw is not None
        # We treat the argument 'request' as special. Django request object is going to be
        # passed instead of whatever the user wanted
        if "request" in args:
            args.remove('request')
        if defaults is None:
            defaults = []
        else:
            defaults = list(defaults)
        for i in args:
            self.fields[i] = forms.CharField(label=i)
        for k, v in function_paramaters.items():
            self.fields[k] = forms.CharField(label=k, initial=v)
        while len(defaults) > 0:
            value = defaults.pop()
            field = args.pop()
            self.fields[field].initial = value
