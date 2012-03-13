#!/usr/bin/env python

import os

from distutils.core import setup
from distutils.sysconfig import get_python_lib

pkgs_path = get_python_lib()
app_name = 'adagios'

def get_filelist(path):
	"""Returns a list of all files in a given directory"""
	files = []
	directories_to_check = [path]
	while len(directories_to_check) > 0:
		current_directory = directories_to_check.pop(0)
		for i in os.listdir(current_directory):
			if i == '.gitignore': continue
			relative_path = current_directory + "/" + i
			if os.path.isfile(relative_path): files.append(relative_path)
			elif os.path.isdir(relative_path): directories_to_check.append(relative_path)
			else: print "what am i?", i
	return files

template_files = get_filelist('adagios')
data_files = map(lambda x: x.replace('adagios/',''), template_files)

setup(name=app_name,
    version='1.0',
    description='Adagios web-configuration front-end to NAgios',
    author='Pall Sigurdsson, Tomas Edwardsson',
    author_email='palli@opensource.is',
    url='https://adagios.opensource.is/',
    packages=['adagios'],
    package_data={'adagios': data_files }

)
