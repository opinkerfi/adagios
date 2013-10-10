
"""

Convenient stateless functions for the status module. These are meant for programs to interact
with status of Nagios.

"""

import time
import pynag.Control.Command
import pynag.Model
import django.core.mail
import pynag.Utils
import adagios.status.utils
import pynag.Parsers
import collections
from pynag.Utils import PynagError


def hosts(fields=None, *args, **kwargs):
    """ Get List of hosts. Any parameters will be passed straight throught to pynag.Utils.grep()

        Arguments:
            fields -- If specified, a list of attributes to return. If unspecified, all fields are returned.

            Any *args will be passed to livestatus directly
            Any **kwargs will be treated as a pynag.Utils.grep()-style filter
    """
    query = list(args)
    if not fields is None:
        # fields should be a list, lets create a Column: query for livestatus
        if isinstance(fields, (str, unicode)):
            fields = fields.split(',')
        if len(fields) > 0:
            argument = 'Columns: %s' % (' '.join(fields))
            query.append(argument)
    livestatus_arguments = pynag.Utils.grep_to_livestatus(*query, **kwargs)

    livestatus = pynag.Parsers.mk_livestatus()
    hosts = livestatus.get_hosts(*livestatus_arguments)
    return hosts


def services(fields=None, *args, **kwargs):
    """ Similar to hosts(), is a wrapper around adagios.status.utils.get_services()
    """
    return adagios.status.utils.get_services(fields=fields, *args, **kwargs)


def contacts(fields=None, *args, **kwargs):
    """ Wrapper around pynag.Parsers.mk_livestatus.get_contacts()
    """
    l = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    return l.get_contacts(*args, **kwargs)


def emails(*args, **kwargs):
    """ Returns a list of all emails of all contacts
    """
    l = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config)
    return map(lambda x: x['email'], l.get_contacts('Filter: email !='))


def acknowledge(host_name, service_description=None, sticky=1, notify=1, persistent=0, author='adagios', comment='acknowledged by Adagios'):
    """ Acknowledge one single host or service check

    """
    if service_description in (None, '', u'', '_HOST_'):
        pynag.Control.Command.acknowledge_host_problem(host_name=host_name,
                                                       sticky=sticky,
                                                       notify=notify,
                                                       persistent=persistent,
                                                       author=author,
                                                       comment=comment,
                                                       )
    else:
        pynag.Control.Command.acknowledge_svc_problem(host_name=host_name,
                                                      service_description=service_description,
                                                      sticky=sticky,
                                                      notify=notify,
                                                      persistent=persistent,
                                                      author=author,
                                                      comment=comment,
                                                      )


def downtime(host_name, service_description=None, start_time=None, end_time=None, fixed=1, trigger_id=0, duration=7200, author='adagios', comment='Downtime scheduled by adagios', all_services_on_host=False):
    """ Schedule downtime for a host or a service """
    if fixed in (1, '1') and start_time in (None, ''):
        start_time = time.time()
    if fixed in (1, '1') and end_time in (None, ''):
        end_time = int(start_time) + int(duration)
    if all_services_on_host == True:
        return pynag.Control.Command.schedule_host_svc_downtime(
            host_name=host_name,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        )
    elif service_description in (None, '', u'', '_HOST_'):
        return pynag.Control.Command.schedule_host_downtime(
            host_name=host_name,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        )
    else:
        return pynag.Control.Command.schedule_svc_downtime(host_name=host_name,
                                                           service_description=service_description,
                                                           start_time=start_time,
                                                           end_time=end_time,
                                                           fixed=fixed,
                                                           trigger_id=trigger_id,
                                                           duration=duration,
                                                           author=author,
                                                           comment=comment,
                                                           )


def reschedule(host_name, service_description, check_time=time.time(), wait=0):
    """ Reschedule a check of this service/host

    Arguments:
      host_name -- Name of the host
      service_description -- Name of the service check. If left empty, host check will be rescheduled
      check_time -- timestamp of when to execute this check, if left empty, execute right now
      wait -- If set to 1, function will not run until check has been rescheduled
    """
    if check_time is None or check_time is '':
        check_time = time.time()
    if service_description in (None, '', u'', '_HOST_'):
        service_description = ""
        pynag.Control.Command.schedule_forced_host_check(
            host_name=host_name, check_time=check_time)
    else:
        pynag.Control.Command.schedule_forced_svc_check(
            host_name=host_name, service_description=service_description, check_time=check_time)
    if wait == "1":
        livestatus = pynag.Parsers.mk_livestatus()
        livestatus.query("GET services",
                         "WaitObject: %s %s" % (
                             host_name, service_description),
                         "WaitCondition: last_check > %s" % check_time,
                         "WaitTrigger: check",
                         "Filter: host_name = %s" % host_name,
                         )
    return "ok"


def comment(author, comment, host_name, service_description=None, persistent=1):
    """ Adds a comment to a particular service.

    If the "persistent" field is set to zero (0), the comment will be deleted the next time Nagios is restarted.
    Otherwise, the comment will persist across program restarts until it is deleted manually. """

    if service_description in (None, '', u'', '_HOST_'):
        pynag.Control.Command.add_host_comment(
            host_name=host_name, persistent=persistent, author=author, comment=comment)
    else:
        pynag.Control.Command.add_svc_comment(
            host_name=host_name, service_description=service_description, persistent=persistent, author=author, comment=comment)
    return "ok"


