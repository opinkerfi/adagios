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
        try:
            self.livestatus.query('GET timeperiods')
        except Exception, e:
            print "%s while trying to read livestatus: %s" % (type(e), e)
            print os.listdir(self.tempdir)
            print os.listdir(self.tempdir + "conf.d")
            if os.path.exists(self.tempdir + "nagios.log"):
                print open(self.tempdir + "nagios.log").read()

    def tearDown(self):
        self.stopNagiosEnvironment()

    def createNagiosEnvironment(self):
        """ Starts a nagios server with empty config in an isolated environment """
        self.tempdir = t = tempfile.mkdtemp('nagios-unittests') + "/"
        cfg_file = t + "/nagios.cfg"
        open(cfg_file, 'w').write('')

        objects_dir = t + "/conf.d"
        os.mkdir(objects_dir)

        with open(objects_dir + "/minimal_config.cfg", 'w') as f:
            f.write(minimal_config)




        config = pynag.Parsers.config(cfg_file=cfg_file)
        config.parse()
        config._edit_static_file(attribute='log_file', new_value=t + "/nagios.log")
        config._edit_static_file(attribute='object_cache_file', new_value=t + "objects.cache")
        config._edit_static_file(attribute='precached_object_file', new_value=t + "/objects.precache")
        config._edit_static_file(attribute='lock_file', new_value=t + "nagios.pid")
        config._edit_static_file(attribute='command_file', new_value=t + "nagios.cmd")
        config._edit_static_file(attribute='state_retention_file', new_value=t + "retention.dat")
        config._edit_static_file(attribute='cfg_dir', new_value=objects_dir)
        config._edit_static_file(attribute='log_initial_states', new_value="1")
        config._edit_static_file(attribute='enable_embedded_perl', new_value='0')
        config._edit_static_file(attribute='event_broker_options', new_value='-1')
        config._edit_static_file(attribute='illegal_macro_output_chars', new_value='''~$&|<>''')

        # Find mk_livestatus broker module
        global_config = pynag.Parsers.config(cfg_file=adagios.settings.nagios_config)
        global_config.parse_maincfg()
        for k, v in global_config.maincfg_values:
            if k == 'broker_module' and 'livestatus' in v:
                livestatus_module = v.split()[0]
                line = "%s %s" % (livestatus_module, t + "/livestatus.socket")
                config._edit_static_file('broker_module', new_value=line)
            elif k == 'p1_file':
                config._edit_static_file(attribute='p1_file', new_value=v)


        self.original_objects_dir = pynag.Model.pynag_directory
        self.original_cfg_file = pynag.Model.cfg_file
        self.original_cfg_file_in_adagios = adagios.settings.nagios_config

        pynag.Model.config = config
        pynag.Model.cfg_file = cfg_file
        pynag.Model.pynag_directory = objects_dir
        pynag.Model.eventhandlers = []
        adagios.settings.nagios_config = cfg_file

        command = [adagios.settings.nagios_binary, '-d', cfg_file]
        result = pynag.Utils.runCommand(command=command, shell=False)
        code, stdout, stderr = result
        if result[0] != 0:
            command_string = ' '.join(command)
            if os.path.exists(self.tempdir + "nagios.log"):
                print open(self.tempdir + "nagios.log").read()
            raise Exception("Failed to start nagios. Command: %s\nexit codecode=%s\nstdout=%s\nstderr=%s" % (command_string, result[0], result[1], result[2]))

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
        adagios.settings.nagios_config = self.original_cfg_file_in_adagios

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

