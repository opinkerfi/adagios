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
        from pynag import Model
        s = Model.Service.objects.all
        c['config'] = Model.config.errors
        return render_to_response('test.html', c, context_instance = RequestContext(request))

