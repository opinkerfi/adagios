# Create your views here.
from django.shortcuts import render_to_response, redirect
from django.core import serializers
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
#from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt

my_module = None

# TODO: rewrite to use inspect module instead of my_module.__dict__. That is the correct approach.


def _load(module_name):
    #global my_module
    #if not my_module:
    my_module = __import__(module_name, fromlist=[''])
    return my_module

@csrf_exempt   
def handle_request(request, module_name, attribute, format):
    m = _load(module_name)
    # TODO: Only allow function calls if method == POST
    if request.method == 'GET':
        item = m.__dict__[attribute]
        item_type = str(type(item))
        if format == 'help':
            result = item.__doc__
        elif item_type != "<type 'function'>":
            result = m.__dict__[attribute]
        else:
            arguments = request.GET
            result = item( **arguments )
    elif request.method == 'POST':
        item = m.__dict__[attribute]
        item_type = str(type(item))
        if item_type != "<type 'function'>":
            result = m.__dict__[attribute]
        else:
            arguments = {} #request.POST.items()
            for k, v in request.POST.items():
                print "%s = %s (%s)" % (k,v, type(v))
                arguments[k] = v
            result = item( **arguments )
    else:
        raise BaseException("Unsupported operation: %s" % (request.method))
    if format == 'json':
        import json 
        result = json.dumps( result, sort_keys=True, indent=4 )
        mimetype='application/javascript'
    elif format == 'xml':
            # TODO: For some reason Ubuntu does not have this module. Where is it? Should we use lxml instead ?
            import xml.marshal.generic
            result = xml.marshal.generic.dumps(result)
            mimetype='application/xml'
    elif format == 'txt':
        result = str(result)
        mimetype='text/plain'
    else:
        result = str(result)
        mimetype='text/plain'  
    return HttpResponse(result, mimetype=mimetype)
def index( request, module_name ):
    m = _load(module_name)
    gets,puts = [],[]
    for k,v in m.__dict__.items():
        if k.startswith('_'): continue
        if k == '': continue
        item_type = str(type(v))
        #description = "%-30s\t%s\n" % (k, str(type(v)))
        if item_type == "<type 'module'>":
            continue
        if item_type == "<type 'function'>":
            puts.append( k )
        else:
            gets.append( k )
    c = {}
    c['module_name'] = module_name
    c['gets'] = gets
    c['puts'] = puts
    c['module_documenation'] = m.__doc__
    return render_to_response('index.html', c)