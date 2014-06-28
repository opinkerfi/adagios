# -*- coding: utf-8 -*-
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
#
# Utility functions for the status app. These are mostly used by
# adagios.status.views

import pynag.Utils
import pynag.Parsers
import adagios.settings
from adagios.misc.rest import add_notification, clear_notification
import simplejson as json

from collections import defaultdict
from adagios import userdata

state = defaultdict(lambda: "unknown")
state[0] = "ok"
state[1] = "warning"
state[2] = "critical"

def get_all_backends():
    # TODO: Properly support multiple instances, using split here is not a good idea
    backends = adagios.settings.livestatus_path or ''
    backends = backends.split(',')
    backends = map(lambda x: x.strip(), backends)
    return backends


def livestatus(request):
    """ Returns a new pynag.Parsers.mk_livestatus() object with authauser automatically set from request.META['remoteuser']
    """

    if request is None:
        authuser = None
    elif adagios.settings.enable_authorization and not adagios.auth.has_role(request, 'administrators') and not adagios.auth.has_role(request, 'operators'):
        authuser = request.META.get('REMOTE_USER', None)
    else:
        authuser = None
    
    backends = get_all_backends()
    # we remove the disabled backends
    if backends is not None:
        try:
            user = userdata.User(request)
            if user.disabled_backends is not None:
                backends = filter(lambda x: x not in user.disabled_backends, backends)
            clear_notification("userdata problem")
        except Exception as e:
            message = "%s: %s" % (type(e), str(e))
            add_notification(level="warning", notification_id="userdata problem", message=message)

    livestatus = pynag.Parsers.MultiSite(
        nagios_cfg_file=adagios.settings.nagios_config,
        livestatus_socket_path=adagios.settings.livestatus_path,
        authuser=authuser)
    
    for i in backends:
        livestatus.add_backend(path=i, name=i)
    
    return livestatus


def query(request, *args, **kwargs):
    """ Wrapper around pynag.Parsers.mk_livestatus().query(). Any authorization logic should be performed here. """
    l = livestatus(request)
    return l.query(*args, **kwargs)


def get_hostgroups(request, *args, **kwargs):
    """ Get a list of hostgroups from mk_livestatus
    """
    l = livestatus(request)
    return l.get_hostgroups(*args, **kwargs)


def get_hosts(request, tags=None, fields=None, *args, **kwargs):
    """ Get a list of hosts from mk_livestatus

     This is a wrapper around pynag.Parsers.mk_livestatus().query()

     Arguments:
        request  - Not in use
        tags     - Not in use
        fields   - If fields=None, return all columns, otherwise return only the columns provided

        Any *args will be passed directly to livestatus
        Any **kwargs will be converted to livestatus "'Filter:' style strings

     Returns:
        A list of dict (hosts)
    """
    if 'q' in kwargs:
        q = kwargs.get('q')
        del kwargs['q']
        if not isinstance(q, list):
            q = [q]
    else:
        q = []

    # Often search filters include description, which we will skip
    kwargs.pop('description', None)

    if 'host_state' in kwargs:
        kwargs['state'] = kwargs.pop('host_state')

    # If keyword "unhandled" is in kwargs, then we will fetch unhandled
    # hosts only
    if 'unhandled' in kwargs:
        del kwargs['unhandled']
        kwargs['state'] = 1
        kwargs['acknowledged'] = 0
        kwargs['scheduled_downtime_depth'] = 0
        #kwargs['host_scheduled_downtime_depth'] = 0
        #kwargs['host_acknowledged'] = 0

    arguments = pynag.Utils.grep_to_livestatus(*args, **kwargs)
    # if "q" came in from the querystring, lets filter on host_name
    for i in q:
        arguments.append('Filter: name ~~ %s' % i)
        arguments.append('Filter: address ~~ %s' % i)
        arguments.append('Filter: plugin_output ~~ %s' % i)
        arguments.append('Or: 3')
    if fields is None:
        fields = [
            'name', 'plugin_output', 'last_check', 'state', 'services', 'services_with_info', 'services_with_state',
            'parents', 'childs', 'address', 'last_state_change', 'acknowledged', 'downtimes', 'comments_with_info',
            'scheduled_downtime_depth', 'num_services_crit', 'num_services_warn', 'num_services_unknown',
            'num_services_ok', 'num_services_pending']
    # fields should be a list, lets create a Column: query for livestatus
    if isinstance(fields, (str, unicode)):
        fields = fields.split(',')
    if len(fields) > 0:
        argument = 'Columns: %s' % (' '.join(fields))
        arguments.append(argument)
    l = livestatus(request)
    result = l.get_hosts(*arguments)

    # Add statistics to every hosts:
    for host in result:
        try:
            host['num_problems'] = host['num_services_crit'] + \
                host['num_services_warn'] + host['num_services_unknown']
            host['children'] = host['services_with_state']

            if host.get('last_state_change') == 0:
                host['state'] = 3
            host['status'] = state[host['state']]

            ok = host.get('num_services_ok')
            warn = host.get('num_services_warn')
            crit = host.get('num_services_crit')
            pending = host.get('num_services_pending')
            unknown = host.get('num_services_unknown')
            total = ok + warn + crit + pending + unknown
            host['total'] = total
            host['problems'] = warn + crit + unknown
            try:
                total = float(total)
                host['health'] = float(ok) / total * 100.0
                host['percent_ok'] = ok / total * 100
                host['percent_warn'] = warn / total * 100
                host['percent_crit'] = crit / total * 100
                host['percent_unknown'] = unknown / total * 100
                host['percent_pending'] = pending / total * 100
            except ZeroDivisionError:
                host['health'] = 'n/a'
        except Exception:
            pass

    # Sort by host and service status
    result.sort(reverse=True, cmp=lambda a, b: cmp(a.get('num_problems'), b.get('num_problems')))
    result.sort(reverse=True, cmp=lambda a, b: cmp(a.get('state'), b.get('state')))
    return result


