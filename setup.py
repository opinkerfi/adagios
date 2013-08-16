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

        # We drop in a config file for apache and we modify
        # that config file to represent python path on the host
        # building
        site_packages_str = '/usr/lib/python2.7/site-packages'
        python_lib = get_python_lib()

        # If we happen to be running on python 2.7, there is nothing more
        # to do.
        if site_packages_str == python_lib:
            return

        apache_config_file = None
        for dirpath, dirname, filenames in os.walk('build'):
            if dirpath.endswith('apache') and 'adagios.conf' in filenames:
                apache_config_file = os.path.join(dirpath, 'adagios.conf')
        # If build process did not create any config file, we have nothing more to do
        if not apache_config_file:
            return

        # Replace the python path with actual values
        try:
            contents = open(apache_config_file, 'r').read()
            contents = contents.replace(site_packages_str, python_lib)
            open(apache_config_file, 'w').write(contents)
        finally:
            pass

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
