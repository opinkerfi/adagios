# -*- coding: utf-8 -*-
#
# Copyright 2014, Pall Sigurdsson <palli@opensource.is>
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


from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse
import adagios.settings
import adagios.status.utils
import os

from adagios.views import adagios_decorator, error_page
from django.template import RequestContext
from adagios.contrib import get_template_name
from django import template
from django.utils.translation import ugettext as _


@adagios_decorator
def index(request, contrib_dir=None):
    """ List all available user contributed views in adagios.settings.contrib_dir """
    messages = []
    errors = []

    if not contrib_dir:
        contrib_dir = adagios.settings.contrib_dir
    views = os.listdir(contrib_dir)

    if not views:
        errors.append("Directory '%s' is empty" % contrib_dir)
    return render_to_response("contrib_index.html", locals(), context_instance=RequestContext(request))


@adagios_decorator
def contrib(request, arg1, arg2=None, arg3=None, arg4=None):
    messages = []
    errors = []

    full_path = get_template_name(adagios.settings.contrib_dir, arg1, arg2, arg3, arg4)
    if os.path.isdir(full_path):
        return index(request, contrib_dir=full_path)

    with open(full_path) as f:
        content = f.read()

    # Lets populate local namespace with convenient data
    services = lambda: locals().get('services', adagios.status.utils.get_services(request))
    hosts = lambda: locals().get('hosts', adagios.status.utils.get_hosts(request))
    service_problems = lambda: locals().get('service_problems', adagios.status.utils.get_hosts(request, state__isnot='0'))
    host_problems = lambda: locals().get('host_problems', adagios.status.utils.get_hosts(request, state__isnot='0'))
    statistics = lambda: locals().get('statistics', adagios.status.utils.get_statistics(request))

    t = template.Template(content)
    c = template.Context(locals())
    html = t.render(c)
    return HttpResponse(html)
