# Create your views here.
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse
from django.shortcuts import RequestContext


def hello_world(request):
    """ This is an example view. """
    c = {}
    return render_to_response("myapp_helloworld.html", c, context_instance=RequestContext(request))

