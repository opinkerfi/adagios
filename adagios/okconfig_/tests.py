# -*- coding: utf-8 -*-

from django.utils import unittest
from django.test.client import Client

import okconfig
import adagios.settings

okconfig.cfg_file = adagios.settings.nagios_config


class TestOkconfig(unittest.TestCase):

    def testOkconfigVerifies(self):
        result = okconfig.verify()
        for k, v in result.items():
            self.assertTrue(v, msg="Failed on test: %s" % k)

    def testIndexPage(self):
        c = Client()
        response = c.get('/okconfig/verify_okconfig')
        self.assertEqual(response.status_code, 200)
