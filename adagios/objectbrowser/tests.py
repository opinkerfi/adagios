# -*- coding: utf-8 -*-

from django.utils import unittest
from django.test.client import Client

import pynag.Model
import adagios.settings
pynag.Model.cfg_file = adagios.settings.nagios_config


class TestObjectBrowser(unittest.TestCase):

    def testNagiosConfigFile(self):
        result = pynag.Model.ObjectDefinition.objects.all
        config = pynag.Model.config.cfg_file
        self.assertGreaterEqual(
            len(result), 0, msg="Parsed nagios.cfg, but found no objects, are you sure this is the right config file (%s) ? " % config)

    def testIndexPage(self):
        c = Client()
        response = c.get('/objectbrowser/')
        self.assertEqual(response.status_code, 200)
