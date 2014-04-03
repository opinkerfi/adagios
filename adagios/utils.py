#!/usr/bin/env python

import multiprocessing
import adagios.status.utils
import time
import adagios
import pynag.Model

from django.utils.translation import ugettext as _


def wait(object_type, WaitObject, WaitCondition, WaitTrigger, **kwargs):
    livestatus = adagios.status.utils.livestatus(None)
    livestatus.get(object_type, WaitObject=WaitObject, WaitCondition=WaitCondition, WaitTrigger=WaitTrigger, **kwargs)
    print WaitObject

def wait_for_objects(object_type, object_list, condition=None, trigger='check'):
    if not condition:
        condition = "last_check > %s" % int(0)
    callback = lambda x: wait(object_type, WaitObject=x, WaitCondition=condition, WaitTrigger=trigger)
    for WaitObject in object_list:
        callback(WaitObject)

def wait_for_service(host_name, service_description, condition='last_check >= 0', trigger='check'):
    livestatus = adagios.status.utils.livestatus(None)
    waitobject = "%s;%s" % (host_name, service_description)
    livestatus.get_services(
        host_name=host_name,
        service_description=service_description,
        WaitCondition=condition,
        WaitObject=waitobject
    )

from multiprocessing.pool import ThreadPool


class Task(object):
    def __init__(self, num_processes=5):
        self._tasks = []
        adagios.tasks.append(self)
        self._pool = ThreadPool(processes=num_processes)

    def add(self, function, *args, **kwargs):
        print "Adding Task:", locals()
        result = self._pool.apply_async(function, args, kwargs)
        self._tasks.append(result)
        #print result.get()

    def status(self):
        all_tasks = self._tasks
        for i in all_tasks:
            print i.ready()
        completed_tasks = filter(lambda x: x.ready(), all_tasks)
        return "{done}/{total} done.".format(done=len(completed_tasks), total=len(all_tasks))

    def get_id(self):
        return hash(self)

    def ready(self):
        """ Returns True if all the Tasks in this class have finished running. """
        return max(map(lambda x: x.ready(), self._tasks))


def update_eventhandlers(request):
    """ Iterates through all pynag eventhandler and informs them who might be making a change
    """
    remote_user = request.META.get('REMOTE_USER', 'anonymous')
    for i in pynag.Model.eventhandlers:
        i.modified_by = remote_user

    # if okconfig is installed, make sure okconfig is notified of git
    # settings
    try:
        from pynag.Utils import GitRepo
        import okconfig
        okconfig.git = GitRepo(directory=os.path.dirname(
            adagios.settings.nagios_config), auto_init=False, author_name=remote_user)
    except Exception:
        pass
