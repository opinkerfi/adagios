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

from django.http import HttpResponse
import traceback
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, loader
from django import template
from django.utils.translation import ugettext as _
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


def error_page(request, context=None):
    if context is None:
        context = {}
        context['errors'] = []
        context['errors'].append('Error occured, but no error messages provided, what happened?')
    if request.META.get('CONTENT_TYPE') == 'application/json':
        context.pop('request', None)
        content = str(context)
        response = HttpResponse(content=content, content_type='application/json')
    else:
        response = render_to_response('status_error.html', context, context_instance=RequestContext(request))
    response.status_code = 500
    return response


def index(request):
    """ This view is our frontpage """
    # If status view is enabled, redirect to frontpage of the status page:
    if adagios.settings.enable_status_view:
        return redirect('adagios.status.views.status_index', permanent=True)
    else:
        return redirect('objectbrowser', permanent=True)


def http_403(request, exception=None):
    context = {}
    context['exception'] = exception
    if request.META.get('CONTENT_TYPE') == 'application/json':
        c = {}
        c['exception_type'] = exception.__class__
        c['message'] = str(exception.message)
        c['access_required'] = exception.access_required
        response = HttpResponse(content=str(c), content_type='application/json')
    else:
        response = render_to_response('403.html', context, context_instance=RequestContext(request))
    response.status_code = 403
    return response
