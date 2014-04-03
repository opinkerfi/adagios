
"""

Convenient stateless functions for the status module. These are meant for programs to interact
with status of Nagios.

"""

import time
import pynag.Control.Command
import pynag.Model
import pynag.Utils
import adagios.status.utils
import pynag.Parsers
import collections

from django.utils.translation import ugettext as _

def hosts(request, fields=None, **kwargs):
    """ Get List of hosts. Any parameters will be passed straight throught to pynag.Utils.grep()

        Arguments:
            fields -- If specified, a list of attributes to return. If unspecified, all fields are returned.

            Any **kwargs will be treated as a pynag.Utils.grep()-style filter
    """
    return adagios.status.utils.get_hosts(request=request, fields=fields, **kwargs)


def services(request, fields=None, **kwargs):
    """ Similar to hosts(), is a wrapper around adagios.status.utils.get_services()
    """
    return adagios.status.utils.get_services(request=request, fields=fields, **kwargs)

def services_dt(request, fields=None, **kwargs):
    """ Similar to hosts(), is a wrapper around adagios.status.utils.get_services()
    """
    services = adagios.status.utils.get_services(request=request, fields='host_name,description')

    result = {
        'sEcho': len(services),
	'iTotalRecords': len(services),
        'aaData': []
    }
    for service in services:
        result['aaData'].append(service.values())
    return result


def contacts(request, fields=None, *args, **kwargs):
    """ Wrapper around pynag.Parsers.mk_livestatus.get_contacts()
    """
    l = adagios.status.utils.livestatus(request)
    return l.get_contacts(*args, **kwargs)


def emails(request, *args, **kwargs):
    """ Returns a list of all emails of all contacts
    """
    l = adagios.status.utils.livestatus(request)
    return map(lambda x: x['email'], l.get_contacts('Filter: email !='))


def acknowledge_many(hostlist, servicelist, sticky=1, notify=1, persistent=0, author="adagios", comment="acknowledged by Adagios"):
    """ Same as acknowledge, but for acknowledge on many hosts services at a time.

     Arguments:
        hostlist    -- string in the format of host1;host2;host3
        servicelist -- string in the format of host1,service1;host2,service2
    """
    items = []
    for i in hostlist.split(';'):
        if not i: continue
        items.append((i, None))

    for i in servicelist.split(';'):
        if not i: continue
        host_name,service_description = i.split(',')
        items.append((host_name, service_description))
    for i in items:
        acknowledge(
                host_name=i[0],
                service_description=i[1],
                sticky=sticky,
                notify=notify,
                persistent=persistent,
                author=author,
                comment=comment
        )
    return "Success"


def acknowledge(host_name, service_description=None, sticky=1, notify=1, persistent=0, author='adagios', comment='acknowledged by Adagios'):
    """ Acknowledge one single host or service check """
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


def downtime_many(hostlist, servicelist, hostgrouplist, start_time=None, end_time=None, fixed=1, trigger_id=0, duration=7200, author='adagios', comment='Downtime scheduled by adagios', all_services_on_host=False, hostgroup_name=None):
    """ Same as downtime, but for acknowledge on many hosts services at a time.

     Arguments:
        hostlist    -- string in the format of host1;host2;host3
        hostgrouplist -- string in the format of hostgroup1;hostgroup2;hostgroup3
        servicelist -- string in the format of host1,service1;host2,service2
    """
    items = []
    for i in hostlist.split(';'):
        if not i: continue
        items.append((i, None, None))
    for i in hostgrouplist.split(';'):
        if not i: continue
        items.append((None, None, i))

    for i in servicelist.split(';'):
        if not i: continue
        host_name, service_description = i.split(',')
        items.append((host_name, service_description, None))
    for i in items:
        host_name = i[0]
        service_description = i[1]
        hostgroup_name = i[2]
        downtime(
            host_name=host_name,
            service_description=service_description,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
            all_services_on_host=all_services_on_host,
            hostgroup_name=hostgroup_name
        )


