import pynag.Model
import os

from adagios import notifications, settings, add_plugin
from adagios.misc.rest import add_notification,clear_notification
import adagios
from pynag import Model
from pynag.Parsers import mk_livestatus
def on_page_load(request):
    """ Collection of actions that take place every page load """
    results = {}
    for k,v in reload_configfile(request).items():
        results[k] = v
    for k,v in get_httpuser(request).items():
        results[k] = v
    for k,v in check_nagios_running(request).items():
        results[k] = v
    for k,v in check_nagios_needs_reload(request).items():
        results[k] = v
    for k,v in get_notifications(request).items():
        results[k] = v
    for k,v in get_unhandled_problems(request).items():
        results[k] = v
    for k,v in resolve_urlname(request).items():
        results[k] = v
    for k,v in check_selinux(request).items():
        results[k] = v
    for k,v in activate_plugins(request).items():
        results[k] = v
    for k,v in check_git(request).items():
        results[k] = v
    for k,v in check_destination_directory(request).items():
        results[k] = v
    for k,v in check_nagios_cfg(request).items():
        results[k] = v
    return results

def activate_plugins(request):
    """ Activates any plugins specified in settings.plugins """
    for k,v in settings.plugins.items():
        add_plugin(name=k,modulepath=v)
    return {'misc_menubar_items':adagios.misc_menubar_items, 'menubar_items':adagios.menubar_items}

def resolve_urlname(request):
    """Allows us to see what the matched urlname for this
    request is within the template"""
    from django.core.urlresolvers import resolve
    try:
        res = resolve(request.path)
        if res:
            return {'urlname': res.url_name}
    except Exception:
        return {}


def get_httpuser(request):
    """ Get the current user that is authenticating to us and update event handlers"""
    remote_user = request.META.get('REMOTE_USER', 'anonymous')
    for i in pynag.Model.eventhandlers:
        i.modified_by = remote_user
    return {'remote_user': remote_user }

def get_unhandled_problems(request):
    """ Get number of any unhandled problems via livestatus """
    results = {}
    try:
        livestatus = mk_livestatus()
        problems = livestatus.query('GET services','Filter: state != 0', 'Filter: acknowledged = 0', 'Filter: scheduled_downtime_depth = 0')
        results['problems'] = problems
        results['num_problems'] = len(problems)
    except Exception:
        pass
    return results
def check_nagios_cfg(request):
    """ Check availability of nagios.cfg """
    return { 'nagios_cfg' : pynag.Model.config.cfg_file }

def check_destination_directory(request):
    """ Check that adagios has a place to store new objects """
    dest = settings.destination_directory
    dest_dir_was_found = False
    for k,v in Model.config.maincfg_values:
        if k != 'cfg_dir':
            continue
        if os.path.normpath(v) == os.path.normpath(dest):
            dest_dir_was_found=True
    if not dest_dir_was_found:
        add_notification(level="warning",notification_id="dest_dir", message="Destination for new objects (%s) is not defined in nagios.cfg" %dest)
    elif not os.path.isdir(dest):
        add_notification(level="warning", notification_id="dest_dir", message="Destination directory for new objects (%s) is not found. Please create it." %dest)
    else:
        clear_notification(notification_id="dest_dir")
    return {}

def check_git(request):
    """ Notify user if there is uncommited data in git repository """
    nagiosdir = os.path.dirname(pynag.Model.config.cfg_file)
    if settings.enable_githandler == True:
        try:
            git = Model.EventHandlers.GitEventHandler(nagiosdir, 'adagios', 'adagios')
            uncommited_files = git.get_uncommited_files()
            if len(uncommited_files) > 0:
                add_notification(level="warning", notification_id="uncommited", message="There are %s uncommited files in %s" % (len(uncommited_files), nagiosdir))
            else:
                clear_notification(notification_id="uncommited")
            clear_notification(notification_id="git_missing")
        except Model.EventHandlers.EventHandlerError, e:
            if e.errorcode == 128:
                add_notification(level="warning", notification_id="git_missing", message="Git Handler is enabled but there is no git repository in %s. Please init a new git repository." % nagiosdir)
    return {}

def check_nagios_running(request):
    """ Notify user if nagios is not running """
    nagios_pid = pynag.Model.config._get_pid()
    return { "nagios_running":(nagios_pid is not None)}

def check_nagios_needs_reload(request):
    """ Notify user if nagios needs a reload """
    return { "needs_reload": pynag.Model.config.needs_reload() }

def check_selinux(request):
    """ Check if selinux is enabled and notify user """
    if not settings.warn_if_selinux_is_active == True:
        return {}
    try:
        if open('/sys/fs/selinux/enforce', 'r').readline().strip() == "1":
            add_notification(level="warning", message='SELinux is enabled, that is not supported, please disable it, see https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Enterprise_Linux/6/html-single/Security-Enhanced_Linux/index.html#sect-Security-Enhanced_Linux-Enabling_and_Disabling_SELinux-Disabling_SELinux')
    except Exception:
        pass
    return {}

def get_notifications(request):
    """ Returns a hash map of adagios.notifications """
    return { "notifications": notifications  }



def reload_configfile(request):
    """ Load the configfile from settings.adagios_configfile and put its content in adagios.settings. """
    try:
        clear_notification("configfile")
        locals = {}
        execfile(settings.adagios_configfile,globals(),locals)
        for k,v in locals.items():
            settings.__dict__[k] = v
    except Exception, e:
        add_notification(level="warning", message=str(e), notification_id="configfile")
    return {}
