# -*- coding: utf-8 -*-

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

    def TestSettings(self):
        self._testPageLoad('/misc/settings')
