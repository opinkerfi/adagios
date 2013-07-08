import adagios.settings
from os import walk
import re


def get_pagelist(request):
    """ Returns a list of custom pages that are available.

     The pagelist is a relative path to all files in the
     adagios.settings.extra_pages directory
    """
    pages_dir = adagios.settings.extra_pages
    pagelist = []
    for directory, dirnames, filenames in walk(pages_dir):
        for f in filenames:
            filename = directory + "/" + f
            pagelist.append(filename)
    # Change the full path to files into relative paths
    pagelist = map(lambda x: re.sub(pages_dir + '/', '', x), pagelist)
    return pagelist
