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
from django.test.client import RequestFactory
import adagios.utils
import adagios.misc.rest
import adagios.userdata
import os


class FakeAdagiosEnvironment(unittest.TestCase):
    """ Test the features of adagios.utils.FakeAdagiosEnvironment
    """
    @classmethod
    def setUpClass(cls):
        cls.fake_adagios = adagios.utils.FakeAdagiosEnvironment()

    @classmethod
    def tearDownClass(cls):
        cls.fake_adagios.terminate()

    def testFakeAdagiosEnvironment(self):
        fake_adagios = self.fake_adagios

        # Make sure temporary environment gets created
        fake_adagios.create_minimal_environment()
        self.assertTrue(os.path.exists(fake_adagios.adagios_config_file))

        # Make sure adagios.settings is updated
        global_config_file = adagios.settings.adagios_configfile
        fake_adagios.update_adagios_global_variables()

        # Make sure adagios_config_file changed
        self.assertTrue(adagios.settings.adagios_configfile != global_config_file)

        # Make sure the new test is in the tempdir
        self.assertTrue(adagios.settings.adagios_configfile.startswith(fake_adagios.tempdir))

        # Make sure global variables are proparly restored
        fake_adagios.restore_adagios_global_variables()
        self.assertTrue(adagios.settings.adagios_configfile == global_config_file)


class MiscTestCase(unittest.TestCase):

    def setUp(self):
        self.environment = adagios.utils.get_test_environment()

    def tearDown(self):
        self.environment.terminate()

    def _testPageLoad(self, url):
        c = Client()
        response = c.get(url)
        self.assertEqual(response.status_code, 200)

    def TestPageLoads(self):
        """ Smoke test views in /misc/
        """
        self.loadPage("/misc/settings")
        self.loadPage("/misc/preferences")
        self.loadPage("/misc/nagios")
        self.loadPage("/misc/settings")
        self.loadPage("/misc/service")
        self.loadPage("/misc/pnp4nagios")
        self.loadPage("/misc/mail")
        self.loadPage("/misc/images")

    def loadPage(self, url):
        """ Load one specific page, and assert if return code is not 200 """
        try:
            c = Client()
            response = c.get(url)
            self.assertEqual(response.status_code, 200, _("Expected status code 200 for page %s") % url)
        except Exception, e:
            self.assertEqual(True, _("Unhandled exception while loading %(url)s: %(e)s") % {'url': url, 'e': e})

    def test_user_preferences(self):
        c = Client()
        response = c.post('/misc/preferences/',
                          {'theme': 'spacelab', 'language': 'fr'})

        assert(response.status_code == 200)
        assert('spacelab/style.css' in response.content)
        assert('(fr)' in response.content)

    def load_get(self, url):
        c = Client()
        response = c.get(url)
        return response
    
    def test_topmenu_highlight(self):
        r = self.load_get('/status/')
        assert '<li class="active">\n  <a href="/status">' in r.content
    
    def test_leftmenu_highlight(self):
        r = self.load_get('/status/problems')
        assert '<li class="active">\n          <a href="/status/problems">' in r.content
    
    def test_app_name(self):
        from adagios import settings
        settings.TOPMENU_HOME = 'Free beer'
        r = self.load_get('/status')
        assert 'Free beer' in r.content


class RestTest(unittest.TestCase):
    """Tests for adagios.misc.rest"""
    def setUp(self):
        self.environment = adagios.utils.get_test_environment()

        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.user = adagios.userdata.User(self.request)
        self.user._username = 'test'
        self.user.__dict__ = {}
        self.user.save()

    def tearDown(self):
        self.environment.terminate()

    def test_save_search(self):
        adagios.misc.rest.save_search(self.request, 'test', 'http://localhost')
        user = adagios.userdata.User(self.request)
        self.assertEqual({'test':'http://localhost'}, user.to_dict()['saved_searches'])

    def test_get_saved_searches(self):
        adagios.misc.rest.save_search(self.request, 'test', 'http://adagios')
        self.assertEqual({'test':'http://adagios'}, adagios.misc.rest.get_saved_searches(self.request))

    def test_save_search_raises_on_no_name(self):
        with self.assertRaises(ValueError):
            adagios.misc.rest.save_search(self.request, '', 'http://localhost')

    def test_save_search_raises_on_no_url(self):
        with self.assertRaises(ValueError):
            adagios.misc.rest.save_search(self.request, 'name', '')

    def test_delete_saved_search(self):
        adagios.misc.rest.save_search(self.request, 'test', 'http://adagios')
        self.assertEqual({'test':'http://adagios'}, adagios.misc.rest.get_saved_searches(self.request))

        adagios.misc.rest.delete_saved_search(self.request, 'test')
        self.assertFalse(adagios.misc.rest.get_saved_searches(self.request))
