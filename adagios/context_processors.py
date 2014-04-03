import pynag.Model
import os
import getpass

from adagios import notifications, settings, add_plugin
from adagios.misc.rest import add_notification, clear_notification

import pynag.Model.EventHandlers
import pynag.Parsers
import adagios
import adagios.status.utils
from pynag import Model
import time
import datetime
from adagios import __version__

from django.utils.translation import ugettext as _

def on_page_load(request):
    """ Collection of actions that take place every page load """
    results = {}
    for k, v in reload_configfile(request).items():
        results[k] = v
    for k, v in get_httpuser(request).items():
        results[k] = v
    for k, v in get_tagged_comments(request).items():
        results[k] = v
    for k, v in check_nagios_running(request).items():
        results[k] = v
    for k, v in get_notifications(request).items():
        results[k] = v
    for k, v in get_unhandled_problems(request).items():
        results[k] = v
    for k, v in resolve_urlname(request).items():
        results[k] = v
    for k, v in check_selinux(request).items():
        results[k] = v
    for k, v in activate_plugins(request).items():
        results[k] = v
    for k, v in check_destination_directory(request).items():
        results[k] = v
    for k, v in check_nagios_cfg(request).items():
        results[k] = v
    for k, v in get_current_time(request).items():
        results[k] = v
    for k, v in get_okconfig(request).items():
        results[k] = v
    for k, v in get_nagios_url(request).items():
        results[k] = v
    for k, v in get_local_user(request).items():
        results[k] = v
    for k, v in get_current_settings(request).items():
        results[k] = v
    for k, v in get_plugins(request).items():
        results[k] = v
    for k, v in get_current_version(request).items():
        results[k] = v
    for k, v in get_serverside_includes(request).items():
        results[k] = v
    return results


def get_current_time(request):
    """ Make current timestamp available to templates
    """
    result = {}
    try:
        now = datetime.datetime.now()
        result['current_time'] = now.strftime("%b %d %H:%M")
        result['current_timestamp'] = int(time.time())
    except Exception:
        return result
    return result


def get_serverside_includes(request):
    """ Returns a list of serverside includes to include on this page """
    result = {}
    try:
        result['ssi_headers'] = []
        result['ssi_footers'] = []
        dirname = adagios.settings.serverside_includes
        current_url = resolve_urlname(request)
        if not dirname:
            return {}
        if not os.path.isdir(dirname):
            return {}
        files = os.listdir(dirname)
        common_header_file = "common-header.ssi"
        common_footer_file = "common-footer.ssi"
        custom_header_file = "{urlname}-header.ssi".format(urlname=current_url)
        custom_footer_file = "{urlname}-footer.ssi".format(urlname=current_url)
        if common_header_file in files:
            result['ssi_headers'].append(dirname + "/" + common_header_file)
        if common_footer_file in files:
            result['ssi_footers'].append(dirname + "/" + common_footer_file)
        if custom_header_file in files:
            result['ssi_headers'].append(dirname + "/" + custom_header_file)
        if custom_footer_file in files:
            result['ssi_footers'].append(dirname + "/" + custom_footer_file)
    except Exception:
        return {}
    return result


def activate_plugins(request):
    """ Activates any plugins specified in settings.plugins """
    for k, v in settings.plugins.items():
        add_plugin(name=k, modulepath=v)
    return {'misc_menubar_items': adagios.misc_menubar_items, 'menubar_items': adagios.menubar_items}


def get_local_user(request):
    """ Return user that is running the adagios process under apache
    """
    user = getpass.getuser()
    return {'local_user': user}


def get_current_version(request):
    """ Returns current adagios version """
    return {'adagios_version': __version__}

def get_current_settings(request):
    """ Return a copy of adagios.settings
    """
    return {'settings': adagios.settings}


def resolve_urlname(request):
    """Allows us to see what the matched urlname for this
    request is within the template"""
    from django.core.urlresolvers import resolve
    try:
        res = resolve(request.path)
        if res:
            return {'urlname': res.url_name}
    except Exception:
        return {'urlname': 'None'}


def get_httpuser(request):
    """ Get the current user that is authenticating to us and update event handlers"""
    try:
        remote_user = request.META.get('REMOTE_USER', None)
    except Exception:
        remote_user = "anonymous"
    return {'remote_user': remote_user or "anonymous"}


def get_nagios_url(request):
    """ Get url to legasy nagios interface """
    return {'nagios_url': settings.nagios_url}


def get_tagged_comments(request):
    """ (for status view) returns number of comments that mention the remote_user"""
    try:
        remote_user = request.META.get('REMOTE_USER', 'anonymous')
        livestatus = adagios.status.utils.livestatus(request)
        tagged_comments = livestatus.query(
            'GET comments', 'Stats: comment ~ %s' % remote_user, columns=False)[0]
        if tagged_comments > 0:
            return {'tagged_comments': tagged_comments}
        else:
            return {}
    except Exception:
        return {}


