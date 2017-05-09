# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Pall Sigurdsson <palli@opensource.is>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Django settings for adagios project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG
USE_TZ = True

# Hack to allow relative template paths
import os
from glob import glob
from warnings import warn
import string

djangopath = os.path.dirname(__file__)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS
STATIC_URL = "/media/"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/test',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
# TIME_ZONE = 'Atlantic/Reykjavik'
TIME_ZONE = None
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True


STATIC_URL = '/media/'
STATIC_ROOT = '%s/media/' % djangopath

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = '/media/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'adagios.auth.AuthorizationMiddleWare',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
)

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

LANGUAGES = (
    ('en', 'English'),
    ('fr', 'French'),
)

LOCALE_PATHS = (
    "%s/locale/" % (djangopath),
)

ROOT_URLCONF = 'adagios.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "%s/templates" % (djangopath),
)

INSTALLED_APPS = [
    #'django.contrib.auth',
    #'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    #'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    #'django.contrib.staticfiles',
    'adagios.objectbrowser',
    'adagios.rest',
    'adagios.misc',
    'adagios.pnp',
    'adagios.contrib',
]

TEMPLATE_CONTEXT_PROCESSORS = ('adagios.context_processors.on_page_load',
    #"django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    #"django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages")


# Themes options #
# To rapidly switch your theme, update THEME_DEFAULT and leave the rest.

# folders in which themes files will be looked up
THEMES_FOLDER = 'themes'  # in 'media/'

# default theme in use, it should be present in the THEMES_FOLDER
# (or at least through a symbolic link)
THEME_DEFAULT = 'default'

# CSS entry-point, in the theme folder
THEME_ENTRY_POINT = 'style.css'

# folder where users preferences are stored
USER_PREFS_PATH = "/var/lib/adagios/userdata/"


# name displayed in the top left corner
TOPMENU_HOME = 'Adagios'

# items in the top menubar (excluding those coming from %s_menubar.html)
# The identfier is used to recognize active links (which are displayed
# differently).
# The view can begin with '/' (and will go to http://server/...)
# or can be a view name.
# See Nagvis example for direct link, though the template contrib/nagvis.html must be created.
TOPMENU_ITEMS = [
    # Name,        identifier,      view_url,                                icon
    # ('Nagvis',  'nagvis',        '/contrib/nagvis.html',                  'glyph-display'),
    ('Configure', 'objectbrowser', 'objectbrowser.views.list_object_types', 'glyph-edit'),
    ('Nagios',    'nagios',        'misc.views.nagios',                     'glyph-list'),

]

# This mapping shows how we define a service as 'unhandled'
UNHANDLED_SERVICES = {
    'state__isnot': 0,
    'acknowledged': 0,
    'scheduled_downtime_depth': 0,
    'host_state': 0,
    'host_scheduled_downtime_depth': 0,
    'host_acknowledged': 0,
}


# This mapping shows how we define a host as 'unhandled'
UNHANDLED_HOSTS = {
    'state': 1,
    'acknowledged': 0,
    'scheduled_downtime_depth': 0
}

# A list of strings representing the host/domain names that this Django site can
# serve. This is a security measure to prevent HTTP Host header attacks
# Values in this list can be fully qualified names (e.g. www.example.com)
# A value beginning with a period can be used as a subdomain wildcard:
# '.example.com' will match example.com, www.example.com
# A value of '*' will match anything
ALLOWED_HOSTS = ['*']

# Graphite #

# the url where to fetch data and images
graphite_url = "http://localhost:9091"

# time ranges for generated graphs
# the CSS identifier only needs to be unique here (it will be prefixed)
GRAPHITE_PERIODS = [
    # Displayed name, CSS identifier, Graphite period
    ('4 hours',       'hours',        '-4h'),
    ('One day',       'day',          '-1d'),
    ('One week',      'week',         '-1w'),
    ('One month',     'month',        '-1mon'),
    ('One year',      'year',         '-1y'),
    ]

# querystring that will be passed on to graphite's render method.
graphite_querystring = "target={host_}.{service_}.{metric_}&width=500&height=200&from={from_}d&lineMode=connected&title={title}&target={host_}.{service_}.{metric_}_warn&target={host_}.{service_}.{metric_}_crit"

# Title format to use on all graphite graphs
graphite_title = "{host} - {service} - {metric}"

# default selected (active) tab, and the one rendered in General-preview
GRAPHITE_DEFAULT_TAB = 'day'

# Adagios specific configuration options. These are just the defaults,
# Anything put in /etc/adagios.d/adagios.conf will overwrite this.
nagios_config = None  # Sensible default is "/etc/nagios/nagios.cfg"
nagios_url = "/nagios"
# define if you are using a sysv5 init script
nagios_init_script = None
nagios_service = "nagios"
nagios_binary = "/usr/bin/nagios"
livestatus_path = None
livestatus_limit = 500
default_host_template = 'generic-host'
default_service_template = 'generic-service'
default_contact_template = 'generic-contact'
enable_githandler = False
enable_loghandler = False
enable_authorization = False
enable_status_view = True
enable_bi = True
enable_pnp4nagios = True
enable_graphite = False
enable_local_logs = True
contrib_dir = "/var/lib/adagios/contrib/"
serverside_includes = "/etc/adagios/ssi"
escape_html_tags = True
warn_if_selinux_is_active = True
destination_directory = "/etc/nagios/adagios/"
administrators = "nagiosadmin,@users"
pnp_url = "/pnp4nagios"
pnp_filepath = "/usr/share/nagios/html/pnp4nagios/index.php"
include = ""
django_secret_key = ""
map_center = "64.119595,-21.655426"
map_zoom = "10"
title_prefix = "Adagios - "
auto_reload = False
refresh_rate = "30"

plugins = {}

# Profiling settings
#
# You can use the @profile("filename") to profile single functions within
# adagios. Not enabled by default on any function.
#
# Documenations at
# https://github.com/opinkerfi/adagios/wiki/Profiling-Decorators-within-Adagios
PROFILE_LOG_BASE = "/var/lib/adagios"

# Load config files from /etc/adagios
# Adagios uses the configuration file in /etc/adagios/adagios.conf by default.
# If it doesn't exist you should create it. Otherwise a adagios.conf will be
# created in the django project root which should be avoided.
adagios_configfile = "/etc/adagios/adagios.conf"


def reload_configfile(adagios_configfile=None):
    "Process adagios.conf style file and any includes; updating the settings"
    if not adagios_configfile:
        adagios_configfile = globals()['adagios_configfile']
    try:
        if not os.path.exists(adagios_configfile):
            alternative_adagios_configfile = "%s/adagios.conf" % djangopath
            message = "Config file '{adagios_configfile}' not found. Using {alternative_adagios_configfile} instead."
            warn(message.format(**locals()))
            adagios_configfile = alternative_adagios_configfile
            open(adagios_configfile, "a").close()

        execfile(adagios_configfile, globals())
        # if config has any default include, lets include that as well
        configfiles = glob(include)
        for configfile in configfiles:
            execfile(configfile, globals())
    except IOError, e:
        warn('Unable to open %s: %s' % (adagios_configfile, e.strerror))

reload_configfile()

try:
    from django.utils.crypto import get_random_string
except ImportError:
    def get_random_string(length, stringset=string.ascii_letters + string.digits + string.punctuation):
        '''
        Returns a string with `length` characters chosen from `stringset`
        >>> len(get_random_string(20)) == 20
        '''
        return ''.join([stringset[i % len(stringset)] for i in [ord(x) for x in os.urandom(length)]])

if not django_secret_key:
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    SECRET_KEY = get_random_string(50, chars)
    try:
        data = "\n# Automaticly generated secret_key\ndjango_secret_key = '%s'\n" % SECRET_KEY
        with open(adagios_configfile, "a") as config_fh:
            config_fh.write(data)
    except Exception, e:
        warn("ERROR: Got %s while trying to save django secret_key in %s" % (type(e), adagios_configfile))

else:
    SECRET_KEY = django_secret_key

ALLOWED_INCLUDE_ROOTS = (serverside_includes,)

if enable_status_view:
    plugins['status'] = 'adagios.status'
if enable_bi:
    plugins['bi'] = 'adagios.bi'

for k, v in plugins.items():
    INSTALLED_APPS.append(v)

# default preferences, for new users or when they are not available
PREFS_DEFAULT = {
    'language': 'en',
    'theme': THEME_DEFAULT,
    'refresh_rate': refresh_rate
}

# Allow tests to run server on multiple ports
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000-9000'
