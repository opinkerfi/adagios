# -*- coding: utf-8 -*-

import os

from django.utils import unittest
from django.test.client import Client

import pynag.Parsers

import tempfile
import os
from adagios.contrib import get_template_name
import pynag.Utils


class ContribTests(unittest.TestCase):
    def setUp(self):
        base_path = tempfile.mkdtemp()
        self.base_path = base_path

    def tearDown(self):
        command = ['rm', '-rf', self.base_path]
        pynag.Utils.runCommand(command=command, shell=False)

    def testGetTemplateFilename(self):
        base_path = self.base_path

        file1 = base_path + '/file1'
        dir1 = base_path + '/dir1'
        file2 = dir1 + '/file2'

        open(file1, 'w').write('this is file1')
        os.mkdir(dir1)
        open(file2, 'w').write('this is file2')

        self.assertEqual(file1, get_template_name(base_path, 'file1'))
        self.assertEqual(file2, get_template_name(base_path, 'dir1', 'file2'))
        self.assertEqual(file2, get_template_name(base_path, 'dir1', 'file2', 'unneeded_argument'))

        # Try to return a filename that is outside base_path
        exception1 = lambda: get_template_name(base_path, '/etc/passwd')
        self.assertRaises(Exception, exception1)

        # Try to return a filename that is outside base_path
        exception2 = lambda: get_template_name(base_path, '/etc/', 'passwd')
        self.assertRaises(Exception, exception2)

        # Try to return a filename that is outside base_path
        exception3 = lambda: get_template_name(base_path, '..', 'passwd')
        self.assertRaises(Exception, exception3)





