from django.http import HttpResponse
import traceback
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, loader
from django import template
import time
import logging
import adagios.settings
import adagios.utils
from adagios.exceptions import AccessDenied

def adagios_decorator(view_func):
    """ This is a python decorator intented for all views in the status module.

     It catches all unhandled exceptions and displays them on a generic web page.

     Kind of what the django exception page does when debug mode is on.
    """
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        try:
            if request.method == 'POST':
                adagios.utils.update_eventhandlers(request)
            result = view_func(request, *args, **kwargs)
            end_time = time.time()
            time_now = time.ctime()
            duration = end_time - start_time
            return result
        except Exception, e:
            c = {}
            c['exception'] = str(e)
            c['exception_type'] = str(type(e).__name__)
            c['traceback'] = traceback.format_exc()
            return error_page(request, context=c)
    wrapper.__name__ = view_func.__name__
    wrapper.__module__ = view_func.__module__
    return wrapper


def require_administrator(view_func):
    """ python decorator that raises exception if user is not administrator """
    def wrapper(request, *args, **kwargs):
        try:
            adagios.utils.require_administrator(request)
            return view_func(request, *args, **kwargs)
        except AccessDenied, e:
            return http_403(request)
    wrapper.__name__ = view_func.__name__
    wrapper.__module__ = view_func.__module__
    return wrapper


def error_page(request, context=None):
    if context is None:
        context = {}
        context['errors'] = []
        context['errors'].append('Error occured, but no error messages provided, what happened?')
    t = loader.get_template('status_error.html')

    c = template.Context(context)
    t = t.render(c)
    response = HttpResponse(t, content_type="text/html")
    response.status_code = 500
    return response

@require_administrator
def index(request):
    """ This view is our frontpage """
    # If status view is enabled, redirect to frontpage of the status page:
    if adagios.settings.enable_status_view:
        return redirect('status_index', permanent=True)
    else:
        return redirect('objectbrowser', permanent=True)


def http_403(request):
    context = {}

    context['access_level'] = adagios.utils.get_access_level(request)
    context['username'] = request.META.get('REMOTE_USER', 'anonymous')

    t = loader.get_template('403.html')
    c = template.Context(context)
    t = t.render(c)
    response = HttpResponse(t, content_type="text/html")
    response.status_code = 403
    return response