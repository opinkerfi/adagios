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
from django.test import LiveServerTestCase
import adagios.status
import adagios.status.utils
import adagios.status.graphite
import adagios.settings
import adagios.utils
import simplejson as json
import adagios.seleniumtests
from mock import patch
import adagios.status.rest

try:
    from selenium.webdriver.common.by import By
except ImportError:
    pass


class LiveStatusTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.nagios_config = adagios.settings.nagios_config
        cls.environment = adagios.utils.get_test_environment()
        cls.environment.start()

        cls.livestatus = cls.environment.get_livestatus()

        cls.factory = RequestFactory()

    @classmethod
    def tearDownClass(cls):
        cls.environment.terminate()

    def testLivestatusConnectivity(self):
        requests = self.livestatus.query('GET status', 'Columns: requests')
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

    def test_status_detail(self):
        """ Tests for /status/detail """
        tmp = self.loadPage('/status/detail?contact_name=nagiosadmin')
        self.assertTrue('nagiosadmin belongs to the following' in tmp.content)

        tmp = self.loadPage('/status/detail?host_name=ok_host')
        self.assertTrue('ok_host' in tmp.content)

        tmp = self.loadPage('/status/detail?host_name=ok_host&service_description=ok%20service%201')
        self.assertTrue('ok_host' in tmp.content)

        tmp = self.loadPage('/status/detail?contactgroup_name=admins')
        self.assertTrue('nagiosadmin' in tmp.content)


    def testStateHistory(self):
        request = self.factory.get('/status/state_history')
        adagios.status.views.state_history(request)

    def loadPage(self, url, expected_status_code=200):
        """ Load one specific page, and assert if return code is not 200 """
        c = Client()
        response = c.get(url)
        self.assertEqual(response.status_code, expected_status_code, _("Expected status code %(code)s for page %(url)s") % {'code': expected_status_code, 'url': url})
        return response

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

    def test_rest_top_alert_producers(self):
        """ Test adagios.rest.status.top_alert_producers
        """
        c = Client()
        data = {}
        data['limit'] = '1'
        response = c.post('/rest/status/json/top_alert_producers', data=data)
        self.assertEqual(200, response.status_code)

        json_reply = json.loads(response.content)
        self.assertFalse(len(json_reply) > 1, "Too many objects returned" \
                         " limit is 1, json:\n" + str(json_reply))

class Graphite(unittest.TestCase):
    def test__get_graphite_url(self):
        """ Smoketest for  adagios.status.graphite._get_graphite_url() """
        base = "http://localhost/graphite"
        host = "localhost"
        service = "Ping"
        metric = "packetloss"
        from_ = "-1d"
        parameters = locals()
        parameters.pop('self', None)
        result = adagios.status.graphite._get_graphite_url(**parameters)
        self.assertTrue(result.startswith(base))
        self.assertTrue(host in result)
        self.assertTrue(service in result)
        self.assertTrue(metric in result)

    def test_get(self):
        """ Smoketest for adagios.status.graphite.get() """
        base = "http://localhost/graphite"
        host = "localhost"
        service = "Ping"
        metrics = ["packetloss", "rta"]
        units = [("test", "test", "-1d")]
        parameters = locals()
        parameters.pop('self', None)
        result = adagios.status.graphite.get(**parameters)
        self.assertTrue(result)
        self.assertTrue(len(result) == 1)
        self.assertTrue('rta' in result[0]['metrics'])
        self.assertTrue('packetloss' in result[0]['metrics'])