minimal_config = r"""
define timeperiod {
  alias                          24 Hours A Day, 7 Days A Week
  friday          00:00-24:00
  monday          00:00-24:00
  saturday        00:00-24:00
  sunday          00:00-24:00
  thursday        00:00-24:00
  timeperiod_name                24x7
  tuesday         00:00-24:00
  wednesday       00:00-24:00
}

define timeperiod {
  alias                          24x7 Sans Holidays
  friday          00:00-24:00
  monday          00:00-24:00
  saturday        00:00-24:00
  sunday          00:00-24:00
  thursday        00:00-24:00
  timeperiod_name                24x7_sans_holidays
  tuesday         00:00-24:00
  use		us-holidays		; Get holiday exceptions from other timeperiod
  wednesday       00:00-24:00
}

define contactgroup {
  alias                          Nagios Administrators
  contactgroup_name              admins
  members                        nagiosadmin
}

define command {
  command_line                   $USER1$/check_ping -H $HOSTADDRESS$ -w 3000.0,80% -c 5000.0,100% -p 5
  command_name                   check-host-alive
}

define command {
  command_line                   $USER1$/check_dhcp $ARG1$
  command_name                   check_dhcp
}

define command {
  command_line                   $USER1$/check_ftp -H $HOSTADDRESS$ $ARG1$
  command_name                   check_ftp
}

define command {
  command_line                   $USER1$/check_hpjd -H $HOSTADDRESS$ $ARG1$
  command_name                   check_hpjd
}

define command {
  command_line                   $USER1$/check_http -I $HOSTADDRESS$ $ARG1$
  command_name                   check_http
}

define command {
  command_line                   $USER1$/check_imap -H $HOSTADDRESS$ $ARG1$
  command_name                   check_imap
}

define command {
  command_line                   $USER1$/check_disk -w $ARG1$ -c $ARG2$ -p $ARG3$
  command_name                   check_local_disk
}

define command {
  command_line                   $USER1$/check_load -w $ARG1$ -c $ARG2$
  command_name                   check_local_load
}

define command {
  command_line                   $USER1$/check_mrtgtraf -F $ARG1$ -a $ARG2$ -w $ARG3$ -c $ARG4$ -e $ARG5$
  command_name                   check_local_mrtgtraf
}

define command {
  command_line                   $USER1$/check_procs -w $ARG1$ -c $ARG2$ -s $ARG3$
  command_name                   check_local_procs
}

define command {
  command_line                   $USER1$/check_swap -w $ARG1$ -c $ARG2$
  command_name                   check_local_swap
}

define command {
  command_line                   $USER1$/check_users -w $ARG1$ -c $ARG2$
  command_name                   check_local_users
}

define command {
  command_line                   $USER1$/check_nt -H $HOSTADDRESS$ -p 12489 -v $ARG1$ $ARG2$
  command_name                   check_nt
}

define command {
  command_line                   $USER1$/check_ping -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$ -p 5
  command_name                   check_ping
}

define command {
  command_line                   $USER1$/check_pop -H $HOSTADDRESS$ $ARG1$
  command_name                   check_pop
}

define command {
  command_line                   $USER1$/check_smtp -H $HOSTADDRESS$ $ARG1$
  command_name                   check_smtp
}

define command {
  command_line                   $USER1$/check_snmp -H $HOSTADDRESS$ $ARG1$
  command_name                   check_snmp
}

define command {
  command_line                   $USER1$/check_ssh $ARG1$ $HOSTADDRESS$
  command_name                   check_ssh
}

define command {
  command_line                   $USER1$/check_tcp -H $HOSTADDRESS$ -p $ARG1$ $ARG2$
  command_name                   check_tcp
}

define command {
  command_line                   $USER1$/check_udp -H $HOSTADDRESS$ -p $ARG1$ $ARG2$
  command_name                   check_udp
}

define contact {
  name                           generic-contact
  host_notification_commands     notify-host-by-email
  host_notification_options      d,u,r,f,s
  host_notification_period       24x7
  register                       0
  service_notification_commands  notify-service-by-email
  service_notification_options   w,u,c,r,f,s
  service_notification_period    24x7
}

define host {
  name                           generic-host
  event_handler_enabled          1
  failure_prediction_enabled     1
  flap_detection_enabled         1
  notification_period            24x7
  notifications_enabled          1
  process_perf_data              1
  register                       0
  retain_nonstatus_information   1
  retain_status_information      1
}

define host {
  name                           generic-printer
  use                            generic-host
  check_command                  check-host-alive
  check_interval                 5
  check_period                   24x7
  contact_groups                 admins
  max_check_attempts             10
  notification_interval          30
  notification_options           d,r
  notification_period            workhours
  register                       0
  retry_interval                 1
  statusmap_image                printer.png
}

define host {
  name                           generic-router
  use                            generic-switch
  register                       0
  statusmap_image                router.png
}

define service {
  name                           generic-service
  action_url                     /pnp4nagios/graph?host=$HOSTNAME$&srv=$SERVICEDESC$
  active_checks_enabled          1
  check_freshness                0
  check_period                   24x7
  event_handler_enabled          1
  failure_prediction_enabled     1
  flap_detection_enabled         1
  icon_image                     unknown.gif
  is_volatile                    0
  max_check_attempts             3
  normal_check_interval          10
  notes_url                      /adagios/objectbrowser/edit_object/object_type=service/shortname=$HOSTNAME$/$SERVICEDESC$
  notification_interval          60
  notification_options           w,u,c,r
  notification_period            24x7
  notifications_enabled          1
  obsess_over_service            1
  parallelize_check              1
  passive_checks_enabled         1
  process_perf_data              1
  register                       0
  retain_nonstatus_information   1
  retain_status_information      1
  retry_check_interval           2
}

define host {
  name                           generic-switch
  use                            generic-host
  check_command                  check-host-alive
  check_interval                 5
  check_period                   24x7
  contact_groups                 admins
  max_check_attempts             10
  notification_interval          30
  notification_options           d,r
  notification_period            24x7
  register                       0
  retry_interval                 1
  statusmap_image                switch.png
}

define host {
  name                           linux-server
  use                            generic-host
  check_command                  check-host-alive
  check_interval                 5
  check_period                   24x7
  contact_groups                 admins
  max_check_attempts             10
  notification_interval          120
  notification_options           d,u,r
  notification_period            workhours
  register                       0
  retry_interval                 1
}

define service {
  name                           local-service
  use                            generic-service
  max_check_attempts             4
  normal_check_interval          5
  register                       0
  retry_check_interval           1
}

define contact {
  use                            generic-contact
  alias                          Nagios Admin
  contact_name                   nagiosadmin
  email                          nagios@localhost
}

define timeperiod {
  alias                          No Time Is A Good Time
  timeperiod_name                none
}

define command {
  command_line                   /usr/bin/printf "%b" "***** Nagios *****\n\nNotification Type: $NOTIFICATIONTYPE$\nHost: $HOSTNAME$\nState: $HOSTSTATE$\nAddress: $HOSTADDRESS$\nInfo: $HOSTOUTPUT$\n\nDate/Time: $LONGDATETIME$\n" | /bin/mail -s "** $NOTIFICATIONTYPE$ Host Alert: $HOSTNAME$ is $HOSTSTATE$ **" $CONTACTEMAIL$
  command_name                   notify-host-by-email
}

define command {
  command_line                   /usr/bin/printf "%b" "***** Nagios *****\n\nNotification Type: $NOTIFICATIONTYPE$\n\nService: $SERVICEDESC$\nHost: $HOSTALIAS$\nAddress: $HOSTADDRESS$\nState: $SERVICESTATE$\n\nDate/Time: $LONGDATETIME$\n\nAdditional Info:\n\n$SERVICEOUTPUT$\n" | /bin/mail -s "** $NOTIFICATIONTYPE$ Service Alert: $HOSTALIAS$/$SERVICEDESC$ is $SERVICESTATE$ **" $CONTACTEMAIL$
  command_name                   notify-service-by-email
}

define command {
  command_line                   /usr/bin/printf "%b" "$LASTHOSTCHECK$\t$HOSTNAME$\t$HOSTSTATE$\t$HOSTATTEMPT$\t$HOSTSTATETYPE$\t$HOSTEXECUTIONTIME$\t$HOSTOUTPUT$\t$HOSTPERFDATA$\n" >> /var/log/nagios/host-perfdata.out
  command_name                   process-host-perfdata
}

define command {
  command_line                   /usr/bin/printf "%b" "$LASTSERVICECHECK$\t$HOSTNAME$\t$SERVICEDESC$\t$SERVICESTATE$\t$SERVICEATTEMPT$\t$SERVICESTATETYPE$\t$SERVICEEXECUTIONTIME$\t$SERVICELATENCY$\t$SERVICEOUTPUT$\t$SERVICEPERFDATA$\n" >> /var/log/nagios/service-perfdata.out
  command_name                   process-service-perfdata
}

define timeperiod {
  alias                          U.S. Holidays
  december 25             00:00-00:00     ; Christmas
  january 1               00:00-00:00     ; New Years
  july 4                  00:00-00:00     ; Independence Day
  monday -1 may           00:00-00:00     ; Memorial Day (last Monday in May)
  monday 1 september      00:00-00:00     ; Labor Day (first Monday in September)
  name			us-holidays
  thursday 4 november     00:00-00:00     ; Thanksgiving (4th Thursday in November)
  timeperiod_name                us-holidays
}

define host {
  name                           windows-server
  use                            generic-host
  check_command                  check-host-alive
  check_interval                 5
  check_period                   24x7
  contact_groups                 admins
  hostgroups
  max_check_attempts             10
  notification_interval          30
  notification_options           d,r
  notification_period            24x7
  register                       0
  retry_interval                 1
}

define hostgroup {
  alias                          Windows Servers
  hostgroup_name                 windows-servers
}

define timeperiod {
  alias                          Normal Work Hours
  friday		09:00-17:00
  monday		09:00-17:00
  thursday	09:00-17:00
  timeperiod_name                workhours
  tuesday		09:00-17:00
  wednesday	09:00-17:00
}

define command {
	command_name	check_dummy
	command_line	$USER1$/check_dummy!$ARG1$!$ARG2$
}


define host {
	host_name		ok_host
	use			generic-host
	address			ok_host
	max_check_attempts	1
	check_command		check_dummy!0!Everything seems to be okay
}


define service {
	host_name		ok_host
	use			generic-service
	service_description	ok service 1
	check_command		check_dummy!0!Everything seems to be okay
}

"""