# Create your views here.
from django.shortcuts import render_to_response, redirect
from django.core import serializers
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
#from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.template import RequestContext
from django.core.urlresolvers import resolve


import inspect
from django import forms
import os
my_module = None


def _load(module_path):
    #global my_module
    # if not my_module:
    my_module = __import__(module_path, None, None, [''])
    return my_module


@csrf_exempt
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
            if not request.GET.items():
                return render_to_response('function_form.html', c, context_instance=RequestContext(request))
            # Handle get parameters
            arguments = {}
            for k, v in request.GET.items():
                # TODO: Is it safe to turn all digits to int ?
                #if str(v).isdigit(): v = int(float(v))
                arguments[k.encode('utf-8')] = v.encode('utf-8')
            result = item(**arguments)
    elif request.method == 'POST':
        item = members[attribute]
        if not inspect.isfunction(item):
            result = item
        else:
            arguments = {}  # request.POST.items()
            for k, v in request.POST.items():
                arguments[k.encode('utf-8')] = v.encode('utf-8')
            result = item(**arguments)
    else:
        raise BaseException("Unsupported operation: %s" % (request.method))
    # Everything below is just about formatting the results
    if format == 'json':
        result = simplejson.dumps(
            result, ensure_ascii=False, sort_keys=True, skipkeys=True, indent=4)
        mimetype = 'application/javascript'
    elif format == 'xml':
            # TODO: For some reason Ubuntu does not have this module. Where is
            # it? Should we use lxml instead ?
        import xml.marshal.generic
        result = xml.marshal.generic.dumps(result)
        mimetype = 'application/xml'
    elif format == 'txt':
        result = str(result)
        mimetype = 'text/plain'
    else:
        raise BaseException(
            "Unsupported format: '%s'. Valid formats: json xml txt" %
            format)
    return HttpResponse(result, mimetype=mimetype)


def index(request, module_name, module_path):
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

    return render_to_response('javascript.html', c, mimetype="text/javascript", context_instance=RequestContext(request))


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
