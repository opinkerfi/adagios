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

