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

""" Exceptions that Adagios uses and raises
"""


class AdagiosError(Exception):
    """ Base Class for all Adagios Exceptions """
    pass


class AccessDenied(AdagiosError):
    """ This exception is raised whenever a user tries to access a page he does not have access to. """
    def __init__(self, username, access_required, message, path=None, *args, **kwargs):
        self.username = username
        self.access_required = access_required
        self.message = message
        self.path = path
        super(AccessDenied, self).__init__(message, *args, **kwargs)
