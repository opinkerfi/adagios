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

    def TestPageLoads(self):
        """ Smoke test views in /misc/
        """
        self.loadPage("/misc/settings")
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