def delete_comment(comment_id, host_name, service_description=None):
    """
    """
    if not host_name:
        # TODO host_name is not used here, why do we need it ?
        pass
    if service_description in (None, '', u'', '_HOST_'):
        pynag.Control.Command.del_host_comment(comment_id=comment_id)
    else:
        pynag.Control.Command.del_svc_comment(comment_id=comment_id)
    return "ok"


def edit(object_type, short_name, attribute_name, new_value):
    """ Change one single attribute for one single object.

    Arguments:
      object_type    -- Type of object to change (i.e. "host","service", etc)
      short_name      -- Short Name of the object f.e. the host_name of a host
      attribute_name -- Name of attribute to change .. f.e. 'address'
      new_value      -- New value of the object .. f.e. '127.0.0.1'
    Examples:
      edit('host','localhost','address','127.0.0.1')
      edit('service', 'localhost/Ping', 'contactgroups', 'None')
    """
    # TODO : MK Livestatus access acording to remote_user
    c = pynag.Model.string_to_class[object_type]
    my_obj = c.objects.get_by_shortname(short_name)
    my_obj[attribute_name] = new_value
    my_obj.save()
    return str(my_obj)


def get_map_data(host_name=None):
    """ Returns a list of (host_name,2d_coords). If host_name is provided, returns a list with only that host """
    livestatus = pynag.Parsers.mk_livestatus()
    all_hosts = livestatus.query('GET hosts', )
    hosts_with_coordinates = pynag.Model.Host.objects.filter(
        **{'2d_coords__exists': True})
    hosts = []
    connections = []
    for i in all_hosts:
        name = i['name']
        if host_name in (None, '', name):
            # If x does not have any coordinates, break
            coords = None
            for x in hosts_with_coordinates:
                if x.host_name == name:
                    coords = x['2d_coords']
                    break
            if coords is None:
                continue

            tmp = coords.split(',')
            if len(tmp) != 2:
                continue

            x, y = tmp
            host = {}
            host['host_name'] = name
            host['state'] = i['state']
            i['x_coordinates'] = x
            i['y_coordinates'] = y

            hosts.append(i)

    # For all hosts that have network parents, lets return a proper line for
    # those two
    for i in hosts:
        # Loop through all network parents. If network parent is also in our hostlist
        # Then create a connection between the two
        for parent in i.get('parents'):
            for x in hosts:
                if x.get('name') == parent:
                    connection = {}
                    connection['parent_x_coordinates'] = x.get('x_coordinates')
                    connection['parent_y_coordinates'] = x.get('y_coordinates')
                    connection['child_x_coordinates'] = i.get('x_coordinates')
                    connection['child_y_coordinates'] = i.get('y_coordinates')
                    connection['state'] = i.get('state')
                    connection['description'] = i.get('name')
                    connections.append(connection)
    result = {}
    result['hosts'] = hosts
    result['connections'] = connections
    return result


def change_host_coordinates(host_name, latitude, longitude):
    """ Updates longitude and latitude for one specific host """
    host = pynag.Model.Host.objects.get_by_shortname(host_name)
    coords = "%s,%s" % (latitude, longitude)
    host['2d_coords'] = coords
    host.save()


def autocomplete(q):
    """ Returns a list of {'hosts':[], 'hostgroups':[],'services':[]} matching search query q
    """
    if q is None:
        q = ''
    result = {}
    hosts = pynag.Model.Host.objects.filter(host_name__contains=q)
    services = pynag.Model.Service.objects.filter(
        service_description__contains=q)
    hostgroups = pynag.Model.Hostgroup.objects.filter(
        hostgroup_name__contains=q)
    result['hosts'] = sorted(set(map(lambda x: x.host_name, hosts)))
    result['hostgroups'] = sorted(
        set(map(lambda x: x.hostgroup_name, hostgroups)))
    result['services'] = sorted(
        set(map(lambda x: x.service_description, services)))
    return result


def delete_downtime(downtime_id, is_service=True):
    """ Delete one specific downtime with id that matches downtime_id.

    Arguments:
      downtime_id -- Id of the downtime to be deleted
      is_service  -- If set to True or 1, then this is assumed to be a service downtime, otherwise assume host downtime
    """
    if is_service in (True, 1, '1'):
        return pynag.Control.Command.del_svc_downtime(downtime_id)
    else:
        return pynag.Control.Command.del_host_downtime(downtime_id)


