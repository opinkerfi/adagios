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

""" Authorization related stuff in Adagios

"""

import adagios.status.utils
import adagios.views

auditors = []
operators = []
administrators = []

# administrator belongs to all the other groups
administrators += operators + auditors

access_list = list()

# Explicitly grant configuration access only to admins
access_list.append(('adagios.objectbrowser', "administrators"))
access_list.append(('adagios.okconfig_', "administrators"))
access_list.append(('adagios.misc.helpers', "administrators"))
access_list.append(('adagios.misc.views.settings', "administrators"))

access_list.append(('adagios.misc.views.gitlog', "administrators"))
access_list.append(('adagios.misc.views.service', "administrators"))
access_list.append(('adagios.rest.status.edit', "administrators"))
access_list.append(('adagios.status.views.contact', "administrators"))
access_list.append(('adagios.status.views.state_history', "administrators"))
access_list.append(('adagios.status.views.log', "administrators"))
access_list.append(('adagios.status.views.servicegroup', "administrators"))
access_list.append(('adagios.rest.status.state_history', "administrators"))
access_list.append(('adagios.rest.status.top_alert_producers', "administrators"))
access_list.append(('adagios.rest.status.update_check_command', "administrators"))
access_list.append(('adagios.rest.status.log_entries', "administrators"))



# Access to rest interface
access_list.append(('adagios.rest.views', "everyone"))
access_list.append(('adagios.rest.status', "everyone"))
access_list.append(('adagios.misc.rest', "everyone"))


# These modules should more or less be considered "safe"
access_list.append(('django.views.static', "everyone"))
access_list.append(('django.views.i18n', "everyone"))
access_list.append(('adagios.views', "everyone"))
access_list.append(('adagios.status', "everyone"))
access_list.append(('adagios.pnp', "everyone"))
access_list.append(('adagios.contrib', "everyone"))
access_list.append(('adagios.bi.views.index', "everyone"))
access_list.append(('adagios.bi.views.view', "everyone"))
access_list.append(('adagios.bi.views.json', "everyone"))
access_list.append(('adagios.bi.views.graphs_json', "everyone"))
access_list.append(('adagios.misc.helpers.needs_reload', "everyone"))


# If no other rule matches, assume administrators have access
access_list.append(('', "administrators"))


def check_access_to_path(request, path):
    """ Raises AccessDenied if user does not have access to path

    path in this case is a full path to a python module name for example: "adagios.objectbrowser.views.index"
    """
    for search_path, role in access_list:
        if path.startswith(search_path):
            if has_role(request, role):
                return None
            else:
                user = request.META.get('REMOTE_USER', 'anonymous')
                message = "You do not have permission to access %s" % (path, )
                raise adagios.exceptions.AccessDenied(user, access_required=role, message=message, path=path)
    else:
        return None


def has_access_to_path(request, path):
    """ Returns True/False if user in incoming request has access to path

     Arguments:
        path  -- string describing a path to a method or module, example: "adagios.objectbrowser.views.index"
    """
    for search_path, role in access_list:
        if path.startswith(search_path):
            return has_role(request, role)
    else:
        return False


def has_role(request, role):
    """ Returns true if the username in current request has access to a specific role """
    user = request.META.get('REMOTE_USER', "anonymous")

    # Allow if everyone is allowed access
    if role == 'everyone':
        return True

    # Deny if nobody is allowed access
    if role == 'nobody':
        return False

    # Allow if role is "contacts" and user is in fact a valid contact
    if role == 'contacts' and adagios.status.utils.get_contacts(None, name=user):
        return True

    # Allow if role is "users" and we are in fact logged in
    if role == 'users' and user != "anonymous":
        return True

    users_and_groups = globals().get(role, None)
    if hasattr(adagios.settings, role):
        for i in str(getattr(adagios.settings, role)).split(','):
            i = i.strip()
            if i not in users_and_groups:
                users_and_groups.append(i)


    # Deny if no role exists with this name
    if not users_and_groups:
        return False

    # Allow if user is mentioned in your role
    if user in users_and_groups:
        return True

    # If it is specifically stated that "everyone" belongs to the group
    if "everyone" in users_and_groups:
        return True

    # Check if user belongs to any contactgroup that has access
    contactgroups = adagios.status.utils.get_contactgroups(None, 'Columns: name', 'Filter: members >= %s' % user)

    # Allow if we find user belongs to one contactgroup that has this role
    for contactgroup in contactgroups:
        if contactgroup['name'] in users_and_groups:
            return True

    # If we get here, the user clearly did not have access
    return False


def check_role(request, role):
    """ Raises AccessDenied if user in request does not have access to role """
    if not has_role(request, role):
        user = request.META.get('REMOTE_USER', 'anonymous')
        message = "User does not have the required role"
        raise adagios.exceptions.AccessDenied(username=user, access_required=role, message=message)


class AuthorizationMiddleWare(object):
    """ Django MiddleWare class. It's responsibility is to check if an adagios user has access

    if user does not have access to a given view, it is given a 403 error.
    """
    def process_request(self, request):
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not adagios.settings.enable_authorization:
            return None

        function_name = view_func.__name__
        module_name = view_func.__module__
        if module_name == "adagios.rest.views" and function_name == 'handle_request':
            module_name = view_kwargs['module_path']
            function_name = view_kwargs['attribute']

        try:
            path = module_name + '.' + function_name
            check_access_to_path(request, path)
        except adagios.exceptions.AccessDenied, e:
            return adagios.views.http_403(request, exception=e)
