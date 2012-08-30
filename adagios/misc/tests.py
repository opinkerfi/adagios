"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.template import RequestContext
import forms
import django.forms

from django.test import TestCase

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)

__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


def test(request):
        c = { }
        f = forms.PerfDataForm(initial=request.GET)
        if request.method == 'POST':
            f = forms.PerfDataForm(data=request.POST)
            if f.is_valid():
                f.save()
                c['results'] = f.results
                for i in f.results:
                    if i.status == "ok":
                        i.csstag = "success"
                    elif i.status == "critical":
                        i.csstag = "danger"
                    elif i.status == "unknown":
                        i.csstag = 'info'
                    else:
                        i.csstag = i.status
        c['form'] = f
        return render_to_response('test.html', c, context_instance = RequestContext(request))