def top_alert_producers(limit=5, start_time=None, end_time=None):
    """ Return a list of ["host_name",number_of_alerts]

     Arguments:
        limit      -- Limit output to top n hosts (default 5)
        start_time -- Search log starting with start_time (default since last log rotation)
    """
    if start_time == '':
        start_time = None
    if end_time == '':
        end_time = None
    l = pynag.Parsers.LogFiles()
    log = l.get_state_history(start_time=start_time, end_time=end_time)
    top_alert_producers = collections.defaultdict(int)
    for i in log:
        if 'host_name' in i and 'state' in i and i['state'] > 0:
            top_alert_producers[i['host_name']] += 1
    top_alert_producers = top_alert_producers.items()
    top_alert_producers.sort(cmp=lambda a, b: cmp(a[1], b[1]), reverse=True)
    if limit > len(top_alert_producers):
        top_alert_producers = top_alert_producers[:int(limit)]
    return top_alert_producers


def log_entries(*args, **kwargs):
    """ Same as pynag.Parsers.Logfiles().get_log_entries()

    Arguments:
   start_time -- unix timestamp. if None, return all entries from today
   end_time -- If specified, only fetch log entries older than this (unix timestamp)
   strict   -- If True, only return entries between start_time and end_time, if False,
            -- then return entries that belong to same log files as given timeset
   search   -- If provided, only return log entries that contain this string (case insensitive)
   kwargs   -- All extra arguments are provided as filter on the log entries. f.e. host_name="localhost"
    Returns:
   List of dicts

    """
    l = pynag.Parsers.LogFiles()
    return l.get_log_entries(*args, **kwargs)


def state_history(start_time=None, end_time=None, host_name=None, service_description=None):
    """ Returns a list of dicts, with the state history of hosts and services. Parameters behaves similar to get_log_entries

    """
    if start_time == '':
        start_time = None
    if end_time == '':
        end_time = None
    if host_name == '':
        host_name = None
    if service_description == '':
        service_description = None

    l = pynag.Parsers.LogFiles()
    return l.get_state_history(start_time=start_time, end_time=end_time, host_name=host_name, service_description=service_description)


def _get_service_model(host_name, service_description=None):
    """ Return one pynag.Model.Service object for one specific service as seen

    from status point of view. That means it will do its best to return a service
    that was assigned to hostgroup but the caller requested a specific host.

    Returns:
        pynag.Model.Service object
    Raises:
        KeyError if not found
    """
    try:
        return pynag.Model.Service.objects.get_by_shortname("%s/%s" % (host_name, service_description))
    except KeyError, e:
        host = pynag.Model.Host.objects.get_by_shortname(host_name)
        for i in host.get_effective_services():
            if i.service_description == service_description:
                return i
        raise e


def command_line(host_name, service_description=None):
    """ Returns effective command line for a host or a service (i.e. resolves check_command)
    """
    try:
        if service_description in (None, '', '_HOST_'):
            obj = pynag.Model.Host.objects.get_by_shortname(host_name)
        else:
            obj = _get_service_model(host_name, service_description)
        return obj.get_effective_command_line(host_name=host_name)
    except KeyError:
        return "Could not resolve commandline. Object not found"


def update_check_command(host_name, service_description=None, **kwargs):
    """ Saves all custom variables of a given service
    """
    try:
        for k, v in kwargs.items():
            if service_description is None or service_description == '':
                obj = pynag.Model.Host.objects.get_by_shortname(host_name)
            else:
                obj = pynag.Model.Service.objects.get_by_shortname(
                    "%s/%s" % (host_name, service_description))
            if k.startswith("$_SERVICE") or k.startswith('$ARG'):
                obj.set_macro(k, v)
                obj.save()
        return "Object saved"
    except KeyError:
        raise Exception("Object not found")


def get_business_process_names():
    """ Returns all configured business processes
    """
    import adagios.businessprocess
    return map(lambda x: x.name, adagios.businessprocess.get_all_processes())


def get(object_type, *args, **kwargs):
    livestatus_arguments = pynag.Utils.grep_to_livestatus(*args, **kwargs)
    if not object_type.endswith('s'):
        object_type = object_type + 's'
    print kwargs
    if 'name__contains' in kwargs and object_type == 'services':
        print "ok fixing service"
        name = str(kwargs['name__contains'])
        livestatus_arguments = filter(
            lambda x: x.startswith('name'), livestatus_arguments)
        livestatus_arguments.append('Filter: host_name ~ %s' % name)
        livestatus_arguments.append('Filter: description ~ %s' % name)
        livestatus_arguments.append('Or: 2')
    livestatus = pynag.Parsers.mk_livestatus()
    print livestatus_arguments
    results = livestatus.query('GET %s' % object_type, *livestatus_arguments)

    if object_type == 'service':
        for i in results:
            i['name'] = i.get('host_name') + "/" + i.get('description')
    return results


def get_business_process(process_name=None, process_type=None):
    """ Returns a list of all processes in json format.

    If process_name is specified, return all sub processes.
    """
    import adagios.bi
    print str(process_name) == "blabla"
    print repr(process_name)
    if not process_name:
        processes = adagios.bi.get_all_processes()
    else:
        process = adagios.bi.get_business_process(str(process_name), process_type)
        print process
        processes = process.get_processes()
    result = []
    # Turn processes into nice json
    for i in processes:
        json = {}
        json['state'] = i.get_status()
        json['name'] = i.name
        json['display_name'] = i.display_name
        json['subprocess_count'] = len(i.processes)
        json['process_type'] = i.process_type
        result.append(json)
    return result