def get_services(request=None, tags=None, fields=None, *args, **kwargs):
    """ Get a list of services from mk_livestatus.

        This is a wrapper around pynag.Parsers.mk_livestatus().query()

        Arguments:
            requests - Not in use
            tags     - List of 'tags' that will be passed on as a filter to the services.
                       Example of service tags are: problem, unhandled, ishandled,
            fields   - If fields=None, return all columns, otherwise return only the columns provided.
                       fields can be either a list or a comma seperated string
        Any *args will be passed directly to livestatus

        Any **kwargs passed in will be converted to livestatus 'Filter:' strings

        Examples:
        get_services(host_name='localhost') # same as livestatus.query('GET services','Filter: host_name = localhost')

        get_services('Authuser: admin', host_name='localhost')

    """
    if 'q' in kwargs:
        q = kwargs.get('q')
        del kwargs['q']
    else:
        q = []
    if not isinstance(q, list):
        q = [q]

    # If keyword "unhandled" is in kwargs, then we will fetch unhandled
    # services only
    if 'unhandled' in kwargs:
        del kwargs['unhandled']
        kwargs['state__isnot'] = 0
        kwargs['acknowledged'] = 0
        kwargs['scheduled_downtime_depth'] = 0
        kwargs['host_scheduled_downtime_depth'] = 0
        kwargs['host_acknowledged'] = 0
        kwargs['host_state'] = 0
    arguments = pynag.Utils.grep_to_livestatus(*args, **kwargs)

    # If q was added, it is a fuzzy filter on services
    for i in q:
        arguments.append('Filter: host_name ~~ %s' % i.encode('utf-8'))
        arguments.append('Filter: description ~~ %s' % i.encode('utf-8'))
        arguments.append('Filter: plugin_output ~~ %s' % i.encode('utf-8'))
        arguments.append('Filter: host_address ~~ %s' % i.encode('utf-8'))
        arguments.append('Or: 4')

    if fields is None:
        fields = [
            'host_name', 'description', 'plugin_output', 'last_check', 'host_state', 'state', 'scheduled_downtime_depth',
            'last_state_change', 'acknowledged', 'downtimes', 'host_downtimes', 'comments_with_info']
    # fields should be a list, lets create a Column: query for livestatus
    if isinstance(fields, (str, unicode)):
        fields = fields.split(',')
    if len(fields) > 0:
        argument = 'Columns: %s' % (' '.join(fields))
        arguments.append(argument)
    l = livestatus(request)
    result = l.get_services(*arguments)

    # Add custom tags to our service list
    try:
        for service in result:
            # Tag the service with tags such as problems and unhandled
            service_tags = []
            if service['state'] != 0:
                service_tags.append('problem')
                service_tags.append('problems')
                if service['acknowledged'] == 0 and service['downtimes'] == [] and service['host_downtimes'] == []:
                    service_tags.append('unhandled')
                    service['unhandled'] = "unhandled"
                else:
                    service_tags.append('ishandled')
                    service['handled'] = "handled"
            elif service.get('last_state_change') == 0:
                service['state'] = 3
                service_tags.append('pending')
            else:
                service_tags.append('ok')
            if service['acknowledged'] == 1:
                service_tags.append('acknowledged')
            if service['downtimes'] != []:
                service_tags.append('downtime')
            service['tags'] = ' '.join(service_tags)
            service['status'] = state[service['state']]

        if isinstance(tags, str):
            tags = [tags]
        if isinstance(tags, list):
            result = pynag.Utils.grep(result, tags__contains=tags)
    except Exception:
        pass
    return result


def get_contacts(request, *args, **kwargs):
    l = livestatus(request)
    return l.get_contacts(*args, **kwargs)


def get_contactgroups(request, *args, **kwargs):
    l = livestatus(request)
    return l.get_contactgroups(*args, **kwargs)


