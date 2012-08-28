import pynag.Model
from os import environ
from platform import node
from adagios import notifications
from adagios.misc.rest import add_notification,clear_notification

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

def get_notifications(request):
    """ Here we check for different things that the user should be notified of in the
    notification panel.
    """
    try:
        warn = "Nagios should be reloaded to apply new configuration changes"
        ok = "Nagios configuration is up to date. Tommi: See TODO in header.html"
        if pynag.Model.config.needs_reload():
            add_notification(level="warning", message=warn)
            clear_notification(notification_id=ok.__hash__())
        else:
            add_notification(level="success", message=ok)
            clear_notification(notification_id=warn.__hash__())
    except Exception, e:
        pass
    return { "notifications": notifications }
