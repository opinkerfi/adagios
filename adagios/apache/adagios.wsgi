import os
import sys
from distutils.sysconfig import get_python_lib

pkgs_path = get_python_lib()
app_name = 'adagios'

path = '%s/%s' % (pkgs_path, app_name)
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' % app_name

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

