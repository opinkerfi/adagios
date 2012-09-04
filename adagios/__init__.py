import os.path
import adagios

__version__="git-latest"

notifications = {}
active_plugins = {}
misc_menubar_items = []
menubar_items = []

def startup():
    """ Do some pre-loading and parsing of objects

    Returns:
        None
    """
    from adagios import settings

    pynag.Model.cfg_file = settings.nagios_config

    # Pre load objects on startup
    pynag.Model.ObjectDefinition.objects.get_all()

    if settings.enable_githandler == True:
        from pynag.Model import EventHandlers
        pynag.Model.eventhandlers.append(
            pynag.Model.EventHandlers.GitEventHandler(os.path.dirname(pynag.Model.config.cfg_file), 'adagios', 'tommi')
        )
    for k,v in adagios.settings.plugins.items():
        add_plugin(k,v)
from django.conf.urls.defaults import *

def add_plugin(name="myplugin", modulepath=None):
    """ Adds a new django application dynamically to adagios.

    """
    if name in active_plugins:
        return None
    if not modulepath:
        modulepath=name

    plugin_module = __import__(modulepath, fromlist=modulepath.split()).__file__
    #print "modulepath", modulepath, amodule.__file__
    template_dir = os.path.dirname(plugin_module) + "/templates/"


    active_plugins[name] = modulepath

    # Add plugin to INSTALLED_APPLICATIONS
    #import adagios.settings
    #adagios.settings.INSTALLED_APPS.append(modulepath)
    # Add plugin to urls
    import adagios.urls
    new_pattern = patterns('',
        (r'^%s'%name, include("%s.urls" % modulepath) ),
    )
    adagios.urls.urlpatterns += new_pattern
    # if plugin has menubar items, find them and list them
    if os.path.isfile(template_dir + "%s_menubar_misc.html" %name):
        misc_menubar_items.append( "%s_menubar_misc.html" % name)
    if os.path.isfile(template_dir + "%s_menubar.html" %name):
        menubar_items.append( "%s_menubar.html" % name)



try:
    import pynag.Model
    startup()
except Exception:
    pass
