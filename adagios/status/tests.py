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

from django.utils import unittest
from django.test.client import Client
from django.utils.translation import ugettext as _

import pynag.Parsers
import os
from django.test.client import RequestFactory
import adagios.status
import adagios.status.utils

class LiveStatusTestCase(unittest.TestCase):

    def setUp(self):
        from adagios.settings import nagios_config
        self.nagios_config = nagios_config
        self.factory = RequestFactory()

    def testLivestatusConnectivity(self):
        livestatus = adagios.status.utils.livestatus(request=None)
        requests = livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(
            1, len(requests), _("Could not get status.requests from livestatus"))

    def testLivestatusConfigured(self):
        config = pynag.Parsers.config(cfg_file=self.nagios_config)
        config.parse_maincfg()
        for k, v in config.maincfg_values:
            if k == "broker_module" and v.find('livestatus') > 1:
                tmp = v.split()
                self.assertFalse(
                    len(tmp) < 2, _(' We think livestatus is incorrectly configured. In nagios.cfg it looks like this: %s') % v)
                module_file = tmp[0]
                socket_file = tmp[1]
                self.assertTrue(
                    os.path.exists(module_file), _(' Livestatus Broker module not found at "%s". Is nagios correctly configured?') % module_file)
                self.assertTrue(
                    os.path.exists(socket_file), _(' Livestatus socket file was not found (%s). Make sure nagios is running and that livestatus module is loaded') % socket_file)
                return
        self.assertTrue(
            False, _('Nagios Broker module not found. Is livestatus installed and configured?'))

    def testPageLoad(self):
        """ Loads a bunch of status pages, looking for a crash """
        self.loadPage('/status/')
        self.loadPage('/status/hosts')
        self.loadPage('/status/services')
        self.loadPage('/status/contacts')
        self.loadPage('/status/parents')
        self.loadPage('/status/state_history')
        self.loadPage('/status/log')
        self.loadPage('/status/comments')
        self.loadPage('/status/downtimes')
        self.loadPage('/status/hostgroups')
        self.loadPage('/status/servicegroups')
        self.loadPage('/status/map')
        self.loadPage('/status/dashboard')

    def testStateHistory(self):
        request = self.factory.get('/status/state_history')
        adagios.status.views.state_history(request)

    def loadPage(self, url):
        """ Load one specific page, and assert if return code is not 200 """
        try:
            c = Client()
            response = c.get(url)
            self.assertEqual(response.status_code, 200, _("Expected status code 200 for page %s") % url)
        except Exception, e:
            self.assertEqual(True, _("Unhandled exception while loading %(url)s: %(e)s") % {'url': url, 'e': e})

    def testSubmitCommand(self):
        """ Test adagios.rest.status.submit_check_results
        """
        c = Client()
        data = {}
        data['host_name'] = 'adagios test host'
        data['service_description'] = 'nonexistant'
        data['status_code'] = "0"
        data['plugin_output'] = 'test message'
        data['performance_data'] = ''
        response = c.post('/rest/status/json/submit_check_result', data=data)
        self.assertEqual(200, response.status_code)
