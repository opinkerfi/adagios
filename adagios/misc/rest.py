# -*- coding: utf-8 -*-
#
# Copyright 2012, Pall Sigurdsson <palli@opensource.is>
#
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

This is a rest interface used by the "/rest/" module that affects adagios directly.

"""

from adagios import __version__, notifications, tasks
from adagios.settings import plugins
from django.utils.translation import ugettext as _

version = __version__


def add_notification(level="info", message="message", notification_id=None, notification_type=None, user=None):
    """ Add a new notification to adagios notification bar.

    Arguments:
      level                      -- pick "info" "success" "error" "danger"
      message                    -- Arbitary text message,
      notification_id (optional) -- Use this if you want to remote
                                 -- remove this notification later via clear_notification()
      notification_type          -- Valid options: "generic" and "show_once"

      user                       -- If specified, only display notification for this specific user.

    Returns:
      None

    Examples:
    >>> add_notification(level="warning", message="Nagios needs to reload")
    """
    if not notification_id:
        notification_id = str(message.__hash__())
    if not notification_type:
        notification_type = "generic"
    notification = locals()
    notifications[notification_id] = notification


def clear_notification(notification_id):
    """ Clear one notification from adagios notification panel """
    if notification_id in notifications:
        del notifications[notification_id]
        return "success"
    return "not found"


def get_notifications(request):
    """ Shows all current notifications """
    result = []
    for k in notifications.keys():
        i = notifications[k]
        if i.get('user') and i.get('user') != request.META.get('remote_user'):
            continue # Skipt this message if it is meant for someone else
        elif i.get('notification_type') == 'show_once':
            del notifications[k]
            pass
        result.append(i)
    return result


def clear_all_notifications():
    """ Removes all notifications from adagios notification panel """
    notifications.clear()
    return "all notifications cleared"


def list_tasks():
    """

    """
    result = []
    for task in tasks:
        current_task = {
            'task_id': task.get_id(),
            'task_status': task.status()
            }
        result.append(current_task)
    return result


def get_task(task_id="someid"):
    """ Return information about one specific background task """
    for task in tasks:
        if str(task.get_id) == str(task_id) or task_id:
            current_task = {
                'task_id': task.get_id(),
                'task_status': task.status()
            }
            return current_task
    raise KeyError("Task not '%s' Found" % task_id)
