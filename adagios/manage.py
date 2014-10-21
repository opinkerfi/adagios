#!/usr/bin/python
#
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
import sys

if __name__ == "__main__":
    # Insert PYTHONPATH relative to manage.py
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adagios.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

