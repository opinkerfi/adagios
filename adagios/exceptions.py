""" Exceptions that Adagios uses and raises
"""


class AdagiosError(Exception):
    """ Base Class for all Adagios Exceptions """
    pass


class AccessDenied(AdagiosError):
    """ This exception is raised whenever a user tries to access a page he does not have access to. """
    def __init__(self, username, access_required, message, path=None, *args, **kwargs):
        self.username = username
        self.access_required = access_required
        self.message = message
        self.path = path
        super(AccessDenied, self).__init__(message, *args, **kwargs)