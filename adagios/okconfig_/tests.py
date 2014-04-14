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

import okconfig
import adagios.settings

okconfig.cfg_file = adagios.settings.nagios_config


class TestOkconfig(unittest.TestCase):

    def testOkconfigVerifies(self):
        result = okconfig.verify()
        for k, v in result.items():
            self.assertTrue(v, msg=_("Failed on test: %s") % k)

    def testIndexPage(self):
        c = Client()
        response = c.get('/okconfig/verify_okconfig')
        self.assertEqual(response.status_code, 200)

    def testPageLoad(self):
        """ Smoketest for the okconfig views """
        self.loadPage('/okconfig/addhost')
        self.loadPage('/okconfig/scan_network')
        self.loadPage('/okconfig/addgroup')
        self.loadPage('/okconfig/addtemplate')
        self.loadPage('/okconfig/addhost')
        self.loadPage('/okconfig/addservice')
        self.loadPage('/okconfig/install_agent')
        self.loadPage('/okconfig/edit')
        self.loadPage('/okconfig/edit/localhost')
        self.loadPage('/okconfig/verify_okconfig')
    def loadPage(self, url):
        """ Load one specific page, and assert if return code is not 200 """
        try:
            c = Client()
            response = c.get(url)
            self.assertEqual(response.status_code, 200, _("Expected status code 200 for page %s") % url)
        except Exception, e:
            self.assertEqual(True, _("Unhandled exception while loading %(url)s: %(e)s") % {'url': url, 'e': e})