class UtilsTest(unittest.TestCase):
    """Tests for adagios.status.utils"""
    def setUp(self):
        self.host_query = pynag.Parsers.LivestatusQuery('GET hosts')
        self.service_query = pynag.Parsers.LivestatusQuery('GET services')

    def test_search_multiple_attributes_multiple_attributes(self):
        attributes = ['host_name', 'address']
        adagios.status.utils._search_multiple_attributes(self.host_query, attributes, 'test')
        expected_query = 'GET hosts\nFilter: host_name = test\nFilter: address = test\nOr: 2\n\n'
        self.assertEqual(expected_query, self.host_query.get_query())

    def test_search_multiple_attributes_one_attribute(self):
        attributes = ['host_name']
        adagios.status.utils._search_multiple_attributes(self.host_query, attributes, 'test')
        expected_query = 'GET hosts\nFilter: host_name = test\n\n'
        self.assertEqual(expected_query, self.host_query.get_query())

    def test_search_multiple_attributes_empty(self):
        adagios.status.utils._search_multiple_attributes(self.host_query, [], 'test')
        expected_query = 'GET hosts\n\n'
        self.assertEqual(expected_query, self.host_query.get_query())

    def test__process_querystring_for_host_empty(self):
        query = adagios.status.utils._process_querystring_for_host()
        self.assertEqual(self.host_query, query)

    def test__process_querystring_for_host_one_kwarg(self):
        query = adagios.status.utils._process_querystring_for_host(state="1")
        self.host_query.add_filter('state', '1')
        self.assertEqual(self.host_query, query)

    def test__process_querystring_for_host_two_kwargs(self):
        query = adagios.status.utils._process_querystring_for_host(state="1", host_name="localhost")
        self.host_query.add_filters(state=1, host_name="localhost")
        self.assertEqual(self.host_query, query)

    def test__process_querystring_for_host_generic_search(self):
        search = "test"
        query = adagios.status.utils._process_querystring_for_host(q=search)
        self.host_query.add_filter('name__contains', search)
        self.host_query.add_filter('address__contains', search)
        self.host_query.add_filter('plugin_output__contains', search)
        self.host_query.add_filter('alias__contains', search)
        self.host_query.add_or_statement(4)
        self.assertEqual(self.host_query, query)

    def test__process_querystring_for_host_unhandled(self):
        query = adagios.status.utils._process_querystring_for_host(unhandled=True)
        self.host_query.add_filter('scheduled_downtime_depth', 0)
        self.host_query.add_filter('state', 1)
        self.host_query.add_filter('acknowledged', 0)
        self.assertEqual(self.host_query, query)

    def test__process_querystring_for_host_downtime_on(self):
        query = adagios.status.utils._process_querystring_for_host(in_scheduled_downtime="1")
        self.host_query.add_filter('scheduled_downtime_depth__gt', 0)
        self.assertEqual(self.host_query, query)

    def test__process_querystring_for_host_downtime_off(self):
        query = adagios.status.utils._process_querystring_for_host(in_scheduled_downtime="0")
        self.host_query.add_filter('scheduled_downtime_depth', 0)
        self.assertEqual(self.host_query, query)

    def test__process_querystring_for_service_empty(self):
        query = adagios.status.utils._process_querystring_for_service()
        self.assertEqual(self.service_query, query)

    def test__process_querystring_for_service_one_kwarg(self):
        query = adagios.status.utils._process_querystring_for_service(state="1")
        self.service_query.add_filter('state', '1')
        self.assertEqual(self.service_query, query)

    def test__process_querystring_for_service_two_kwargs(self):
        query = adagios.status.utils._process_querystring_for_service(state="1", description="localservice")
        self.service_query.add_filters(state=1, description="localservice")
        self.assertEqual(self.service_query, query)

    def test__process_querystring_for_service_generic_search(self):
        search = "test"
        query = adagios.status.utils._process_querystring_for_service(q=search)
        self.service_query.add_filter('host_name__contains', search)
        self.service_query.add_filter('description__contains', search)
        self.service_query.add_filter('plugin_output__contains', search)
        self.service_query.add_filter('host_address__contains', search)
        self.service_query.add_or_statement(4)
        self.assertEqual(self.service_query, query)

    def test__process_querystring_for_service_unhandled(self):
        query = adagios.status.utils._process_querystring_for_service(unhandled=True)
        self.service_query.add_filter('host_scheduled_downtime_depth', 0)
        self.service_query.add_filter('host_state', 0)
        self.service_query.add_filter('scheduled_downtime_depth', 0)
        self.service_query.add_filter('acknowledged', 0)
        self.service_query.add_filter('state__isnot', 0)
        self.service_query.add_filter('host_acknowledged', 0)
        self.assertEqual(self.service_query, query)

    def test__process_querystring_for_service_downtime_on(self):
        query = adagios.status.utils._process_querystring_for_service(in_scheduled_downtime="1")
        self.service_query.add_filter('scheduled_downtime_depth__gt', 0)
        self.assertEqual(self.service_query, query)

    def test__process_querystring_for_service_downtime_off(self):
        query = adagios.status.utils._process_querystring_for_service(in_scheduled_downtime="0")
        self.service_query.add_filter('scheduled_downtime_depth', 0)
        self.assertEqual(self.service_query, query)