def downtime(host_name=None, service_description=None, start_time=None, end_time=None, fixed=1, trigger_id=0, duration=7200, author='adagios', comment='Downtime scheduled by adagios', all_services_on_host=False, hostgroup_name=None):
    """ Schedule downtime for a host or a service """
    if fixed in (1, '1') and start_time in (None, ''):
        start_time = time.time()
    if fixed in (1, '1') and end_time in (None, ''):
        end_time = int(start_time) + int(duration)
    if all_services_on_host == 'false':
        all_services_on_host = False
    elif all_services_on_host == 'true':
        all_services_on_host = True

    # Check if we are supposed to schedule downtime for a whole hostgroup:
    if hostgroup_name:
        result1 = pynag.Control.Command.schedule_hostgroup_host_downtime(
            hostgroup_name=hostgroup_name,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        ),
        result2 = pynag.Control.Command.schedule_hostgroup_svc_downtime(
            hostgroup_name=hostgroup_name,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        )
        return result1, result2
    # Check if we are recursively scheduling downtime for host and all its services:
    elif all_services_on_host:
        result1 = pynag.Control.Command.schedule_host_svc_downtime(
            host_name=host_name,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        ),
        result2 = pynag.Control.Command.schedule_host_downtime(
            host_name=host_name,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        )
        return result1, result2
    # Otherwise, if this is a host
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
    # otherwise it must be a service:
    else:
        return pynag.Control.Command.schedule_svc_downtime(
            host_name=host_name,
            service_description=service_description,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        )

import adagios.utils


def reschedule_many(request, hostlist, servicelist, check_time=None, **kwargs):
    """ Same as reschedule() but takes a list of hosts/services as input

    Arguments:
      hostlist    -- semicolon seperated list of hosts to schedule checks for. Same as multiple calls with host_name=
      servicelist -- Same as hostlist but for services. Format is: host_name,service_description;host_name,service_description
    """
    #task = adagios.utils.Task()
    #WaitCondition = "last_check > %s" % int(time.time()- 1)
    for i in hostlist.split(';'):
        if not i: continue
        reschedule(request, host_name=i, service_description=None, check_time=check_time)
        #task.add(wait, 'hosts', i, WaitCondition)
    for i in servicelist.split(';'):
        if not i: continue
        host_name,service_description = i.split(',')
        reschedule(request, host_name=host_name, service_description=service_description, check_time=check_time)
        #WaitObject = "{h};{s}".format(h=host_name, s=service_description)
        #task.add(wait, 'services', WaitObject, WaitCondition)
    return {'message': "command sent successfully"}


def reschedule(request, host_name=None, service_description=None, check_time=None, wait=0, hostlist='', servicelist=''):
    """ Reschedule a check of this service/host

    Arguments:
      host_name -- Name of the host
      service_description -- Name of the service check. If left empty, host check will be rescheduled
      check_time -- timestamp of when to execute this check, if left empty, execute right now
      wait -- If set to 1, function will not return until check has been rescheduled
    """

    if check_time is None or check_time is '':
        check_time = time.time()
    if service_description in (None, '', u'', '_HOST_', 'undefined'):
        service_description = ""
        pynag.Control.Command.schedule_forced_host_check(
            host_name=host_name, check_time=check_time)
        if wait == "1":
            livestatus = adagios.status.utils.livestatus(request)
            livestatus.query("GET hosts",
                             "WaitObject: %s " % host_name,
                             "WaitCondition: last_check > %s" % check_time,
                             "WaitTrigger: check",
                             "Filter: host_name = %s" % host_name,
                             )
    else:
        pynag.Control.Command.schedule_forced_svc_check(
            host_name=host_name, service_description=service_description, check_time=check_time)
        if wait == "1":
            livestatus = adagios.status.utils.livestatus(request)
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


def get_map_data(request, host_name=None):
    """ Returns a list of (host_name,2d_coords). If host_name is provided, returns a list with only that host """
    livestatus = adagios.status.utils.livestatus(request)
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


def autocomplete(request, q):
    """ Returns a list of {'hosts':[], 'hostgroups':[],'services':[]} matching search query q
    """
    if q is None:
        q = ''
    result = {}

    hosts = adagios.status.utils.get_hosts(request, host_name__contains=q)
    services = adagios.status.utils.get_services(request, service_description__contains=q)
    hostgroups = adagios.status.utils.get_hostgroups(request, hostgroup_name__contains=q)

    result['hosts'] = sorted(set(map(lambda x: x['name'], hosts)))
    result['hostgroups'] = sorted(set(map(lambda x: x['name'], hostgroups)))
    result['services'] = sorted(set(map(lambda x: x['description'], services)))

    return result


def delete_downtime(downtime_id, is_service=True):
    """ Delete one specific downtime with id that matches downtime_id.

    Arguments:
      downtime_id -- Id of the downtime to be deleted
      is_service  -- If set to True or 1, then this is assumed to be a service downtime, otherwise assume host downtime
    """
    if is_service in (True, 1, '1'):
        pynag.Control.Command.del_svc_downtime(downtime_id)
    else:
        pynag.Control.Command.del_host_downtime(downtime_id)
    return "ok"

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


