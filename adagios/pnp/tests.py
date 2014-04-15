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

import os

from django.utils import unittest
from django.test.client import Client
from django.utils.translation import ugettext as _

import pynag.Parsers
from adagios.settings import nagios_config
from adagios.pnp import functions


class PNP4NagiosTestCase(unittest.TestCase):

    def testPnpIsConfigured(self):
        config = pynag.Parsers.config()
        config.parse_maincfg()
        for k, v in config.maincfg_values:
            if k == "broker_module" and v.find('npcd') > 1:
                tmp = v.split()
                self.assertFalse(
                    len(tmp) < 2, _('We think pnp4nagios broker module is incorrectly configured. In nagios.cfg it looks like this: %s') % v)
                module_file = tmp.pop(0)
                self.assertTrue(
                    os.path.exists(module_file), _('npcd broker_module module not found at "%s". Is nagios correctly configured?') % module_file)

                config_file = None
                for i in tmp:
                    if i.startswith('config_file='):
                        config_file = i.split('=', 1)[1]
                        break
                self.assertIsNotNone(
                    config_file, _("npcd broker module has no config_file= argument. Is pnp4nagios correctly configured?"))
                self.assertTrue(
                    os.path.exists(config_file), _('PNP4nagios config file was not found (%s).') % config_file)
                return
        self.assertTrue(
            False, _('Nagios Broker module not found. Is pnp4nagios installed and configured?'))

    def testGetJson(self):
        result = functions.run_pnp('json')
        self.assertGreaterEqual(
            len(result), 0, msg=_("Tried to get json from pnp4nagios but result was improper"))

    def testPageLoad(self):
        c = Client()
        response = c.get('/pnp/json')
        self.assertEqual(response.status_code, 200)
