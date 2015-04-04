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
from django.core.urlresolvers import reverse
from django.http import QueryDict
import pynag.Model
import adagios.settings
import adagios.utils
import adagios.objectbrowser.forms
import re
import adagios.seleniumtests

from adagios.objectbrowser.forms import PynagAutoCompleteField

pynag.Model.cfg_file = adagios.settings.nagios_config

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
except ImportError:
    # selenium tests are skipped if selenium is not available
    pass


class TestObjectBrowser(unittest.TestCase):

    def testNagiosConfigFile(self):
        result = pynag.Model.ObjectDefinition.objects.all
        config = pynag.Model.config.cfg_file
        self.assertGreaterEqual(
            len(result), 0, msg=_("Parsed nagios.cfg, but found no objects, are you sure this is the right config file (%(config)s) ? ") % {'config': config})

    def testIndexPage(self):
        c = Client()
        response = c.get('/objectbrowser/')
        self.assertEqual(response.status_code, 200)

    def testPageLoad(self):
        """ Smoke test a bunch of views """

        # TODO: Better tests, at least squeeze out a 200OK for these views
        self.loadPage('/objectbrowser/')
        self.loadPage('/objectbrowser/copy', 404)
        self.loadPage('/objectbrowser/search')
        self.loadPage('/objectbrowser/delete', 404)
        self.loadPage('/objectbrowser/bulk_edit')
        self.loadPage('/objectbrowser/bulk_delete')
        self.loadPage('/objectbrowser/bulk_copy')

        self.loadPage('/objectbrowser/edit_all', 404)
        self.loadPage('/objectbrowser/copy_and_edit', 301)

        self.loadPage('/objectbrowser/plugins')
        self.loadPage('/objectbrowser/nagios.cfg')
        self.loadPage('/objectbrowser/import')
        self.loadPage('/objectbrowser/geek_edit', 404)
        self.loadPage('/objectbrowser/advanced_edit', 404)

        #self.loadPage('/objectbrowser/add_to_group')
        self.loadPage('/objectbrowser/add/host', 200)
        self.loadPage('/objectbrowser/add/hostgroup', 200)
        self.loadPage('/objectbrowser/add/service', 200)
        self.loadPage('/objectbrowser/add/servicegroup', 200)
        self.loadPage('/objectbrowser/add/contact', 200)
        self.loadPage('/objectbrowser/add/contactgroup', 200)
        self.loadPage('/objectbrowser/add/timeperiod', 200)
        self.loadPage('/objectbrowser/add/command', 200)
        self.loadPage('/objectbrowser/add/template', 200)

    def loadPage(self, url, expected_code=200):
        """ Load one specific page, and assert if return code is not 200 """
        try:
            c = Client()
            response = c.get(url)
            self.assertEqual(response.status_code, expected_code, _("Expected status code 200 for page %(url)s") % {'url': url})
        except Exception, e:
            self.assertEqual(True, _("Unhandled exception while loading %(url)s: %(error)s") % {'url': url, 'error': e})


