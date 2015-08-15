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


# A special keyword that can be added to some filters to look specifically for 'unhandled' problems.
_UNHANDLED = 'unhandled'


# This key is often passed via querystring as a means to do a 'fuzzy' search of an object.
_SEARCH_KEYWORD = 'q'

# This keyword is used to define how many rows the we should return
_LIMIT_KEYWORD = 'limit'

# This is a common querystring key to filter for hosts/services in downtime.
_IN_SCHEDULED_DOWNTIME = 'in_scheduled_downtime'


# How we map from _IN_SCHEDULED_DOWNTIME querystring to something that livestatus understands
_IN_SCHEDULED_DOWNTIME_MAP = {
    '0': {'scheduled_downtime_depth': '0'},
    '1': {'scheduled_downtime_depth__gt': '0'},
}


_DEFAULT_SERVICE_COLUMNS = [
    'host_name', 'description', 'plugin_output', 'last_check', 'host_state',
    'state', 'scheduled_downtime_depth', 'last_state_change', 'acknowledged',
    'downtimes', 'host_downtimes', 'comments_with_info',
]


_DEFAULT_HOST_COLUMNS = [
    'name', 'plugin_output', 'last_check', 'state', 'services', 'downtimes',
    'last_state_change', 'acknowledged', 'parents', 'childs',  'address',
    'comments_with_info', 'scheduled_downtime_depth', 'num_services_crit',
    'num_services_warn', 'num_services_unknown', 'num_services_ok',
    'num_services_pending', 'services_with_info', 'services_with_state',
]


# Use these fields when making a generic search for hosts
_GENERIC_SEARCH_FIELDS_HOST = [
    'name__contains', 'address__contains', 'plugin_output__contains', 'alias__contains']


# Use these fields when making a generic search for services
_GENERIC_SEARCH_FIELDS_SERVICE = [
    'host_name__contains', 'description__contains', 'plugin_output__contains', 'host_address__contains']

# Name of service description attribute
_ATTRIBUTE_DESCRIPTION = 'description'


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


def add_statistics_to_hosts(result):
    # Add statistics to every hosts:
    for host in result:
        try:
            host['num_problems'] = host['num_services_crit'] + \
                                   host['num_services_warn'] + host['num_services_unknown']
            host['children'] = host['services_with_state']

            # We are inventing a state=3 here for hosts to mean pending host.
            # We are working around a bug where unchecked hosts are assumed to be up.
            # We need to check both last_state_change and last_check because those
            # variables behave differently depending on if host has services or a
            # check command defined.
            # TODO: Remove this hack from here and into the frontend.
            if host.get('last_state_change') == 0 and host.get('last_check') == 0:
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


def _search_multiple_attributes(search_query, attributes, value):
    """Adds search filter to search_query that allows searching for multiple attributes.

    Args:
        search_query: pynag.Parsers.LivestatusQuery object. Filters will be adde to this search_query.
        attributes: List of strings. All the fields we want to search in.
        value: String. Value we want to search for.
    """
    for attribute in attributes:
        search_query.add_filter(attribute, value)
    if len(attributes) > 1:
        search_query.add_or_statement(len(attributes))


def _process_querystring_for_host(*args, **kwargs):
    """Take querystring from django and turn into a livestatus query.

    Note:
        This functions does preproccessing of querystring and turns
        it into a nice livestatus query. We support a few extra keywords
        for example:

        _SEARCH_KEYWORD will be turned into a fuzzy search
        _UNHANDLED keyword will make the query only look at unhandled host problems
        _IN_SCHEDULED_DOWNTIME keyword will look only for objects in scheduled downtime


    Args:
        *args: List of strings. Will be passed directly to LivestatusQuery
        **kwargs: {'str':['str']}. Querystring arguments, will be transformed
            into a valid livestatus query.

    Returns:
        pynag.Parsers.LivestatusQuery a valid livestatus query.
    """
    # By default the search dialog in adagios does a 'fuzzy search' of several fields
    # Lets extract it from our query, so we don't confuse livestatus.
    search_parameter = kwargs.pop(_SEARCH_KEYWORD, None)

    # If the unhandled keyword appears in our querystring, we automatically add
    # some search filters:
    if kwargs.pop(_UNHANDLED, False):
        kwargs.update(adagios.settings.UNHANDLED_HOSTS)

    # If _IN_SCHEDULED_DOWNTIME querystring is applied, we have to transmute it
    # To a different query that livestatus understands:
    in_scheduled_downtime = kwargs.pop(_IN_SCHEDULED_DOWNTIME, False)
    if in_scheduled_downtime:
        if isinstance(in_scheduled_downtime, list):
            in_scheduled_downtime = in_scheduled_downtime[0]
        kwargs.update(_IN_SCHEDULED_DOWNTIME_MAP[in_scheduled_downtime])

    # There are some views out there that look for both hosts and services.
    # Lets purposefully ignore attributes that we know exist for services only
    kwargs.pop(_ATTRIBUTE_DESCRIPTION, None)

    if 'host_state' in kwargs:
        kwargs['state'] = kwargs.pop('host_state')

    query = pynag.Parsers.LivestatusQuery('GET hosts', *args, **kwargs)

    if search_parameter:
        if isinstance(search_parameter, list):
            search_parameter = search_parameter[0]
        _search_multiple_attributes(query, _GENERIC_SEARCH_FIELDS_HOST, search_parameter)

    return query


def _get_limit_from_kwargs(kwargs):
    """Remove _LIMIT from kwargs if present, and convert to int.

    Returns:
        Integer. 'limit' if it was inside kwargs, otherwise adagios.settings.livestatus_limit
    """
    limit = kwargs.pop(_LIMIT_KEYWORD, adagios.settings.livestatus_limit)
    if isinstance(limit, list):
        limit = limit[0]
    limit = int(limit)
    return limit