def get_statistics(request, *args, **kwargs):
    """ Return a list of dict. That contains various statistics from mk_livestatus (like service totals and host totals)
    """
    c = {}
    l = livestatus(request)
    arguments = pynag.Utils.grep_to_livestatus(*args, **kwargs)

    # Get service totals as an array of [ok,warn,crit,unknown]
    c['service_totals'] = l.get_services(
        'Stats: state = 0',
        'Stats: state = 1',
        'Stats: state = 2',
        'Stats: state = 3',
        *arguments
    ) or [0, 0, 0, 0]

    # Get host totals as an array of [up,down,unreachable]
    c['host_totals'] = l.get_hosts(
        'Stats: state = 0',
        'Stats: state = 1',
        'Stats: state = 2',
        *arguments
    ) or [0, 0, 0]

    # Get total number of host/ host_problems
    c['total_hosts'] = sum(c['host_totals'])
    c['total_host_problems'] = c['total_hosts'] - c['host_totals'][0]

    # Get total number of services/ service_problems
    c['total_services'] = sum(c['service_totals'])
    c['total_service_problems'] = c['total_services'] - c['service_totals'][0]

    # Calculate percentage of hosts/services that are "ok"
    try:
        c['service_totals_percent'] = map(lambda x: float(100.0 * x / c['total_services']), c['service_totals'])
    except ZeroDivisionError:
        c['service_totals_percent'] = [0, 0, 0, 0]
    try:
        c['host_totals_percent'] = map(lambda x: float(100.0 * x / c['total_hosts']), c['host_totals'])
    except ZeroDivisionError:
        c['host_totals_percent'] = [0, 0, 0, 0]
    
    unhandled_services = l.get_services(
        'Stats: state > 0',
        acknowledged=0,
        scheduled_downtime_depth=0,
        host_state=0,
        *arguments
    ) or [0]

    unhandled_hosts = l.get_hosts(
        'Stats: state = 1',
        acknowledged=0,
        scheduled_downtime_depth=0,
        *arguments
    ) or [0]

    c['unhandled_services'] = unhandled_services[0]
    c['unhandled_hosts'] = unhandled_hosts[0]

    total_unhandled_network_problems = l.get_hosts(
        'Filter: childs != ',
        'Stats: state = 1',
        acknowledged=0,
        scheduled_downtime_depth=0,
        *arguments
    ) or [0]
    c['total_unhandled_network_problems'] = total_unhandled_network_problems[0]

    tmp = l.get_hosts(
        'Filter: childs != ',
        'Stats: state >= 0',
        'Stats: state > 0',
        *arguments
    ) or [0, 0]

    c['total_network_parents'], c['total_network_problems'] = tmp
    return c


def grep_to_livestatus(object_type, *args, **kwargs):
    """ Take querystring parameters from django request object, and returns list of livestatus queries

        Should support both hosts and services.

        It does minimal support for views have hosts and services in same view and user wants to
        enter some querystring parameters for both.

    """
    result = []
    for key in kwargs:
        if hasattr(kwargs, 'getlist'):
            values = kwargs.getlist(key)
        else:
            values = [kwargs.get(key)]

        if object_type == 'host' and key.startswith('service_'):
            continue
        if object_type == 'host' and key == 'description':
            continue
        if object_type == 'host' and key in ('host_scheduled_downtime_depth', 'host_acknowledged', 'host_state'):
            key = key[len('host_'):]
        if object_type == 'service' and key in ('service_state', 'service_description'):
            key = key[len('service_'):]

        if object_type == 'service' and key == 'unhandled':
            tmp = {}
            tmp['state__isnot'] = 0
            tmp['acknowledged'] = 0
            tmp['scheduled_downtime_depth'] = 0
            tmp['host_scheduled_downtime_depth'] = 0
            tmp['host_acknowledged'] = 0
            tmp['host_state'] = 0
            result += pynag.Utils.grep_to_livestatus(**kwargs)
        elif object_type == 'host' and key == 'unhandled':
            tmp = {}
            tmp['state__isnot'] = 0
            tmp['acknowledged'] = 0
            tmp['scheduled_downtime_depth'] = 0
        elif object_type == 'host' and key == 'q':
            for i in values:
                result.append('Filter: name ~~ %s' % i)
                result.append('Filter: address ~~ %s' % i)
                result.append('Filter: plugin_output ~~ %s' % i)
                result.append('Or: 3')
        elif object_type == 'service' and key == 'q':
            for i in values:
                result.append('Filter: host_name ~~ %s' % i)
                result.append('Filter: description ~~ %s' % i)
                result.append('Filter: plugin_output ~~ %s' % i)
                result.append('Filter: host_address ~~ %s' % i)
                result.append('Or: 4')
        else:
            for value in values:
                result += pynag.Utils.grep_to_livestatus(**{key: value})

    return list(args) + result