class TestPynagForm(unittest.TestCase):
    def setUp(self):
        self.nagios_config = adagios.settings.nagios_config
        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

    def _create_new_host(self):
        host_name = 'unique foo'
        # Make sure host does not exist
        hosts = pynag.Model.Host.objects.filter(host_name=host_name)
        self.assertFalse(hosts, "There should be no host named %s" % host_name)
        host = pynag.Model.Host(host_name=host_name)
        host.save()

        # Make sure host was saved:
        hosts = pynag.Model.Host.objects.filter(host_name=host_name)
        self.assertTrue(hosts, "There should be one host named %s" % host_name)

        return hosts[0]

    def testBasicEdit(self):
        base_url = '/objectbrowser/edit/'

        host = self._create_new_host()
        host_name = host.host_name

        # Load the host via objectbrowser/edit
        url = '{base_url}{object_id}'
        url = url.format(base_url=base_url, object_id=host.get_id())

        c = Client()
        response = c.get(url)
        self.assertEqual(200, response.status_code)

        # See if the output more or less makes sense
        search_string_re = '<input[^>]* name="advanced-host_name"[^>]* value="{host_name}"'
        search_string_re = search_string_re.format(host_name=host_name)
        self.assertTrue(re.search(search_string_re, response.content))

        # Check the actual form we were sent
        form = response.context['form']
        data = form.initial

        self.assertIsNone(data.get('alias'))
        data['alias'] = host_name
        self.assertEqual(host_name, data.get('alias'))
        response = c.post(url, data=data)
        self.assertEqual(302, response.status_code)
        next_url = response['Location']

        response = c.get(next_url)
        self.assertEqual(200, response.status_code)
        form = response.context['form']
        data = form.initial
        self.assertEqual(data['host_name'], host_name)
        #TODO: Uncomment this once the underlying bug has been fixed
        #self.assertEqual(data['alias'], host_name)

    def testBasicEditing(self):
        host = self._create_new_host()
        host_name = host.host_name
        alias = 'some alias for this host'

        initial = host._original_attributes.copy()
        form = adagios.objectbrowser.forms.PynagForm(host, initial=initial)
        data = form.initial
        data['alias'] = alias

        form = adagios.objectbrowser.forms.PynagForm(host, data=data)
        self.assertTrue('alias' in form.data)
        self.assertEqual(alias, data['alias'])
        self.assertTrue('alias' in form.changed_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(alias, form.pynag_object.alias)

        hosts = pynag.Model.Host.objects.filter(host_name=host_name)
        self.assertEqual(1, len(hosts), "there should be exactly 1 host with host_name %s" % host_name)
        host = hosts[0]
        self.assertEqual(host_name, host.host_name)
        self.assertEqual(alias, host.alias)

        # Test that there were no other attributes saved:
        attrs = sorted(host._defined_attributes.keys())
        self.assertEqual(['alias', 'host_name'], attrs)

    def testMultiChoiceFieldEmptyValue(self):
        host = self._create_new_host()
        hostgroups = ''
        host = self._change_object_via_form(host, hostgroups=hostgroups)
        self.assertIsNone(host.hostgroups)

        hostgroups = None
        host = self._change_object_via_form(host, hostgroups=hostgroups)
        self.assertIsNone(host.hostgroups)

        hostgroups = []
        host = self._change_object_via_form(host, hostgroups=hostgroups)
        self.assertIsNone(host.hostgroups)

        self._test_correct_attributes(host, 'host_name')

        hostgroups = 'bla,bla2'
        host = self._change_object_via_form(host, hostgroups=hostgroups)
        self.assertEqual('bla,bla2', host.hostgroups)

        self._test_correct_attributes(host, 'host_name', 'hostgroups')

    def _test_correct_attributes(self, pynag_object, *args):
        """ Asserts if pynag_object._defined_attributes does not match *args"""
        attrs = sorted(pynag_object._defined_attributes.keys())
        expected_attrs = sorted(args)
        self.assertEqual(expected_attrs, attrs)

    def _change_object_via_form(self, my_object=None, **kwargs):
        """ Changes a pynag object using PynagForm

        Args:
            my_object: any pynag object, if empty, autocreate new host
            **kwargs: Any kwargs provided will be attribute:new_value pairs
        Returns:
            The pynag object after it has been saved
        """
        if not my_object:
            my_object = self._create_new_host()

        data = {}
        for key, value in kwargs.iteritems():
            data[key] = value
        # Create new form for saving the data
        form = adagios.objectbrowser.forms.PynagForm(my_object, data=data)
        self.assertTrue(form.is_valid())
        form.save()

        new_id = form.pynag_object.get_id()
        new_object = pynag.Model.ObjectDefinition.objects.get_by_id(new_id)
        return new_object

    def test_changed_data(self):
        my_object = pynag.Model.Service()
        my_object.rewrite(_TEST_SERVICE)
        my_object.save()
        data = {}

        form = adagios.objectbrowser.forms.PynagForm(my_object, data=data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.changed_data)

        data['service_description'] = "new_description"
        form = adagios.objectbrowser.forms.PynagForm(my_object, data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(data.keys(), form.changed_data)

        data['hostgroup_name'] = 'bla'
        form = adagios.objectbrowser.forms.PynagForm(my_object, data=data)
        self.assertTrue(form.is_valid())
        self.assertListEqual(sorted(data.keys()), sorted(form.changed_data))

    def test_change_hostgroup(self):
        host = self._create_new_host()
        host_name = host.host_name
        hostgroups = '+h1,h2'
        host.hostgroups = hostgroups
        host.save()

        form = adagios.objectbrowser.forms.PynagForm(host)
        data = form.initial
        # Check we made no changes to the form and hostgroups is in fact
        # unchanged
        form = adagios.objectbrowser.forms.PynagForm(host, data=data)
        self.assertTrue(form.is_valid())
        form.save()
        host = pynag.Model.Host.objects.get_by_shortname(host_name)
        self.assertEqual(hostgroups, host.hostgroups)

        # Change the hostgroup and make sure the + is left intact
        form = adagios.objectbrowser.forms.PynagForm(host, data={'hostgroups': 'h2'})
        self.assertTrue(form.is_valid())
        form.save()
        host = pynag.Model.Host.objects.get_by_shortname(host_name)
        self.assertEqual('+h2', host.hostgroups)

    def test_issue_389_via_form(self):
        my_object = pynag.Model.Service()
        my_object.rewrite(_TEST_SERVICE)
        my_object.save()
        service_description = 'bla alias'

        new_object = self._change_object_via_form(my_object, service_description=service_description)
        self.assertEqual(service_description, new_object.service_description)

        data = QueryDict('check_period=24x7&use=generic-service&active_checks_enabled=0&notification_period=24x7&check_command=check-liebert-ac-temp&passive_checks_enabled=0&check_interval=1&service_description=Return+Temperatur&max_check_attempts=4&first_notification_delay=&csrfmiddlewaretoken=29180855d18882df3752806ed4d43567&notification_options=w&notification_options=c&notification_options=r&notification_options=u')
        form = adagios.objectbrowser.forms.PynagForm(new_object, data=data)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual('0', form.pynag_object.active_checks_enabled)
        self.assertEqual('HVAC', form.pynag_object.hostgroup_name)

    def test_issue_389_via_view(self):
        # In this test we have a problematic service that produces several bugs when user opens it in
        # objectbrowser and just presses save.
        my_object = pynag.Model.Service()
        my_object.rewrite(_TEST_SERVICE)
        my_object.save()

        url = '/objectbrowser/edit/{object_id}'.format(object_id=my_object.get_id())
        c = Client()

        # This is the exact querystring that was proplematic in issue 389. You can generate a new one
        # By editing edit_object() and printing out request.POST.urlencode()
        data = QueryDict('check_period=24x7&use=generic-service&active_checks_enabled=1&notification_interval=0&contacts=&notification_period=24x7&check_command=check-liebert-ac-temp&contact_groups=Facilities+Admin&servicegroups=&host_name=null&check_interval=1&service_description=Return+Temperature&csrfmiddlewaretoken=29180855d18882df3752806ed4d43567&first_notification_delay=&max_check_attempts=4&notification_options=w&notification_options=c&notification_options=r&notification_options=u&passive_checks_enabled=0')
        response = c.post(url, data)  # Simulate a user that just pressed save button.
        self.assertEqual(302, response.status_code)

        # Get the service again, verify it was changed
        services = pynag.Model.Service.objects.filter(service_description=my_object.service_description)
        self.assertEqual(
            1,
            len(services),
            "No service found with the new service description: %s" % my_object.service_description
        )
        new_service = services[0]

        # Manually change the servie description back, to original and make sure they are the same:
        new_service.service_description = my_object.service_description
        #self.assertEqual(my_object, new_service)

        # Iterate through every field in our original service, make sure
        # They are all same as expected
        for key, old_value in my_object._defined_attributes.items():
            new_value = new_service[key]
            # TODO: Find out what is broken in check_command
            if key in ('check_command'):
                continue
            message = "%s wasnt supposed to change after saving the service" % key
            self.assertEqual(old_value, new_value, message)

        # Same with the new object, just make sure nothinig got created that was not supposed to be there:
        for key in new_service._defined_attributes:
            # TODO: There is a bug which causes these extra attributes to be saved. Cant reproduce it in real
            # Life yet.
            if key in ('active_checks_enabled', 'notification_interval', 'max_check_attempts', 'notification_options'):
                continue
            message = "new service is not supposed to have %s after save" % key
            self.assertFalse(my_object[key] is None, message)

        self.assertTrue(new_service.hostgroup_name == 'HVAC')

    def test_init(self):

        dataset = {'host_name': 'new host_name'}
        empty_service = pynag.Model.Service()
        form = adagios.objectbrowser.forms.PynagForm(empty_service)
        self.assertEqual({}, form.initial)
        self.assertEqual({}, form.data)

        # Little field sanity check
        self.assertTrue('action_url' in form.fields)
        self.assertTrue('host_name' in form.fields)
        self.assertTrue('use' in form.fields)
        self.assertFalse('nonexistant' in form.fields)

        form = adagios.objectbrowser.forms.PynagForm(empty_service, initial=dataset)
        self.assertEqual(dataset, form.initial)
        self.assertEqual({}, form.data)

        form = adagios.objectbrowser.forms.PynagForm(empty_service, data=dataset)
        self.assertEqual(dataset, form.data)
        self.assertEqual({}, form.initial)

    def test_init_are_fields_initilized(self):
        dataset = {'host_name': 'new host_name'}
        empty_service = pynag.Model.Service()
        form = adagios.objectbrowser.forms.PynagForm(empty_service, initial=dataset)
        self.assertEqual(dataset, form.initial)
        self.assertEqual({}, form.data)

        for field_name, field in form.fields.items():
            expected_data = dataset.get(field_name, None)
            message = "Testing initial value for field %s" % field_name
            self.assertEqual(expected_data, field.initial, message)

    def test_initial_value_for_hostgroup(self):
        field_name = 'hostgroups'
        field_value = 'test,test2'
        clean_value = 'test,test2'

        dataset = {field_name: field_value}
        host = pynag.Model.Host(**dataset)
        empty_host = pynag.Model.Host()

        form = adagios.objectbrowser.forms.PynagForm(host)
        self.assertEqual(field_value, form.fields[field_name].initial)

        form = adagios.objectbrowser.forms.PynagForm(empty_host, initial=dataset)
        self.assertEqual(field_value, form.fields[field_name].initial)

        # Try same with a bound form
        form = adagios.objectbrowser.forms.PynagForm(empty_host, data=dataset)
        self.assertTrue(form.is_valid())
        self.assertTrue([field_name], form.changed_data)
        self.assertEqual(field_value, form.data[field_name])
        self.assertEqual(clean_value, form.cleaned_data[field_name])

    def test_initial_values(self):
        dataset = {'service_description': 'unit test', 'use': 'generic-service'}
        service = pynag.Model.Service(**dataset)
        form = adagios.objectbrowser.forms.PynagForm(service)
        self.assertEqual(dataset, form.initial)
        self.assertEqual({}, form.data)


class TestPynagAutoCompleteField(unittest.TestCase):
    def setUp(self):
        self.nagios_config = adagios.settings.nagios_config
        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

    def test_init(self):
        field = PynagAutoCompleteField('host')
        self.assertIsInstance(field, adagios.objectbrowser.forms.PynagAutoCompleteField)

    def test_helptext(self):
        inline_help_text = 'this is a help text'
        field = adagios.objectbrowser.forms.PynagAutoCompleteField('host', inline_help_text=inline_help_text)
        self.assertEqual(inline_help_text, field.widget.attrs['data-placeholder'])

    def test_choices(self):
        field = PynagAutoCompleteField('host', complete="shortname")
        choices_string = field.widget.attrs['data-choices']
        choices_list = choices_string.split(',')
        self.assertIn('ok_host', choices_list)
        self.assertNotIn(None, choices_list)

        field = PynagAutoCompleteField('host', complete="name")
        choices_string = field.widget.attrs['data-choices']
        choices_list = choices_string.split(',')
        self.assertIn('generic-host', choices_list)
        self.assertIn('linux-server', choices_list)
        self.assertNotIn(None, choices_list)
        self.assertNotIn('apc02.disney.com', choices_list)

    def test_get_all_shortnames(self):
        object_type = 'host'
        field = adagios.objectbrowser.forms.PynagAutoCompleteField(object_type=object_type)
        shortnames = field.get_all_shortnames(object_type=object_type)
        self.assertIn('ok_host', shortnames)
        self.assertNotIn(None, shortnames)

    def test_get_all_object_names(self):
        object_type = 'host'
        field = adagios.objectbrowser.forms.PynagAutoCompleteField(object_type=object_type)
        names = field.get_all_object_names(object_type=object_type)
        self.assertNotIn(None, names)
        self.assertIn('generic-host', names)
        self.assertIn('linux-server', names)

    def test_prepare_value(self):
        field = PynagAutoCompleteField(object_type='host')

        self.assertEqual('a,b', field.prepare_value('a,b'))
        self.assertEqual('a,b', field.prepare_value('+a,b'))
        self.assertEqual('a', field.prepare_value('a'))
        self.assertEqual('null', field.prepare_value('null'))


class TestPynagChoiceField(unittest.TestCase):
    def setUp(self):
        self.nagios_config = adagios.settings.nagios_config
        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

    def test_prepare_value(self):
        field = adagios.objectbrowser.forms.PynagChoiceField(initial=None)
        prepare_value = field.prepare_value

        self.assertEqual([], prepare_value(''))
        self.assertEqual([], prepare_value(None))
        self.assertEqual(['a'], prepare_value('a'))
        self.assertEqual(['a'], prepare_value('+a'))
        self.assertEqual(['a'], prepare_value('-a'))
        self.assertEqual(['a'], prepare_value('!a'))
        self.assertEqual(['a', 'b'], prepare_value('a,b'))
        self.assertEqual(['a', 'b'], prepare_value('+a,b'))
        self.assertEqual(['a', 'b'], prepare_value('!a, b'))

        # Test some invalid values
        with self.assertRaises(ValueError):
            prepare_value([])

    def test_init(self):
        initial = 'bla'
        inline_help_text = 'help me'
        field = adagios.objectbrowser.forms.PynagChoiceField(initial=initial, inline_help_text=inline_help_text)
        self.assertEqual(initial, field.initial)
        self.assertEqual(inline_help_text, field.widget.attrs.get('data-placeholder', None))

    def test_clean(self):
        field = adagios.objectbrowser.forms.PynagChoiceField(initial='+ab')
        clean = field.clean

        self.assertEqual('a,b', clean(['a', 'b']))
        self.assertEqual('a,b', clean(('a', 'b')))
        self.assertEqual('b,a', clean(('b', 'a')))

        field.set_prefix('+')
        self.assertEqual('+a,b', clean(['a', 'b']))

        self.assertEqual('null', field.clean([]))

    def test_set_prefix(self):
        field = adagios.objectbrowser.forms.PynagChoiceField()
        self.assertEqual('', field.get_prefix())

        field.set_prefix('+')
        self.assertEqual('+', field.get_prefix())

        field.set_prefix('')
        self.assertEqual('', field.get_prefix())


class TestImportObjectsForm(unittest.TestCase):
    def setUp(self):
        self.nagios_config = adagios.settings.nagios_config

        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

        self.form = adagios.objectbrowser.forms.ImportObjectsForm()
        self.initial = {
            'objects': 'host_name,address\nlocalhost,127.0.0.1',
            'object_type': 'host',
            'seperator': ',',
            'destination_filename': '',
        }

    def test_is_valid_initial_is_false(self):
        self.assertEqual(False, self.form.is_valid())

    def test_is_valid_normal(self):
        form = adagios.objectbrowser.forms.ImportObjectsForm(data=self.initial)
        self.assertTrue(form.is_valid())

    def test_save(self):
        self.assertFalse(pynag.Model.Host.objects.filter(shortname='localhost'))
        form = adagios.objectbrowser.forms.ImportObjectsForm(data=self.initial)
        form.is_valid()
        objects = form.save()
        self.assertEqual(1, len(objects))
        self.assertTrue(pynag.Model.Host.objects.filter(shortname='localhost'))

class AddObjectForm(unittest.TestCase):

    def setUp(self):
        self.environment = adagios.utils.get_test_environment()
        self.addCleanup(self.environment.terminate)

    def test_get_template_if_it_exists(self):
        form = adagios.objectbrowser.forms.AddObjectForm('host')
        self.assertEqual(adagios.settings.default_host_template, form.get_template_if_it_exists())

    def test_get_template_if_it_exists_nonexistant(self):
        host = pynag.Model.Host.objects.get_by_name(adagios.settings.default_host_template)
        host.delete()
        form = adagios.objectbrowser.forms.AddObjectForm('host')
        self.assertEqual('', form.get_template_if_it_exists())

class SeleniumObjectBrowserTestCase(adagios.seleniumtests.SeleniumTestCase):
    def test_contacts_loading(self):
        """Test if contacts under configure loads"""
        for driver in self.drivers:
            driver.get(self.live_server_url + "/objectbrowser/#contact-tab_tab")

            wait = WebDriverWait(driver, 10)

            try:
                # Get all host rows
                contact_table_rows = wait.until(
                    EC.presence_of_all_elements_located((
                        By.XPATH,
                        "//table[contains(@id, 'contact-table')]/tbody/tr"))
                )
            except TimeoutException:
                self.assertTrue(False, "Timed out waiting for contact table to load")

            self.assertTrue(len(contact_table_rows) > 0,
                            "No table rows in contact table")

    def test_hosts_loading(self):
        """Test if hosts under configure loads"""
        for driver in self.drivers:
            driver.get(self.live_server_url + "/objectbrowser")

            wait = WebDriverWait(driver, 10)

            try:
                # Get all host rows
                host_table_rows = wait.until(
                    EC.presence_of_all_elements_located((
                        By.XPATH,
                        "//table[contains(@id, 'host-table')]/tbody/tr"))
                )
            except TimeoutException:
                self.assertTrue(False, "Timed out waiting for host table to load")

            self.assertTrue(len(host_table_rows) > 0,
                            "No table rows in host-table")

_TEST_SERVICE = """
define service {
    use generic-service
    check_command check-liebert-ac-temp!google123!returnTemp!"105,45"!"100,50"
    hostgroup_name HVAC
    passive_checks_enabled 0
    service_description Return Temperature
    host_name null
    check_interval 1
    contact_groups Facilities Admin
}
"""
