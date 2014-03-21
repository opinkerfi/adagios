import os


def startup():
    """ Do some pre-loading and parsing of objects

    Returns:
        None
    """
    from adagios import settings

    pynag.Model.cfg_file = settings.nagios_config
    pynag.Model.pynag_directory = settings.destination_directory

    # Pre load objects on startup
    pynag.Model.ObjectDefinition.objects.get_all()

    from pynag.Model import EventHandlers
    if settings.enable_githandler == True:
        nagios_dir = os.path.dirname(pynag.Model.config.cfg_file)
        githandler = pynag.Model.EventHandlers.GitEventHandler(nagios_dir, 'adagios', 'tommi')
        pynag.Model.eventhandlers.append(githandler)
    if settings.auto_reload:
        handler = pynag.Model.EventHandlers.NagiosReloadHandler(nagios_init=settings.nagios_init_script)
        pynag.Model.eventhandlers.append(handler)

# If any pynag errors occur during initial parsing, we ignore them
# because we still want the webserver to start.
# Any errors that might occur will happen on page load anyway
# so the user will be informed
try:
    import pynag.Model
    startup()
except Exception, e:
    pass
