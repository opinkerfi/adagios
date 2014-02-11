"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import tempfile
import os





from django.test import TestCase
from django.test.client import Client

from adagios.bi import *


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
            self.assertEqual(response.status_code, 200, "Expected status code 200 for page %s" % url)
        except Exception, e:
            self.assertEqual(True, "Unhandled exception while loading %s: %s" % (url, e))


class TestBusinessProcessLogic(TestCase):
    """ This class responsible for testing business classes logic """
    def setUp(self):
        fd, filename = tempfile.mkstemp()
        BusinessProcess._default_filename = filename

    def tearDown(self):
        os.remove(BusinessProcess._default_filename)

    def testBestAndWorstState(self):
        s = BusinessProcess("example process")
        s.status_method = 'use_worst_state'
        self.assertEqual(3, s.get_status(), "Empty bi process should have status unknown")

        s.add_process(process_name="always_ok", process_type="businessprocess", status_method='always_ok')
        self.assertEqual(0, s.get_status(), "BI process with one ok subitem, should have state OK")

        s.add_process("fail subprocess", status_method="always_major")
        self.assertEqual(2, s.get_status(), "BI process with one failed item should have a critical state")

        s.status_method = 'use_best_state'
        self.assertEqual(0, s.get_status(), "BI process using use_best_state should be returning OK")

    def testBusinessRules(self):
        s = BusinessProcess("example process")
        self.assertEqual(3, s.get_status(), "Empty bi process should have status unknown")

        s.add_process(process_name="always_ok", process_type="businessprocess", status_method='always_ok')
        self.assertEqual(0, s.get_status(), "BI process with one ok subitem, should have state OK")

        s.add_process("untagged process", status_method="always_major")
        self.assertEqual(0, s.get_status(), "BI subprocess that is untagged should yield an ok state")

        s.add_process("not critical process", status_method="always_major", tags="not critical")
        self.assertEqual(1, s.get_status(), "A Non critical subprocess should yield 'minor problem'")

        s.add_process("critical process", status_method="always_major", tags="mission critical")
        self.assertEqual(2, s.get_status(), "A critical process in failed state should yield major problem")

        s.add_process("another noncritical process", status_method="always_major", tags="not critical")
        self.assertEqual(2, s.get_status(), "Adding another non critical subprocess should still yield a critical state")


class TestDomainProcess(TestCase):
    """ Test the Domain business process type
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testHost(self):
        domain = get_business_process(process_name='ok.is', process_type='domain')

        # We don't exactly know the status of the domain, but lets run it anyway
        # for smoketesting
        domain.get_status()


import pynag.Model
import pynag.Utils


class TestHostProcess(TestCase):
    """ Test the Host business process type
    """
    def setUp(self):
        self.createNagiosEnvironment()
        self.livestatus = pynag.Parsers.mk_livestatus(nagios_cfg_file=pynag.Model.cfg_file)
    def tearDown(self):
        self.stopNagiosEnvironment()
    def createNagiosEnvironment(self):
        """ Starts a nagios server with empty config in an isolated environment """
        self.tempdir = t = tempfile.mkdtemp('nagios-unittests') + "/"
        cfg_file = t + "/nagios.cfg"
        open(cfg_file, 'w').write('')

        objects_dir = t + "/conf.d"
        os.mkdir(objects_dir)

        minimal_objects_file = os.path.dirname(adagios.__file__) + "/../tests/config/conf.d/minimal_config.cfg"
        command = ['cp', minimal_objects_file, objects_dir]
        pynag.Utils.runCommand(command=command, shell=False)




        config = pynag.Parsers.config(cfg_file=cfg_file)
        config.parse()
        config._edit_static_file(attribute='illegal_macro_output_chars', new_value='''`~$&|'"<>''')
        config._edit_static_file(attribute='log_file', new_value=t + "/nagios.log")
        config._edit_static_file(attribute='object_cache_file', new_value=t + "objects.cache")
        config._edit_static_file(attribute='precached_object_file', new_value=t + "/objects.precache")
        config._edit_static_file(attribute='lock_file', new_value=t + "nagios.pid")
        config._edit_static_file(attribute='command_file', new_value=t + "nagios.cmd")
        config._edit_static_file(attribute='state_retention_file', new_value=t + "retention.dat")
        config._edit_static_file(attribute='cfg_dir', new_value=objects_dir)
        config._edit_static_file(attribute='p1_file', new_value=cfg_file)
        config._edit_static_file(attribute='enable_embedded_perl', new_value='0')
        config._edit_static_file(attribute='event_broker_options', new_value='-1')

        # Find mk_livestatus broker module
        global_config = pynag.Parsers.config(cfg_file=adagios.settings.nagios_config)
        global_config.parse_maincfg()
        for k, v in global_config.maincfg_values:
            if k == 'broker_module' and 'livestatus' in v:
                livestatus_module = v.split()[0]
                line = "%s %s" % (livestatus_module, t + "/livestatus.socket")
                config._edit_static_file('broker_module', new_value=line)


        self.original_objects_dir = pynag.Model.pynag_directory
        self.original_cfg_file = pynag.Model.cfg_file

        pynag.Model.config = config
        pynag.Model.cfg_file = cfg_file
        pynag.Model.pynag_directory = objects_dir
        pynag.Model.eventhandlers = []

        command = "%s "
        pynag.Utils.runCommand(command=[adagios.settings.nagios_binary, '-d', cfg_file], shell=False)[1]

    def stopNagiosEnvironment(self):
        # Stop nagios service
        pid = open(self.tempdir + "nagios.pid").read()
        pynag.Utils.runCommand(command=['kill', pid], shell=False)

        # Clean up temp directory
        command = 'rm','-rf', self.tempdir
        pynag.Utils.runCommand(command=command, shell=False)
        pynag.Model.config = None
        pynag.Model.cfg_file = self.original_cfg_file
        pynag.Model.pynag_directory = self.original_objects_dir

    def testNonExistingHost(self):
        host = get_business_process('non-existant host', process_type='host')
        self.assertEqual(3, host.get_status(), "non existant host processes should have unknown status")

    def testExistingHost(self):
        #localhost = self.livestatus.get_hosts('Filter: host_name = ok_host')
        host = get_business_process('ok_host', process_type='host')
        self.assertEqual(0, host.get_status(), "the host ok_host should always has status ok")

    def testDomainProcess(self):
        domain = get_business_process(process_name='oksad.is', process_type='domain')
        # We don't exactly know the status of the domain, but lets run it anyway
        # for smoketesting
        print domain.get_status()