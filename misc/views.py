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

#from django.core import serializers
#from django.http import HttpResponse, HttpResponseServerError
#from django.utils import simplejson
from django.core.context_processors import csrf
#from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
import forms

def index(request):
	c = {}
	return render_to_response('frontpage.html', c)

def contact_us( request ):
	''' Bring a small form that has a "contact us" form on it '''
	c={}
	c.update(csrf(request))
	if request.method == 'GET':
		form = forms.ContactUsForm(initial=request.GET)
	else:
		form = forms.ContactUsForm(data=request.POST)
		if form.is_valid():
			form.save()
			c['thank_you'] = True
			c['sender'] = form.cleaned_data['sender']
		
	c['form'] = form
	return render_to_response('contact_us.html', c)
		
	
