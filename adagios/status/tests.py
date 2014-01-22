# -*- coding: utf-8 -*-

from django.utils import unittest
from django.test.client import Client

import pynag.Parsers
import os


class LiveStatusTestCase(unittest.TestCase):

    def setUp(self):
        from adagios.settings import nagios_config
        self.nagios_config = nagios_config

    def testLivestatusConnectivity(self):
        livestatus = pynag.Parsers.mk_livestatus(
            nagios_cfg_file=self.nagios_config)
        requests = livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(
            1, len(requests), "Could not get status.requests from livestatus")

    def testLivestatusConfigured(self):
        config = pynag.Parsers.config(cfg_file=self.nagios_config)
        config.parse_maincfg()
        for k, v in config.maincfg_values:
            if k == "broker_module" and v.find('livestatus') > 1:
                tmp = v.split()
                self.assertFalse(
                    len(tmp) < 2, ' We think livestatus is incorrectly configured. In nagios.cfg it looks like this: %s' % v)
                module_file = tmp[0]
                socket_file = tmp[1]
                self.assertTrue(
                    os.path.exists(module_file), ' Livestatus Broker module not found at "%s". Is nagios correctly configured?' % module_file)
                self.assertTrue(
                    os.path.exists(socket_file), ' Livestatus socket file was not found (%s). Make sure nagios is running and that livestatus module is loaded' % socket_file)
                return
        self.assertTrue(
            False, 'Nagios Broker module not found. Is livestatus installed and configured?')

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
        self.loadPage('/misc/map')
        self.loadPage('/status/dashboard')

    def loadPage(self, url):
        """ Load one specific page, and assert if return code is not 200 """
        try:
            c = Client()
            response = c.get(url)
            self.assertEqual(response.status_code, 200, "Expected status code 200 for page %s" % url)
        except Exception, e:
            self.assertEqual(True, "Unhandled exception while loading %s: %s" % (url, e))

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
