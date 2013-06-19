# -*- coding: utf-8 -*-
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
