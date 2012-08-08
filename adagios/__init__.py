def startup():
    """ Do some pre-loading and parsing of objects

    Returns:
        None
    """
    from adagios import settings
    import os.path

    pynag.Model.cfg_file = settings.nagios_config

    # Pre load objects on startup
    pynag.Model.ObjectDefinition.objects.get_all()

    if settings.enable_githandler == True:
        from pynag.Model import EventHandlers
        pynag.Model.eventhandlers.append(
            pynag.Model.EventHandlers.GitEventHandler(os.path.dirname(pynag.Model.config.cfg_file), 'adagios', 'tommi')
        )

try:
    import pynag.Model
    startup()
except Exception:
    pass