# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Pall Sigurdsson <palli@opensource.is>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from django.utils.translation import ugettext as _

def get_template_name(base_path, *args):
    """ Return a full path to a template named base_path/args[0]

    If multiple arguments are provided, treat them as recursive directories, but
    if a valid filename is found, return immediately.

    if base_path is not provided, use adagios.settings.contrib_dir
    """
    if not base_path:
        base_path = adagios.settings.contrib_dir
    path = base_path
    for i in args:
        if not i:
            continue
        path = os.path.join(path, i)
        path = os.path.normpath(path)

        if not path.startswith(base_path):
            raise Exception(_("'%(path)s' is outside contrib dir") % {'path': path})
        elif os.path.isdir(path):
            continue
        elif os.path.isfile(path):
            return path
    return path
