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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '/tmp/test',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
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


# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = "%s/media/" % (djangopath)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'media/'

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
    #'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
)

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
    #'django.contrib.sessions',
    'django.contrib.sites',
    #'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
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
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages")

 


# Adagios specific configuration options. These are just the defaults,
# Anything put in /etc/adagios.d/adagios.conf will overwrite this.
nagios_config=None # Sensible default is "/etc/nagios/nagios.cfg"
nagios_url="/nagios"
nagios_init_script = "/etc/init.d/nagios"
nagios_binary = "/usr/bin/nagios"
livestatus_path = None
enable_githandler=False
enable_loghandler = False
enable_authorization = False
enable_status_view = True
enable_bi = True
contrib_dir = "/var/lib/adagios/contrib/"
serverside_includes = "/etc/adagios/ssi"
escape_html_tags = True
warn_if_selinux_is_active = True
destination_directory="/etc/nagios/adagios/"
administrators="nagiosadmin,@users"
pnp_url = "/pnp4nagios"
pnp_filepath = "/usr/share/nagios/html/pnp4nagios/index.php"
include=""
django_secret_key = ""
map_center = "64.119595,-21.655426"
map_zoom = "10"
title_prefix = "Adagios - "
auto_reload = False

plugins = {}

# Load config files from /etc/adagios
# Adagios uses the configuration file in /etc/adagios/adagios.conf by default.
# If it doesn't exist you should create it. Otherwise a adagios.conf will be
# created in the django project root which should be avoided.
adagios_configfile = "/etc/adagios/adagios.conf"

# Try to save a configuration file into the project djangopath
if not os.path.exists(adagios_configfile):
    adagios_configfile = "%s/adagios.conf" % djangopath
    open(adagios_configfile, "a").close()

try:
    execfile(adagios_configfile)
    # if config has any default include, lets include that as well
    configfiles = glob(include)
    for configfile in configfiles:
        execfile(configfile)
except IOError, e:
    # Only raise on errors other than file not found (missing config is OK)
    if e.errno != 2:
        raise Exception('Unable to open %s: %s' % (adagios_configfile, e.strerror))
    # Warn on missing configs
    else:
        # TODO: Should this go someplace?
        warn('Unable to open %s: %s' % (adagios_configfile, e.strerror))

try:
    from django.utils.crypto import get_random_string
except ImportError:
    def get_random_string(length, stringset=string.ascii_letters+string.digits+string.punctuation):
        '''
        Returns a string with `length` characters chosen from `stringset`
        >>> len(get_random_string(20)) == 20
        '''
        return ''.join([stringset[i%len(stringset)] \
            for i in [ord(x) for x in os.urandom(length)]])

if not django_secret_key:
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    SECRET_KEY = get_random_string(50, chars)
    try:
        data = "\n# Automaticly generated secret_key\ndjango_secret_key = '%s'\n" % SECRET_KEY
        with open(adagios_configfile, "a") as config_fh:
            config_fh.write(data)
    except Exception, e:
        print("ERROR: Got %s while trying to save django secret_key in %s" % (type(e), adagios_configfile))

else:
    SECRET_KEY = django_secret_key

ALLOWED_INCLUDE_ROOTS = (serverside_includes,)

if enable_status_view:
    plugins['status'] = 'adagios.status'
if enable_bi:
    plugins['bi'] = 'adagios.bi'

for k,v in plugins.items():
    INSTALLED_APPS.append( v )

