import os.path

__version__='1.2.7'

notifications = {}
active_plugins = {}
misc_menubar_items = []
menubar_items = []

def add_plugin(name="myplugin", modulepath=None):
    """ Adds a new django application dynamically to adagios.

    """
    if name in active_plugins:
        return None
    if not modulepath:
        modulepath=name

    plugin_module = __import__(modulepath, fromlist=modulepath.split()).__file__
    template_dir = os.path.dirname(plugin_module) + "/templates/"


    active_plugins[name] = modulepath

    # Add plugin to INSTALLED_APPLICATIONS
    #import adagios.settings
    #adagios.settings.INSTALLED_APPS.append(modulepath)
    # Add plugin to urls
    import adagios.urls
    from django.conf.urls.defaults import patterns,include
    new_pattern = patterns('',
        (r'^%s'%name, include("%s.urls" % modulepath) ),
    )
    adagios.urls.urlpatterns += new_pattern
    # if plugin has menubar items, find them and list them
    if os.path.isfile(template_dir + "%s_menubar_misc.html" %name):
        misc_menubar_items.append( "%s_menubar_misc.html" % name)
    if os.path.isfile(template_dir + "%s_menubar.html" %name):
        menubar_items.append( "%s_menubar.html" % name)



# Any plugins og third party extensions to adagios are loaded here.
# We will silently ignore any errors and make sure that the webserver
# will successfully start up if any of the plugins have errors
try:
    from adagios import settings
    for k,v in settings.plugins.items():
        try:
            add_plugin(k,v)
        except Exception:
            pass
except Exception:
    pass

