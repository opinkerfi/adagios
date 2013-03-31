# -*- coding: utf-8 -*-
#
# Utility functions for the status app. These are mostly used by adagios.status.views

import pynag.Utils
import pynag.Parsers
from collections import defaultdict

state = defaultdict(lambda: "unknown")
state[0] = "ok"
state[1] = "warning"
state[2] = "critical"

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
        q = kwargs['q']
        del kwargs['q']
    else:
        q = None
    arguments = pynag.Utils.grep_to_livestatus(*args,**kwargs)

    if not fields is None:
    # fields should be a list, lets create a Column: query for livestatus
        if isinstance(fields, (str,unicode) ):
            fields = fields.split(',')
        if len(fields) > 0:
            argument = 'Columns: %s' % ( ' '.join(fields))
            arguments.append(argument)
    livestatus = pynag.Parsers.mk_livestatus()
    result = livestatus.get_hosts(*arguments)

    # Add statistics to every hosts:
    for host in result:
        host['num_problems'] = host['num_services_crit'] +  host['num_services_warn'] +  host['num_services_unknown']
        host['children'] = host['services_with_state']
        host['status'] = state[host['state']]

        ok = host.get('num_services_ok')
        warn = host.get('num_services_warn')
        crit = host.get('num_services_crit')
        pending = host.get('num_services_pending')
        unknown = host.get('num_services_unknown')
        total = ok + warn + crit +pending + unknown
        host['total'] = total
        host['problems'] = warn + crit + unknown
        try:
            total = float(total)
            host['health'] = float(ok) / total * 100.0
            host['percent_ok'] = ok/total*100
            host['percent_warn'] = warn/total*100
            host['percent_crit'] = crit/total*100
            host['percent_unknown'] = unknown/total*100
            host['percent_pending'] = pending/total*100
        except ZeroDivisionError:
            host['health'] = 'n/a'

    # Sort by service status
    result.sort(reverse=True, cmp=lambda a,b: cmp(a['num_problems'], b['num_problems']))
    return result


def get_services(request=None, tags=None, fields=None, *args,**kwargs):
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
        q = kwargs['q']
        del kwargs['q']
    else:
        q = None
    arguments = pynag.Utils.grep_to_livestatus(*args,**kwargs)

    if not fields is None:
    # fields should be a list, lets create a Column: query for livestatus
        if isinstance(fields, (str,unicode) ):
            fields = fields.split(',')
        if len(fields) > 0:
            argument = 'Columns: %s' % ( ' '.join(fields))
            arguments.append(argument)
    livestatus = pynag.Parsers.mk_livestatus()
    result = livestatus.get_services(*arguments)


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
            result = pynag.Utils.grep(result,tags__contains=tags)
    except Exception, e:
        pass
    return result

def get_statistics(request):
    """ Return a list of dict. That contains various statistics from mk_livestatus (like service totals and host totals)
    """
    c = {}
    l = pynag.Parsers.mk_livestatus()
    c['service_totals'] = l.query('GET services', 'Stats: state = 0', 'Stats: state = 1', 'Stats: state = 2','Stats: state = 3',)
    c['host_totals'] = l.query('GET hosts', 'Stats: state = 0', 'Stats: state = 1', 'Stats: state = 2',)
    c['service_totals_percent'] = map(lambda x: float(100.0 * x / sum(c['service_totals'])), c['service_totals'])
    c['host_totals_percent'] = map(lambda x: float(100.0 * x / sum(c['host_totals'])), c['host_totals'])

    c['total_hosts'] = sum(c['host_totals'])
    c['total_services'] = sum(c['service_totals'])
    c['unhandled_services'] = l.query('GET services',
                                            'Filter: acknowledged = 0',
                                            'Filter: scheduled_downtime_depth = 0',
                                            'Filter: host_state = 0',
                                            'Stats: state > 0',
    )[0]
    c['unhandled_hosts'] = l.query('GET hosts',
                                         'Filter: acknowledged = 0',
                                         'Filter: scheduled_downtime_depth = 0',
                                         'Stats: state > 0',
                                         )[0]
    tmp = l.query('GET hosts',
                     'Filter: acknowledged = 0',
                     'Filter: scheduled_downtime_depth = 0',
                     'Filter: childs = ',
                     'Stats: state >= 0',
                     'Stats: state > 0',
                     )
    print tmp
    c['total_network_parents'], c['total_network_problems'] = tmp
    return c