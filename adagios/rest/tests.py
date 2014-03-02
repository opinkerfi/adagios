"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.utils import unittest
from django.test.client import Client
import json


class LiveStatusTestCase(unittest.TestCase):
    def testPageLoad(self):
        """ Smoke Test for various rest modules """
        self.loadPage('/rest')
        self.loadPage('/rest/status/')
        self.loadPage('/rest/pynag/')
        self.loadPage('/rest/adagios/')
        self.loadPage('/rest/status.js')
        self.loadPage('/rest/pynag.js')
        self.loadPage('/rest/adagios.js')

    def testDnsLookup(self):
        """ Test the DNS lookup rest call
        """
        path = "/rest/pynag/json/dnslookup"
        data = {'host_name': 'localhost'}
        try:
            c = Client()
            response = c.post(path=path, data=data)
            json_data = json.loads(response.content)
            self.assertEqual(response.status_code, 200, "Expected status code 200 for page %s" % path)
            self.assertEqual(True, 'addresslist' in json_data, "Expected 'addresslist' to appear in response")
        except KeyError, e:
            self.assertEqual(True, "Unhandled exception while loading %s: %s" % (path, e))


    def loadPage(self, url):
        """ Load one specific page, and assert if return code is not 200 """
        try:
            c = Client()
            response = c.get(url)
            self.assertEqual(response.status_code, 200, "Expected status code 200 for page %s" % url)
        except Exception, e:
            self.assertEqual(True, "Unhandled exception while loading %s: %s" % (url, e))