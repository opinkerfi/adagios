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

import pynag.Model
import adagios.settings
pynag.Model.cfg_file = adagios.settings.nagios_config


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
