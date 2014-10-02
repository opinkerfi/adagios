# -*- coding: utf-8 -*-
#
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

from django.utils.encoding import smart_str
from django import forms

class AdagiosForm(forms.Form):
    """ Base class for all forms in this module. Forms that use pynag in any way should inherit from this one.
    """
    def clean(self):
        cleaned_data = {}
        tmp = super(AdagiosForm, self).clean()
        for k,v in tmp.items():
            if isinstance(k, (unicode)):
                k = smart_str(k)
            if isinstance(v, (unicode)):
                v = smart_str(v)
            cleaned_data[k] = v
        return cleaned_data
