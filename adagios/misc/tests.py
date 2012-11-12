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


def test_old(request):
        c = { }
        c['messages'] = []
        f = forms.PerfDataForm(initial=request.GET)
        from pynag import Parsers
        s = Parsers.status()
        s.parse()
        c['objects'] = s.data['servicestatus']
        host_name=request.GET.get('host_name')
        service_description=request.GET.get('service_description')
        if host_name and service_description:
            for i in c['objects']:
                if i.get('host_name') == host_name and i.get('service_description') == service_description:
                    if i.get('current_state') == "0":
                        i['status'] = "success"
                    elif i.get('current_state') == "1":
                        i['status'] = "warning"
                    elif i.get('current_state') == "2":
                        i['status'] = "danger"
                    else:
                        i['status'] = "info"
                    c['object'] = i
                    from pynag import Model
                    perfdata = i.get('performance_data', 'a=1')
                    perfdata = Model.PerfData(perfdata)
                    c['results'] = results = perfdata.metrics

                    for i in results:
                        if i.status == "ok":
                            i.csstag = "success"
                        elif i.status == "critical":
                            i.csstag = "danger"
                        elif i.status == "unknown":
                            i.csstag = 'info'
                        else:
                            i.csstag = i.status

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

def test_old_as_hell(request):
    c = {}
    c['messages'] = []

    from pynag import Parsers
    s = Parsers.status()
    s.parse()
    c['hosts'] = hosts = s.data['hoststatus']
    c['services'] = services = s.data['servicestatus']
    for host in hosts:
        host['services'] = []
        host['status'] = state[host['current_state']]
        for service in services:
            if service['host_name'] == host['host_name']:
                service['status'] = state[service['current_state']]
                host['services'].append( service)
    return render_to_response('status.html', c, context_instance = RequestContext(request))


def test(request):
    c = {}
    c['messages'] = []
    return render_to_response('test.html', c, context_instance = RequestContext(request))