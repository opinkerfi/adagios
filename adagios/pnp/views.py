# -*- coding: utf-8 -*-
#
# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2010, Pall Sigurdsson <palli@opensource.is>
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

from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse
from adagios.pnp.functions import run_pnp
from adagios.views import adagios_decorator
import json


@adagios_decorator
def pnp(request, pnp_command='image'):
    c = {}
    c['messages'] = []
    c['errors'] = []
    result = run_pnp(pnp_command, **request.GET)
    content_type = "text"
    if pnp_command == 'image':
        content_type = "image/png"
    elif pnp_command == 'json':
        content_type = "application/json"
    return HttpResponse(result, content_type=content_type)
