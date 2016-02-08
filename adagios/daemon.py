# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Tomas Edwardsson <tommi@tommi.org>
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

"""Methods for controlling and getting status of the Nagios daemon"""

from pynag.Control import daemon
from adagios import settings

class Daemon(daemon):
    def __init__(self):
        super(Daemon, self).__init__()

        # Mapping needed
        if settings.nagios_binary:
            self.nagios_bin = settings.nagios_binary
        if settings.nagios_config:
            self.nagios_cfg = settings.nagios_config
        if settings.nagios_init_script:
            self.nagios_init = settings.nagios_init_script
        if settings.nagios_service:
            self.service_name = settings.nagios_service

# vim: sts=4 expandtab autoindent
