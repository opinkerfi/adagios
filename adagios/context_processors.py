import pynag.Model
from os import environ
from platform import node

from adagios import notifications, settings
from adagios.misc.rest import add_notification,clear_notification

def on_page_load(request):
    """ Collection of actions that take place every page load """
    results = {}
    for k,v in reload_configfile(request).items():
        results[k] = v
    for k,v in get_httpuser(request).items():
        results[k] = v
    for k,v in check_nagios_needs_reload(request).items():
        results[k] = v
    for k,v in get_notifications(request).items():
        results[k] = v
    for k,v in resolve_urlname(request).items():
        results[k] = v
    for k,v in check_selinux(request).items():
        results[k] = v

    return results


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
    for i in pynag.Model.eventhandlers:
        i.modified_by = request.META.get('REMOTE_USER', 'anonymous')
    return {}


def check_nagios_needs_reload(request):
    """ Notify user if nagios needs a reload """
    try:
        # Remove notification if there was any
        clear_notification("needs_reload")
        warn = "Nagios should be reloaded to apply new configuration changes"
        ok = "Nagios configuration is up to date. Tommi: See TODO in header.html"
        needs_reload = pynag.Model.config.needs_reload()
        if needs_reload:
            add_notification(level="warning", message=warn, notification_id="needs_reload")
        else:
            add_notification(level="success", message=ok, notification_id="needs_reload")
    except KeyError, e:
        raise e
    return { "needs_reload":needs_reload }

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
            print k, '==', v
            settings.__dict__[k] = v
    except Exception, e:
        add_notification(level="warning", message=str(e), notification_id="configfile")
    return {}
