__author__ = 'palli'


class AdagiosError(Exception):
    """ Base Class for all Adagios Exceptions """
    pass


class AccessDenied(AdagiosError):
    """ This exception is raised whenever a user tries to access a page he does not have access to. """
    def __init__(self, username, access_required, access_level, *args, **kwargs):
        self.username = username
        self.access_required = access_required
        self.access_level = access_level
        message = "Access Denied. {username} needs to be part of {access_required}."
        message = message.format(**locals())
        super(AccessDenied, self).__init__(message, *args, **kwargs)