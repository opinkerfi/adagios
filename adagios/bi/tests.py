"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client

from adagios.bi import *


class TestGraphs(TestCase):

    def testPNP4NagiosGraph_get_image_url(self):

        pnp = PNP4NagiosGraph('apc01.acme.com', 'Ping', 'rta')
        # pnp.get_image_url()


class TestBusinessProcess(TestCase):

    def test_save_and_load(self):
        """ This test will test load/save of a business process.

         The procedure is as follows:
         * Load a business process
         * Save it
         * Make changes
         * Load it again, and verify changes were saved.
        """
        bp_name = 'test_business_process'

        b = BusinessProcess(bp_name)
        b.load()

        # Append a dot to the bp name and save
        new_display_name = b.display_name or '' + "."
        b.display_name = new_display_name
        b.save()

        # Load bp again
        b = BusinessProcess(bp_name)
        b.load()

        self.assertEqual(b.display_name, new_display_name)

    def test_add_process(self):
        """ Test adding new processes to a current BP
        """
        bp_name = 'test'
        sub_process_name = 'sub_process'
        sub_process_display_name = 'This is a subprocess of test'
        b = BusinessProcess(bp_name)
        b.add_process(sub_process_name, display_name=sub_process_display_name)
        for i in b.get_processes():
            if i.name == sub_process_name and i.display_name == sub_process_display_name:
                return
        else:
            self.assertTrue(
                False, 'We tried adding a business process but could not find it afterwards')

    def test_hostgroup_bp(self):
        bp_name = 'test'
        hostgroup_name = 'acme-network'
        b = BusinessProcess(bp_name)
        b.add_process(hostgroup_name, 'hostgroup')

    def test_remove_process(self):
        """ Test removing a subprocess from a businessprocess
        """
        bp_name = 'test'
        sub_process_name = 'sub_process'
        sub_process_display_name = 'This is a subprocess of test'
        b = BusinessProcess(bp_name)
        b.add_process(sub_process_name, display_name=sub_process_display_name)
        self.assertNotEqual([], b.processes)
        b.remove_process(sub_process_name)
        self.assertEqual([], b.processes)

    def test_get_all_processes(self):
        get_all_processes()

    def test_macros(self):
        bp = get_business_process('uniq test case', status_method="use_worst_state")

        macros_for_empty_process = {
            'num_problems': 0,
            'num_state_0': 0,
            'num_state_1': 0,
            'num_state_2': 0,
            'num_state_3': 0,
            'current_state': 3,
            'friendly_state': 'unknown',
            'percent_problems': 0,
            'percent_state_3': 0,
            'percent_state_2': 0,
            'percent_state_1': 0,
            'percent_state_0': 0
        }
        self.assertEqual(3, bp.get_status())
        self.assertEqual(macros_for_empty_process, bp.resolve_all_macros())

        bp.add_process("always_ok", status_method="always_ok")
        bp.add_process("always_major", status_method="always_major")

        macros_for_nonempty_process = {
            'num_problems': 1,
            'num_state_0': 1,
            'num_state_1': 0,
            'num_state_2': 1,
            'num_state_3': 0,
            'current_state': 2,
            'friendly_state': 'major problems',
            'percent_problems': 50.0,
            'percent_state_3': 0.0,
            'percent_state_2': 50.0,
            'percent_state_1': 0.0,
            'percent_state_0': 50.0
        }
        self.assertEqual(2, bp.get_status())
        self.assertEqual(macros_for_nonempty_process, bp.resolve_all_macros())

    def testPageLoad(self):
        self.loadPage('/bi')
        self.loadPage('/bi/add')
        self.loadPage('/bi/add/subprocess')
        self.loadPage('/bi/add/graph')

    def loadPage(self, url):
        """ Load one specific page, and assert if return code is not 200 """
        try:
            c = Client()
            response = c.get(url)
            self.assertEqual(response.status_code, 200, "Expected status code 200 for page %s" % url)
        except Exception, e:
            self.assertEqual(True, "Unhandled exception while loading %s: %s" % (url, e))