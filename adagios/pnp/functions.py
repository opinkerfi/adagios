import os

import pynag.Utils
from pynag.Utils import PynagError
from adagios import settings
import subprocess


def run_pnp(pnp_command, **kwargs):
    """ Run a specific pnp command

    Arguments:
      pnp_command -- examples: image graph json xml export
      host        -- filter results for a specific host
      srv         -- filter results for a specific service
      source      -- Fetch a specific datasource (0,1,2,3, etc)
      view        -- Specific timeframe (0 = 4 hours, 1 = 25 hours, etc)
    Returns:
      Results as they appear from pnp's index.php
    Raises:
      PynagError if command could not be run

    """
    try:
        pnp_path = settings.pnp_path
    except Exception, e1:
        pnp_path = find_pnp_path()
    # Cleanup kwargs
    pnp_arguments = {}
    for k, v in kwargs.items():
        k = str(k)
        if isinstance(v, list):
            v = v[0]
        v = str(v)
        pnp_arguments[k] = v
    querystring = '&'.join(map(lambda x: "%s=%s" % x, pnp_arguments.items()))
    pnp_parameters = pnp_command + "?" + querystring
    command = ['php', pnp_path, pnp_parameters]
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
    stdout, stderr = proc.communicate('through stdin to stdout')
    result = proc.returncode, stdout, stderr
    return result[1]


def find_pnp_path():
    """ Look through common locations of pnp4nagios, tries to locate it automatically """
    possible_paths = [settings.pnp_filepath]
    possible_paths += [
        "/usr/share/pnp4nagios/html/index.php",
        "/usr/share/nagios/html/pnp4nagios/index.php"
    ]
    for i in possible_paths:
        if os.path.isfile(i):
            return i
    raise PynagError(
        _("Could not find pnp4nagios/index.php. Please specify it in adagios->settings->PNP. Tried %s") % possible_paths)
