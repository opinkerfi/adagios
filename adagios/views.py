import traceback
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
import time
import logging


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
    return render_to_response('status_error.html', context, context_instance=RequestContext(request))