class SeleniumStatusTestCase(adagios.seleniumtests.SeleniumTestCase):
    def test_network_parents(self):
        """Status Overview, Network Parents should show an integer"""
        for driver in self.drivers:
            driver.get(self.live_server_url + "/status")

            # Second link is Network Parents in overview
            self.assertEqual(driver.find_elements(By.XPATH,
                "//a[@href='/status/parents']")[1].text.isdigit(), True)

    def test_services_select_all(self):
        """Loads services list and tries to select everything

        Flow:
            Load http://<url>/status/services
            Click select all
            Look for statustable rows
            Assert that all rows are checked"""

        for driver in self.drivers:
            driver.get(self.live_server_url + "/status/services")

            driver.find_element_by_xpath("//input[@class='select_many']").click()
            driver.find_element_by_xpath("//a[@class='select_all']").click()

            # Get all statustable rows
            status_table_rows = driver.find_element_by_xpath(
                "//table[contains(@class, 'statustable')]"
            ).find_elements(By.XPATH, "//tbody/tr[contains(@class, 'mainrow')]")

            # Sub-select non-selected
            for row in status_table_rows:
                self.assertTrue('row_selected' in row.get_attribute('class'),
                                "Non selected row found after selecting all: " + \
                                row.text)

    def test_status_overview_top_alert_producers(self):
        """Check the top alert producers part of status overview"""
        for driver in self.drivers:
            driver.get(self.live_server_url + "/status")

            top_alert_table_rows = driver.find_elements(By.XPATH,
                "//table[@id='top_alert_producers']/tbody/tr"
            )

            count = 0
            for row in top_alert_table_rows:
                if 'display' not in row.get_attribute('style'):
                    count += 1

            self.assertTrue(count <= 3, "Top alert producers returns too many rows")

class RestTests(unittest.TestCase):
    def test_reschedule_raises_on_float_string_check_time(self):
        """reschedule should raise on string float"""
        self.assertRaises(ValueError, adagios.status.rest.reschedule,
                          request={},
                          host_name='localhost',
                          check_time='1.1')

    @patch('pynag.Control.Command.schedule_forced_host_check')
    def test_reschedule_calls_host_check_with_int_check_time(self,
                                                             mock_host_check):
        """reschedule converts to int before calling schedule_forced_host_check
        """
        mock_host_check.return_value = None
        adagios.status.rest.reschedule(request={},
                                       host_name='localhost',
                                       check_time=1.1)
        mock_host_check.assert_called_once_with(host_name='localhost',
                                                check_time=1)

    @patch('time.time')
    @patch('pynag.Control.Command.schedule_forced_host_check')
    def test_reschedule_uses_current_time_with_no_check_time(
            self, mock_host_check, mock_time):
        """reschedule uses current time as int when no check_time specified"""
        mock_host_check.return_value = None
        mock_time.return_value = 7357.7357
        adagios.status.rest.reschedule(request={},
                                       host_name='localhost')
        mock_host_check.assert_called_once_with(host_name='localhost',
                                                check_time=7357)

    @patch('time.time')
    @patch('pynag.Control.Command.schedule_forced_host_check')
    def test_reschedule_calls_host_check_with_current_time_when_empty_string(
            self,
            mock_host_check,
            mock_time):
        """reschedule called with empty string sets check_time to current"""
        mock_host_check.return_value = None
        mock_time.return_value = 7357.7357
        adagios.status.rest.reschedule(request={},
                                       host_name='localhost',
                                       check_time='')
        mock_host_check.assert_called_once_with(host_name='localhost',
                                                check_time=7357)
