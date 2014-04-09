import os

def startup():
    """ Do some pre-loading and parsing of objects

    Returns:
        None
    """
    from adagios import settings

    pynag.Model.cfg_file = settings.nagios_config
    pynag.Model.pynag_directory = settings.destination_directory

    # Multi-Layered Parsing settings
    pynag.Model.multilayered_parsing = settings.enable_multilayered_parsing
    pynag.Model.layers = settings.layers
    pynag.Model.adagios_layer = settings.adagios_layer
    if pynag.Model.multilayered_parsing:
        # Do layer compiling and generate the actual config
        pynag.Model.source_tracker = pynag.Parsers.SourceTracker()
        pynag.Model.compile_layers()

    # Pre load objects on startup
    pynag.Model.ObjectDefinition.objects.get_all()

    if settings.enable_githandler == True:
        from pynag.Model import EventHandlers
        pynag.Model.eventhandlers.append(
            pynag.Model.EventHandlers.GitEventHandler(
                os.path.dirname(pynag.Model.config.cfg_file), 'adagios', 'tommi')
        )

# If any pynag errors occur during initial parsing, we ignore them
# because we still want the webserver to start.
# Any errors that might occur will happen on page load anyway
# so the user will be informed
try:
    import pynag.Model
    startup()
except Exception, e:
    pass
