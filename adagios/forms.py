# -*- coding: utf-8 -*-
from django.utils.encoding import smart_str
from django import forms

class AdagiosForm(forms.Form):
    """ Base class for all forms in this module. Forms that use pynag in any way should inherit from this one.
    """
    def clean(self):
        cleaned_data = super(forms.Form, self).clean()
        for k,v in cleaned_data.items():
            if isinstance(v, (str,unicode)):
                cleaned_data[k] = smart_str(v)
        return cleaned_data
