# -*- coding: utf-8 -*-
#
# Copyright 2010, Pall Sigurdsson <palli@opensource.is>
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
from adagios.pnp.functions import run_pnp
import json


def pnp(request, pnp_command='image'):
    c = {}
    c['messages'] = []
    c['errors'] = []
    result = run_pnp(pnp_command, **request.GET)
    mimetype = "text"
    if pnp_command == 'image':
        mimetype = "image/png"
    elif pnp_command == 'json':
        mimetype = "application/json"
    return HttpResponse(result, mimetype)
