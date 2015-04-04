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

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.utils import unittest
from django.test.client import Client
from django.utils.translation import ugettext as _
import json

import adagios.utils


class LiveStatusTestCase(unittest.TestCase):

    def setUp(self):
        self.environment = adagios.utils.get_test_environment()
        self.environment.start()
        self.addCleanup(self.environment.terminate)

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
            self.assertEqual(response.status_code, 200, _("Expected status code 200 for page %s") % path)
            self.assertEqual(True, 'addresslist' in json_data, _("Expected 'addresslist' to appear in response"))
        except KeyError, e:
            self.assertEqual(True, _("Unhandled exception while loading %(path)s: %(exc)s") % {'path': path, 'exc': e})

    def testGetAllHostsViaJSON(self):
        """Test fetching hosts via json"""
        path = "/rest/status/json/hosts"
        data = {'fields': 'host_name'}
        c = Client()
        response = c.post(path=path, data=data)
        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 200, _("Expected status code 200 for page %s") % path)
        self.assertEqual(['ok_host'], [x['name'] for x in json_data])
        self.assertEqual(['name', 'backend'], json_data[0].keys())

    def loadPage(self, url):
        """ Load one specific page, and assert if return code is not 200 """
        try:
            c = Client()
            response = c.get(url)
            self.assertEqual(response.status_code, 200, _("Expected status code 200 for page %s") % url)
        except Exception, e:
            self.assertEqual(True, _("Unhandled exception while loading %(url)s: %(exc)s") % {'url': url, 'exc': e})
