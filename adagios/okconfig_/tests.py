# -*- coding: utf-8 -*-

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