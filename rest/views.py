# Create your views here.
from django.shortcuts import render_to_response, redirect
from django.core import serializers
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson

my_module = None

def _load(module_name):
    #global my_module
    #if not my_module:
    my_module = __import__(module_name, fromlist=[''])
    return my_module
    
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
        item = okconfig.__dict__[attribute]
        item_type = str(type(item))
        if item_type != "<type 'function'>":
            result = okconfig.__dict__[attribute]
        else:
            arguments = request.POST
            result = item( **arguments )
    else:
        raise BaseException("Unsupported operation: %s" % (request.method))
    if format == 'json':
        import json
        result = json.dumps( result )
    else:
        result = str(result)
    return HttpResponse(result, mimetype='application/javascript')

def index( request, module_name ):
    m = _load(module_name)
    gets,puts = [],[]
    for k,v in m.__dict__.items():
        if k.startswith('_'): continue
        if k == '': continue
        item_type = str(type(v))
        #description = "%-30s\t%s\n" % (k, str(type(v)))
        if item_type == "<type 'function'>":
            puts.append( k )
        else:
            gets.append( k )
    c = {}
    c['module_name'] = module_name
    c['gets'] = gets
    c['puts'] = puts
    c['module_documenation'] = m.__doc__
    print m.__doc__
    return render_to_response('rest/index.html', c)