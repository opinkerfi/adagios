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
        compile_layers()

    # Pre load objects on startup
    pynag.Model.ObjectDefinition.objects.get_all()

    if settings.save_services_with_hosts:
        for serv in pynag.Model.Service.objects.all:
            serv.merge_service_to_host()

    if settings.enable_githandler == True:
        from pynag.Model import EventHandlers
        pynag.Model.eventhandlers.append(
            pynag.Model.EventHandlers.GitEventHandler(
                os.path.dirname(pynag.Model.config.cfg_file), 'adagios', 'tommi')
        )

def compile_layers():
    """ Parses all the layers and generates complete config to use in 
    adagios 
    """
    if pynag.Model.multilayered_parsing:
        pynag.Model.config = pynag.Parsers.LayeredConfigCompiler(
                cfg_file=pynag.Model.cfg_file,
                layers=pynag.Model.layers,
                destination_directory=pynag.Model.pynag_directory
                )
        pynag.Model.config.parse()
        pynag.Model.config = pynag.Parsers.LayeredConfig(
                cfg_file=pynag.Model.cfg_file,
                adagios_layer = pynag.Model.adagios_layer
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