def get_unhandled_problems(request):
    """ Get number of any unhandled problems via livestatus """
    results = {}
    try:
        livestatus = adagios.status.utils.livestatus(request)
        num_problems = livestatus.query('GET services',
                                        'Filter: state != 0',
                                        'Filter: acknowledged = 0',
                                        'Filter: host_acknowledged = 0',
                                        'Filter: scheduled_downtime_depth = 0',
                                        'Filter: host_scheduled_downtime_depth = 0',
                                        'Stats: state != 0',
                                        'Stats: host_state != 0',
                                        columns=False)
        results['num_problems'] = num_problems[0] + num_problems[1]
        results['num_unhandled_problems'] = num_problems[0] + num_problems[1]

        result = livestatus.query('GET services',
                                        'Stats: state != 0',
                                        'Stats: state != 0',
                                        'Stats: acknowledged = 0',
                                        'Stats: scheduled_downtime_depth = 0',
                                        'Stats: host_state = 0',
                                        'StatsAnd: 4',
                                        columns=False
                                        )
        num_service_problems_all = result[0]
        num_service_problems_unhandled = result[1]


        result = livestatus.query('GET hosts',
                                        'Stats: state != 0',
                                        'Stats: state != 0',
                                        'Stats: acknowledged = 0',
                                        'Stats: scheduled_downtime_depth = 0',
                                        'Stats: host_state = 1',
                                        'StatsAnd: 4',
                                        columns=False
                                        )
        num_host_problems_all = result[0]
        num_host_problems_unhandled = result[1]

        num_problems_all = num_service_problems_all + num_host_problems_all
        num_problems_unhandled = num_service_problems_unhandled + num_host_problems_unhandled

        num_problems = num_problems_unhandled

        results = locals()
        del results['livestatus']
        del results['result']
        del results['request']

    except Exception:
        pass
    return results


def check_nagios_cfg(request):
    """ Check availability of nagios.cfg """
    return {'nagios_cfg': pynag.Model.config.cfg_file}


def check_destination_directory(request):
    """ Check that adagios has a place to store new objects """
    dest = settings.destination_directory
    dest_dir_was_found = False
    for k, v in Model.config.maincfg_values:
        if k != 'cfg_dir':
            continue
        if os.path.normpath(v) == os.path.normpath(dest):
            dest_dir_was_found = True
    if not dest_dir_was_found:
        add_notification(level="warning", notification_id="dest_dir",
                         message="Destination for new objects (%s) is not defined in nagios.cfg" % dest)
    elif not os.path.isdir(dest):
        add_notification(level="warning", notification_id="dest_dir",
                         message="Destination directory for new objects (%s) is not found. Please create it." % dest)
    else:
        clear_notification(notification_id="dest_dir")
    return {}


def check_nagios_running(request):
    """ Notify user if nagios is not running """
    try:
        if pynag.Model.config is None:
            pynag.Model.config = pynag.Parsers.config(
                adagios.settings.nagios_config)
        nagios_pid = pynag.Model.config._get_pid()
        return {"nagios_running": (nagios_pid is not None)}
    except Exception:
        return {}


def check_selinux(request):
    """ Check if selinux is enabled and notify user """
    notification_id = "selinux_active"
    if settings.warn_if_selinux_is_active:
        try:
            if open('/sys/fs/selinux/enforce', 'r').readline().strip() == "1":
                add_notification(
                    level="warning",
                    message='SELinux is enabled, which is likely to give your monitoring engine problems., see <a href="https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Enterprise_Linux/6/html-single/Security-Enhanced_Linux/index.html#sect-Security-Enhanced_Linux-Enabling_and_Disabling_SELinux-Disabling_SELinux">here</a> for information on how to disable it.',
                    notification_id=notification_id,
                )
        except Exception:
            pass
    else:
        clear_notification(notification_id)
    return {}


def get_notifications(request):
    """ Returns a hash map of adagios.notifications """
    return {"notifications": notifications}


def get_okconfig(request):
    """ Returns {"okconfig":True} if okconfig module is installed.
    """
    try:
        if "okconfig" in settings.plugins:
            return {"okconfig": True}
        return {}
    except Exception:
        return {}


def get_plugins(request):
    """
    """
    return {'plugins': settings.plugins}


def reload_configfile(request):
    """ Load the configfile from settings.adagios_configfile and put its content in adagios.settings. """
    try:
        clear_notification("configfile")
        locals = {}
        execfile(settings.adagios_configfile, globals(), locals)
        for k, v in locals.items():
            settings.__dict__[k] = v
    except Exception, e:
        add_notification(
            level="warning", message=str(e), notification_id="configfile")
    return {}


if __name__ == '__main__':
    on_page_load(request=None)