def state_history(start_time=None, end_time=None, object_type=None, host_name=None, service_description=None, hostgroup_name=None):
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
    log_entries = l.get_state_history(start_time=start_time, end_time=end_time, host_name=host_name, service_description=service_description)
    if object_type == 'host' or object_type == 'service':
        pass
    elif object_type == 'hostgroup':
        hg = pynag.Model.Hostgroup.objects.get_by_shortname(hostgroup_name)
        hosts = hg.get_effective_hosts()
        hostnames = map(lambda x: x.host_name, hosts)
        log_entries = filter(lambda x: x['host_name'] in hostnames, log_entries)
    else:
        raise Exception("Unsupported object type: %s" % object_type)

    # Add some css-hints for and duration of each state history entry as percent of duration
    # this is used by all views that have state history and on top of it a progress bar which shows
    # Up/downtime totals.
    c = {'log': log_entries }
    if len(c['log']) > 0:
        log = c['log']
        c['start_time'] = start_time = log[0]['time']
        c['end_time'] = log[-1]['time']
        now = time.time()

        total_duration = now - start_time
        css_hint = {}
        css_hint[0] = 'success'
        css_hint[1] = 'warning'
        css_hint[2] = 'danger'
        css_hint[3] = 'info'
        for i in log:
            i['duration_percent'] = 100 * i['duration'] / total_duration
            i['bootstrap_status'] = css_hint[i['state']]

    return log_entries

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
    """ Returns effective command line for a host or a service (i.e. resolves check_command) """
    try:
        obj = _get_host_or_service(host_name, service_description)
        return obj.get_effective_command_line(host_name=host_name)
    except KeyError:
        return "Could not resolve commandline. Object not found"


def _get_host_or_service(host_name, service_description=None):
    """ Return a pynag.Model.Host or pynag.Model.Service or raise exception if none are found """
    host = pynag.Model.Host.objects.get_by_shortname(host_name)
    if not service_description or service_description == '_HOST_':
        return host
    else:
        search_result = pynag.Model.Service.objects.filter(host_name=host_name, service_description=service_description)
        if search_result:
            return search_result[0]
        # If no services were found, the service might be applied to a hostgroup
        for service in host.get_effective_services():
            if service.service_description == service_description:
                return service
    raise KeyError("Object not found")


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
            if k.startswith("$_SERVICE") or k.startswith('$ARG') or k.startswith('$_HOST'):
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


def get(request, object_type, *args, **kwargs):
    livestatus_arguments = pynag.Utils.grep_to_livestatus(*args, **kwargs)
    if not object_type.endswith('s'):
        object_type += 's'
    if 'name__contains' in kwargs and object_type == 'services':
        name = str(kwargs['name__contains'])
        livestatus_arguments = filter(
            lambda x: x.startswith('name'), livestatus_arguments)
        livestatus_arguments.append('Filter: host_name ~ %s' % name)
        livestatus_arguments.append('Filter: description ~ %s' % name)
        livestatus_arguments.append('Or: 2')
    livestatus = adagios.status.utils.livestatus(request)
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
    if not process_name:
        processes = adagios.bi.get_all_processes()
    else:
        process = adagios.bi.get_business_process(str(process_name), process_type)
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


def remove_downtime(request, host_name, service_description=None, downtime_id=None):
    """ Remove downtime for one specific host or service """
    downtimes_to_remove = []
    # If downtime_id is not provided, remove all downtimes of that service or host
    if downtime_id:
        downtimes_to_remove.append(downtime_id)
    else:
        livestatus = adagios.status.utils.livestatus(request)
        query_parameters = []
        query_parameters.append('GET downtimes')
        query_parameters.append('Filter: host_name = {host_name}'.format(**locals()))
        if service_description:
            query_parameters.append('Filter: service_description = {service_description}'.format(**locals()))
        result = livestatus.query(*query_parameters)
        for i in result:
            downtime_id = i['id']
            downtimes_to_remove.append(downtime_id)

    if service_description:
        for i in downtimes_to_remove:
            pynag.Control.Command.del_svc_downtime(downtime_id=i)
    else:
        for i in downtimes_to_remove:
            pynag.Control.Command.del_host_downtime(downtime_id=i)
    return "ok"


def remove_acknowledgement(host_name, service_description=None):
    """ Remove downtime for one specific host or service """
    if not service_description:
        pynag.Control.Command.remove_host_acknowledgement(host_name=host_name)
    else:
        pynag.Control.Command.remove_svc_acknowledgement(host_name=host_name, service_description=service_description)
    return "ok"


