
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
    return str(my_obj)