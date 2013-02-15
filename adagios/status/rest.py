
'''

Convenient stateless functions for pynag. This module is used by the /rest/ interface of adagios.

'''

import time
import pynag.Control.Command
import pynag.Model

def hosts(**kwargs):
    """ Get status information about hosts

    """
    livestatus = pynag.Parsers.mk_livestatus()
    return livestatus.get_hosts()


def acknowledge(host_name, service_description=None, sticky=1, notify=1,persistent=0,author='adagios',comment='acknowledged by Adagios'):
    """ Acknowledge one single host or service check

    """
    if not service_description:
        pynag.Control.Command.acknowledge_host_problem(host_name=self.host_name,
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

def downtime(host_name,service_description=None,start_time=None,end_time=None,fixed=1,trigger_id=0,duration=7200,author='adagios',comment='Downtime scheduled by adagios',all_services_on_host=False):
    """ Schedule downtime for a host or a service """
    if fixed == 1 and start_time is None:
        start_time = time.time()
    if fixed == 1 and end_time is None:
        end_time = start_time + duration
    if all_services_on_host == True:
        return pynag.Control.Command.schedule_host_svc_downtime(host_name=host_name,
            start_time=start_time,
            end_time=end_time,
            fixed=fixed,
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        )
    elif not service_description:
        return pynag.Control.Command.schedule_host_downtime(host_name=host_name,
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
    return "error"

def reschedule(host_name,service_description, check_time=time.time(), wait=0):
    """ Reschedule a check of this service/host

    Arguments:
      host_name -- Name of the host
      service_description -- Name of the service check. If left empty, host check will be rescheduled
      check_time -- timestamp of when to execute this check, if left empty, execute right now
      wait -- If set to 1, function will not run until check has been rescheduled
    """
    if check_time is None or check_time is '':
        check_time = time.time()
    if not service_description:
        service_description = ""
        pynag.Control.Command.schedule_forced_host_check(host_name=host_name,check_time=check_time)
    else:
        pynag.Control.Command.schedule_forced_svc_check(host_name=host_name,service_description=service_description,check_time=check_time)
    if wait == "1":
        livestatus = pynag.Parsers.mk_livestatus()
        livestatus.query("GET services",
            "WaitObject: %s %s" % (host_name,service_description),
            "WaitCondition: last_check > %s" % check_time,
            "WaitTrigger: check",
            "Filter: host_name = %s" % host_name,
        )
    return "ok"

def comment(author,comment,host_name,service_description=None,persistent=1):
    """ Adds a comment to a particular service.

    If the "persistent" field is set to zero (0), the comment will be deleted the next time Nagios is restarted.
    Otherwise, the comment will persist across program restarts until it is deleted manually. """

    if not service_description:
        pynag.Control.Command.add_host_comment(host_name=host_name,persistent=persistent,author=author,comment=comment)
    else:
        pynag.Control.Command.add_svc_comment(host_name=host_name,service_description=service_description,persistent=persistent,author=author,comment=comment)
    return "ok"

def delete_comment(comment_id, host_name, service_description=None):
    """
    """
    if not service_description:
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
    time.sleep(2)
    c = pynag.Model.string_to_class[object_type]
    my_obj = c.objects.get_by_shortname(short_name)
    my_obj[attribute_name] = new_value
    my_obj.save()
    return str(my_obj)


def get_map_data(host_name=None):
    """ Returns a list of (host_name,2d_coords). If host_name is provided, returns a list with only that host """
    livestatus = pynag.Parsers.mk_livestatus()
    all_hosts = livestatus.query('GET hosts', )
    hosts_with_coordinates = pynag.Model.Host.objects.filter(**{'2d_coords__exists':True})
    result = []
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

            x,y = tmp
            host = {}
            host['host_name'] = name
            host['state'] = i['state']
            i['x_coordinates'] = x
            i['y_coordinates'] = y

            result.append( i )
    return result


def change_host_coordinates(host_name, latitude,longitude):
    """ Updates longitude and latitude for one specific host """
    host = pynag.Model.Host.objects.get_by_shortname(host_name)
    coords = "%s,%s" % (latitude,longitude)
    host['2d_coords'] = coords
    host.save()

def autocomplete(q):
    """ Returns a list of {'hosts':[], 'hostgroups':[],'services':[]} matching search query q
    """
    if q is None:
        q = ''
    result = {}
    hosts = pynag.Model.Host.objects.filter(host_name__contains=q)
    services = pynag.Model.Service.objects.filter(service_description__contains=q)
    hostgroups = pynag.Model.Hostgroup.objects.filter(hostgroup_name__contains=q)
    result['hosts'] = sorted(set(map(lambda x: x.host_name, hosts)))
    result['hostgroups'] = sorted(set(map(lambda x: x.hostgroup_name, hostgroups)))
    result['services'] = sorted(set(map(lambda x: x.service_description, services)))
    return result


if __name__ == '__main__':
    start = int(time.time())
    end = start+500
    print downtime(host_name='nagios.example.com',service_description='Ping',
        start_time=start,
        end_time=end,
        comment='test by palli')