def submit_check_result(request, host_name, service_description=None, autocreate=False, status_code=3, plugin_output="No message was entered", performance_data=""):
    """ Submit a passive check_result for a given host or a service

    Arguments:
        host_name           -- Name of the host you want to submit check results for
        service_description -- If provided, submit a result for service this service instead of a host
        autocreate          -- If this is set to True, and host/service does not exist. It will be created
        status_code              -- Nagios style status for the check (0,1,2,3 which means ok,warning,critical, etc)
        plugin_output       -- The text output of the check to display in a web interface
        performance_data    -- Optional, If there are any performance metrics to display
    """
    livestatus = adagios.status.utils.livestatus(request)
    result = {}
    output = plugin_output + " | " + performance_data
    if not service_description:
        object_type = 'host'
        args = pynag.Utils.grep_to_livestatus(host_name=host_name)
        objects = livestatus.get_hosts(*args)
    else:
        object_type = 'service'
        args = pynag.Utils.grep_to_livestatus(host_name=host_name, service_description=service_description)
        objects = livestatus.get_services(*args)

    if not objects and autocreate is True:
        raise Exception("Autocreate not implemented yet")
    elif not objects:
        result['error'] = 'No %s with that name' % object_type
    else:
        if object_type == 'host':
            pynag.Control.Command.process_host_check_result(host_name, status_code, output)
        else:
            pynag.Control.Command.process_service_check_result(host_name, service_description, status_code, output)
        result['message'] = "Command has been submitted."
    return result


def statistics(request, **kwargs):
    """ Returns a dict with various statistics on status data. """
    return adagios.status.utils.get_statistics(request, **kwargs)


def metrics(request, **kwargs):
    """ Returns a list of dicts which contain service perfdata metrics
    """
    result = []
    fields = "host_name description perf_data state host_state".split()
    services = adagios.status.utils.get_services(request, fields=fields, **kwargs)
    for service in services:
        metrics = pynag.Utils.PerfData(service['perf_data']).metrics
        metrics = filter(lambda x: x.is_valid(), metrics)
        for metric in metrics:
            metric_dict = {
                'host_name': service['host_name'],
                'service_description': service['description'],
                'state': service['state'],
                'host_state': service['host_state'],
                'label': metric.label,
                'value': metric.value,
                'uom': metric.uom,
                'warn': metric.warn,
                'crit': metric.crit,
                'min': metric.min,
                'max': metric.max,
            }
            result.append(metric_dict)
    return result

def metric_names(request, **kwargs):
    """ Returns the names of all perfdata metrics that match selected request """
    metric_names = set()
    fields = "host_name description perf_data state host_state".split()
    services = adagios.status.utils.get_services(request, fields=fields, **kwargs)
    for service in services:
        metrics = pynag.Utils.PerfData(service['perf_data']).metrics
        metrics = filter(lambda x: x.is_valid(), metrics)
        for metric in metrics:
            metric_names.add(metric.label)

    result = {
        'services that match filter': len(services),
        'filter': kwargs,
        'metric_names': sorted(list(metric_names)),
    }
    return result

def wait(table, WaitObject, WaitCondition=None, WaitTrigger='check', **kwargs):
    print "Lets wait for", locals()
    if not WaitCondition:
        WaitCondition = "last_check > %s" % int(time.time()-1)
    livestatus = adagios.status.utils.livestatus(None)
    print "livestatus ok"
    result = livestatus.get(table, 'Stats: state != 999', WaitObject=WaitObject, WaitCondition=WaitCondition, WaitTrigger=WaitTrigger, **kwargs)
    print "ok no more waiting for ", WaitObject
    return result


def wait_many(hostlist, servicelist, WaitCondition=None, WaitTrigger='check', **kwargs):
    if not WaitCondition:
        WaitCondition = "last_check > %s" % int(time.time()-1)
    livestatus = adagios.status.utils.livestatus(None)
    for host in hostlist.split(';'):
        if not host:
            continue
        WaitObject = host
        livestatus.get('hosts', WaitObject=WaitObject, WaitCondition=WaitCondition, WaitTrigger=WaitTrigger, **kwargs)
        print WaitObject
    for service in servicelist.split(';'):
        if not service:
            continue
        WaitObject = service.replace(',', ';')
        livestatus.get('services', WaitObject=WaitObject, WaitCondition=WaitCondition, WaitTrigger=WaitTrigger, **kwargs)
        print WaitObject

