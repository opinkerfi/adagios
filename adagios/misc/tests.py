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


class MiscTestCase(unittest.TestCase):

    def setUp(self):
        from adagios.settings import nagios_config
        self.nagios_config = nagios_config

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

