from django.http import HttpResponse
import traceback
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, loader
from django import template
import time
import logging
import adagios.settings

def error_handler(fn):
    """ This is a python decorator intented for all views in the status module.

     It catches all unhandled exceptions and displays them on a generic web page.

     Kind of what the django exception page does when debug mode is on.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = fn(*args, **kwargs)
            end_time = time.time()
            time_now = time.ctime()
            duration = end_time - start_time
            try:
                with open('/var/log/adagios.log', 'a') as f:
                    message = "%s %s.%s %s seconds\n" % (time_now, fn.__module__, fn.__name__, duration)
                    f.write(message)
            except IOError:
                pass
            return result
        except Exception, e:
            c = {}
            c['exception'] = e
            c['exception_type'] = str(type(e).__name__)
            c['traceback'] = traceback.format_exc()
            return error_page(*args, context=c)
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


def index(request):
    """ This view is our frontpage """
    # If status view is enabled, redirect to frontpage of the status page:
    if adagios.settings.enable_status_view:
        return redirect('status_index', permanent=True)
    else:
        return redirect('objectbrowser', permanent=True)