#!/usr/bin/env python

import os

from distutils.core import setup
from distutils.command.build import build
from distutils.sysconfig import get_python_lib
from adagios import __version__

app_name = 'adagios'
version = __version__


def get_filelist(path):
    """Returns a list of all files in a given directory"""
    files = []
    directories_to_check = [path]
    while len(directories_to_check) > 0:
        current_directory = directories_to_check.pop(0)
        for i in os.listdir(current_directory):
            if i == '.gitignore':
                continue
            relative_path = current_directory + "/" + i
            if os.path.isfile(relative_path):
                files.append(relative_path)
            elif os.path.isdir(relative_path):
                directories_to_check.append(relative_path)
            else:
                print "what am i?", i
    return files

template_files = get_filelist('adagios')
data_files = map(lambda x: x.replace('adagios/', '', 1), template_files)


class adagios_build(build):
    def run(self):
        # Normal build:
        build.run(self)

        # Custom build steps:
        adagios_conf_lines = []
        site_packages_str = '/usr/lib/python2.7/site-packages'
        # Python 2.4 compatibility
        conf_r = open('build/lib/adagios/apache/adagios.conf', 'r')
        try:
            for line in conf_r.readlines():
                adagios_conf_lines.append(line.replace(site_packages_str, get_python_lib()))
        finally:
            conf_r.close()
        conf_w = open('build/lib/adagios/apache/adagios.conf', 'w')
        try:
            for line in adagios_conf_lines:
                conf_w.write(line)
        finally:
            conf_w.close()

setup(name=app_name,
    version=version,
    description='Web Based Nagios Configuration',
    author='Pall Sigurdsson, Tomas Edwardsson',
    author_email='palli@opensource.is',
    url='https://adagios.opensource.is/',
    packages=['adagios'],
    package_data={'adagios': data_files},
    requires=['django', 'pynag'],
    cmdclass=dict(build=adagios_build),

)
