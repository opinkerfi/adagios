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
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import tempfile
import os
import time




from django.test import TestCase
from django.test.client import Client
from django.utils.translation import ugettext as _

from adagios.bi import *
import adagios.utils


class TestBusinessProcess(TestCase):
    def setUp(self):
        fd, filename = tempfile.mkstemp()
        BusinessProcess._default_filename = filename

    def tearDown(self):
        os.remove(BusinessProcess._default_filename)

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
            self.assertEqual(response.status_code, 200, _("Expected status code 200 for page %s") % url)
        except Exception, e:
            self.assertEqual(True, "Unhandled exception while loading %s: %s" % (url, e))

    def test_delete(self):
        bp1 = BusinessProcess('bp1')
        bp1.save()

        bp2 = BusinessProcess('bp2')
        bp2.save()

        self.assertEqual(['bp1', 'bp2'], get_all_process_names())

    def test_delete_recursive(self):
        bp1 = BusinessProcess('bp1')
        bp2 = BusinessProcess('bp2')
        bp1.save()
        bp2.save()
        bp1.add_process('bp2', 'businessprocess')
        bp1.save()

        self.assertEqual(1, len(bp1.get_processes()))

        bp2.delete()
        bp1 = get_business_process('bp1')
        self.assertFalse(bp1.get_processes())


class TestBusinessProcessLogic(TestCase):
    """ This class responsible for testing business classes logic """
    def setUp(self):
        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

        self.environment.start()

        fd, filename = tempfile.mkstemp()
        BusinessProcess._default_filename = filename

    def tearDown(self):
        os.remove(BusinessProcess._default_filename)

    def testBestAndWorstState(self):
        s = BusinessProcess("example process")
        s.status_method = 'use_worst_state'
        self.assertEqual(3, s.get_status(), _("Empty bi process should have status unknown"))

        s.add_process(process_name="always_ok", process_type="businessprocess", status_method='always_ok')
        self.assertEqual(0, s.get_status(), _("BI process with one ok subitem, should have state OK"))

        s.add_process("fail subprocess", status_method="always_major")
        self.assertEqual(2, s.get_status(), _("BI process with one failed item should have a critical state"))

        s.status_method = 'use_best_state'
        self.assertEqual(0, s.get_status(), _("BI process using use_best_state should be returning OK"))

    def testBusinessRules(self):
        s = BusinessProcess("example process")
        self.assertEqual(3, s.get_status(), _("Empty bi process should have status unknown"))

        s.add_process(process_name="always_ok", process_type="businessprocess", status_method='always_ok')
        self.assertEqual(0, s.get_status(), _("BI process with one ok subitem, should have state OK"))

        s.add_process("untagged process", status_method="always_major")
        self.assertEqual(0, s.get_status(), _("BI subprocess that is untagged should yield an ok state"))

        s.add_process("not critical process", status_method="always_major", tags="not critical")
        self.assertEqual(1, s.get_status(), _("A Non critical subprocess should yield 'minor problem'"))

        s.add_process("critical process", status_method="always_major", tags="mission critical")
        self.assertEqual(2, s.get_status(), _("A critical process in failed state should yield major problem"))

        s.add_process("another noncritical process", status_method="always_major", tags="not critical")
        self.assertEqual(2, s.get_status(), _("Adding another non critical subprocess should still yield a critical state"))


class TestDomainProcess(TestCase):
    """ Test the Domain business process type
    """
    def setUp(self):
        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

        self.environment.start()

    def testHost(self):
        domain = get_business_process(process_name='ok.is', process_type='domain')

        # We don't exactly know the status of the domain, but lets run it anyway
        # for smoketesting
        domain.get_status()


class TestServiceProcess(TestCase):
    """ Test Service Business process type """
    def setUp(self):
        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

        self.environment.start()

    def testService(self):
        service = get_business_process('ok_host/ok service 1', process_type='service')
        status = service.get_status()
        self.assertFalse(service.errors)
        self.assertEqual(0, status, "The service should always have status OK")


class TestHostProcess(TestCase):
    """ Test the Host business process type
    """
    def setUp(self):
        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

        self.environment.start()

    def testNonExistingHost(self):
        host = get_business_process('non-existant host', process_type='host')
        self.assertEqual(3, host.get_status(), _("non existant host processes should have unknown status"))

    def testExistingHost(self):
        host = get_business_process('ok_host', process_type='host')
        self.assertEqual(0, host.get_status(), _("the host ok_host should always has status ok"))

    def testDomainProcess(self):
        # We don't exactly know the status of the domain, but lets run it anyway
        # for smoketesting
        get_business_process(process_name='oksad.is', process_type='domain')
