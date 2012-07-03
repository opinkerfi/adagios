"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.core.context_processors import csrf
from django.shortcuts import render_to_response
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
        from pynag import Model
        services = Model.Service.objects.filter(host_name='argon.ok.is',service_description__contains='')
        c['hostname'] = 'argon.ok.is'
        c.update(csrf(request))
        if request.method == 'POST':
            for k,v in request.POST.items():
                if k.count('::') < 2: continue
                host_name,service_description,attribute = k.split('::',2)
                for i in services:
                    if i['service_description'] == service_description:
                        if i[attribute] != v:
                            i[attribute] = v
                            i.save()
        myforms =[]       
        for service in services:
            initial = {}
            initial['service_description'] = service['service_description']
            initial['register'] = service['register'] == "1"
            form = forms.OkconfigEditTemplateForm(initial= initial)
            form.s = service['service_description']
            form.command_line = service.get_effective_command_line()
            for k in service.keys():
                if k.startswith('_'):
                    fieldname="%s::%s::%s" % ( service['host_name'], service['service_description'], k)
                    form.fields[fieldname] = django.forms.CharField(initial=service[k], label=k)
            myforms.append( form )
        c['forms'] = myforms
        return render_to_response('test.html', c)