def get_hosts(request, fields=None, *args, **kwargs):
    """ Get a list of hosts from mk_livestatus

     This is a wrapper around pynag.Parsers.mk_livestatus().query()

     Arguments:
        request: Django request object
        fields: List of strings. Which fields should be present in our response. If undefined, use _DEFAULT_HOST_FIELDS

        *args will be passed directly to livestatus
        **kwargs passed in will be converted to livestatus 'Filter:' strings

    Returns:
        List of dicts. The output from livestatus query.
    """
    limit = _get_limit_from_kwargs(kwargs)
    query = _process_querystring_for_host(*args, **kwargs)
    if limit:
        query.set_limit(limit)
    else:
        query.remove_limit()

    if fields is None:
        fields = _DEFAULT_HOST_COLUMNS

    # fields should be a list, lets create a Column: query for livestatus
    if isinstance(fields, (str, unicode)):
        fields = fields.split(',')

    query.set_columns(*fields)
    l = livestatus(request)
    hosts = l.query(query)

    add_statistics_to_hosts(hosts)
    
    hosts.sort(reverse=True, cmp=lambda a, b: cmp(a.get('num_problems'), b.get('num_problems')))
    hosts.sort(reverse=True, cmp=lambda a, b: cmp(a.get('state'), b.get('state')))

    if limit:
        return hosts[:limit]
    return hosts


def _process_querystring_for_service(*args, **kwargs):
    """Take querystring from django and turn into a livestatus query.

    Note:
        This functions does preproccessing of querystring and turns
        it into a nice livestatus query. We support a few extra keywords
        for example:

        _SEARCH_KEYWORD will be turned into a fuzzy search
        _UNHANDLED keyword will make the query only look at unhandled service
        _IN_SCHEDULED_DOWNTIME keyword will look only for objects in scheduled downtime


    Args:
        *args: List of strings. Will be passed directly to LivestatusQuery
        **kwargs: {'str':['str']}. Querystring arguments, will be transformed
            into a valid livestatus query.

    Returns:
        pynag.Parsers.LivestatusQuery a valid livestatus query.
    """

    # By default the search dialog in adagios does a 'fuzzy search' of several fields
    # Lets extract it from our query, so we don't confuse livestatus.
    search_parameter = kwargs.pop(_SEARCH_KEYWORD, None)

    # If the unhandled keyword appears in our querystring, we automatically add
    # some search filters:
    if kwargs.pop(_UNHANDLED, False):
        kwargs.update(adagios.settings.UNHANDLED_SERVICES)

    # If _IN_SCHEDULED_DOWNTIME querystring is applied, we have to transmute it
    # To a different query that livestatus understands:
    in_scheduled_downtime = kwargs.pop(_IN_SCHEDULED_DOWNTIME, False)
    if in_scheduled_downtime:
        if isinstance(in_scheduled_downtime, list):
            in_scheduled_downtime = in_scheduled_downtime[0]
        kwargs.update(_IN_SCHEDULED_DOWNTIME_MAP[in_scheduled_downtime])

    query = pynag.Parsers.LivestatusQuery('GET services', *args, **kwargs)

    if search_parameter:
        if isinstance(search_parameter, list):
            search_parameter = search_parameter[0]
        search_parameter = search_parameter.encode('utf-8')
        query.add_filters(host_name__contains=search_parameter)
        query.add_filters(description__contains=search_parameter)
        query.add_filters(plugin_output__contains=search_parameter)
        query.add_filters(host_address__contains=search_parameter)
        query.add_header_line('Or: 4')

    return query


def get_services(request=None, fields=None, *args, **kwargs):
    """ Get a list of services from Livestatus.

        This is a wrapper around pynag.Parsers.Livestatus.query()

        Arguments:
            requests: Django request object.
            fields: List of strings. If defined, collect these specific columns from livestatus. Otherwise a
              sane default from _DEFAULT_SERVICE_COLUMNS will be returned.
            *args will be passed directly to livestatus
            **kwargs passed in will be converted to livestatus 'Filter:' strings

        Returns:
            List of dicts. The output from livestatus query.
    """
    limit = _get_limit_from_kwargs(kwargs)
    query = _process_querystring_for_service(*args, **kwargs)
    if limit:
        query.set_limit(limit)
    else:
        query.remove_limit()

    fields = fields or _DEFAULT_SERVICE_COLUMNS
    if not isinstance(fields, list):  # HACK, we still have web rest queries that reference us like this
        fields = fields.split()
    query.set_columns(*fields)

    l = livestatus(request)
    services = l.query(query)

    # TODO: Can we get rid of this function in the future and workaround this another way ?
    _add_custom_tags_to_services(services)

    if limit:
        return services[:limit]
    return services


def _add_custom_tags_to_services(services):
    """Add custom tags like 'unhandled' or 'problem' to a list of services.

    Args:
        services. List of dict. Usually the output from a livestatus query.

    """
    # Add custom tags to our service list
    try:
        for service in services:
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
    except Exception:
        pass
    return services


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


def get_log_entries(request, *args, **kwargs):
    """ Get log entries via pynag.Utils.LogFiles

    Returns:
        Log entries that matches the search query in (list of dict)
    """
    if not adagios.settings.enable_local_logs:
        return []
    log = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config)
    return log.get_log_entries(*args, **kwargs)


def get_state_history(request, *args, **kwargs):
    """ Get state history via pynag.Utils.LogFiles

    Returns:
        Log entries that matches the search query in (list of dict)
    """
    if not adagios.settings.enable_local_logs:
        return []
    log = pynag.Parsers.LogFiles(maincfg=adagios.settings.nagios_config)
    return log.get_state_history(*args, **kwargs)
