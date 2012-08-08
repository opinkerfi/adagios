import pynag.Model
from os import environ
from platform import node

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