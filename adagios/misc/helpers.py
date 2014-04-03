#!/usr/bin/python

"""

Convenient stateless functions for pynag. This module is used by the /rest/ interface of adagios.

"""


import platform
import re
from pynag import Model
from pynag import Parsers
from pynag import Control
from pynag import Utils
from pynag import __version__
from socket import gethostbyname_ex
import adagios.settings
from django.utils.translation import ugettext as _


#_config = Parsers.config(adagios.settings.nagios_config)
#_config.parse()
version = __version__


def _get_dict(x):
    x.__delattr__('objects')
    return x._original_attributes


def get_objects(object_type=None, with_fields="id,shortname,object_type", **kwargs):
    """ Get any type of object definition in a dict-compatible fashion

        Arguments:
            object_type (optional) -- Return objects of this type
            with_fields (optional) -- comma seperated list of objects to show (default=id,shortname,object_type)
            any other argument is passed on as a filter to pynag
        Examples:
            # show all active hosts and their ip address
            get_objects(object_type="host", register="1", with_fields="host_name,address")
            # show all attributes of all services
            get_objects(object_type="service", with_fields='*')
        Returns:
            List of ObjectDefinition
    """

    tmp = Model.ObjectDefinition.objects.filter(
        object_type=object_type, **kwargs)
    with_fields = with_fields.split(',')
    # return map(lambda x: _get_dict(x), tmp)
    return map(lambda x: object_to_dict(x, attributes=with_fields), tmp)


def servicestatus(with_fields="host_name,service_description,current_state,plugin_output"):
    """ Returns a list of all active services and their current status """
    s = Parsers.status()
    s.parse()
    fields = with_fields.split(',')
    result_list = []
    for serv in s.data['servicestatus']:
        current_object = {}
        for k, v in serv.items():
            if fields == ['*'] or k in fields:
                current_object[k] = v
        result_list.append(current_object)
    return result_list


def object_to_dict(object, attributes="id,shortname,object_type"):
    """ Takes in a specific object definition, returns a hash maps with "attributes" as keys"""
    result = {}
    if not attributes or attributes == '*':
        return object._original_attributes
    elif isinstance(attributes, list):
        pass
    else:
        attributes = attributes.split(',')
    for k in attributes:
        result[k] = object[k]
    return result


def get_object(id, with_fields="id,shortname,object_type"):
    """Returns one specific ObjectDefinition"""
    o = Model.ObjectDefinition.objects.get_by_id(id)
    return object_to_dict(o, attributes=with_fields)


def delete_object(object_id, recursive=False, cleanup_related_items=True):
    """ Delete one specific ObjectDefinition

    Arguments:
      object_id             -- The pynag id of the definition you want to delete
      cleanup_related_items -- If True, clean up references to this object in other definitions
      recursive             -- If True, also remove other objects that depend on this one.
                               For example, when deleting a host, also delete all its services
    Returns:
      True on success. Raises exception on failure.
    """

    o = Model.ObjectDefinition.objects.get_by_id(object_id)
    o.delete(recursive=recursive, cleanup_related_items=cleanup_related_items)
    return True


def get_host_names(invalidate_cache=False):
    """ Returns a list of all hosts """
    if invalidate_cache is True:
        raise NotImplementedError()
    all_hosts = Model.Host.objects.all
    hostnames = []
    for i in all_hosts:
        if not i['host_name'] is None:
            hostnames.append(i['host_name'])
    return sorted(hostnames)


def change_attribute(id, attribute_name, new_value):
    """Changes object with the designated ID to file

    Arguments:
        id                -- object_id of the definition to be saved
        attribute_name    -- name of the attribute (i.e. "host_name")
        new_value         -- new value (i.e. "host.example.com")
    """
    o = Model.ObjectDefinition.objects.get_by_id(id)
    o[attribute_name] = new_value
    o.save()


def change_service_attribute(identifier, new_value):
    """
    Change one service that is identified in the form of:
    host_name::service_description::attribute_name

    Examples:
    >>> change_service_attribute("localhost::Ping::service_description", "Ping2")

    Returns:
        True on success,
    Raises:
        Exception on error
    """
    tmp = identifier.split('::')
    if len(tmp) != 3:
        raise ValueError(
            "identifier must be in the form of host_name::service_description::attribute_name (got %s)" % identifier)
    host_name, service_description, attribute_name = tmp
    try:
        service = Model.Service.objects.get_by_shortname(
            "%s/%s" % (host_name, service_description))
    except KeyError, e:
        raise KeyError("Could not find service %s" % e)
    service[attribute_name] = new_value
    service.save()
    return True


def copy_object(object_id, recursive=False, **kwargs):
    """ Copy one objectdefinition.

    Arguments:
        object_id -- id of the object to be copied
        recursive -- If True, also copy related child objects
        **kwargs  -- Any other argument will be treated as an attribute
                  -- to change on the new object
    Returns:
        "Object successfully copied"
    Examples:
        copy_object(1234567890, host_name=new_hostname)
        "Object successfully copied to <filename>"
    """
    o = Model.ObjectDefinition.objects.get_by_id(object_id)
    new_object = o.copy(recursive=recursive, **kwargs)
    return "Object successfully copied to %s" % new_object.get_filename()


def run_check_command(object_id):
    """ Runs the check_command for one specified object

    Arguments:
        object_id         -- object_id of the definition (i.e. host or service)
    Returns:
        [return_code,stdout,stderr]
    """
    if platform.node() == 'adagios.opensource.is':
        return 1, 'Running check commands is disabled in demo-environment'
    o = Model.ObjectDefinition.objects.get_by_id(object_id)
    return o.run_check_command()


def set_maincfg_attribute(attribute, new_value, old_value='None', append=False):
    """ Sets specific configuration values of nagios.cfg

        Required Arguments:
                attribute   -- Attribute to change (i.e. process_performance_data)
                new_value   -- New value for the attribute (i.e. "1")

        Optional Arguments:
                old_value   -- Specify this to change specific value
                filename    -- Configuration file to modify (i.e. /etc/nagios/nagios.cfg)
                append      -- Set to 'True' to append a new configuration attribute
        Returns:
                True	-- If any changes were made
                False	-- If no changes were made
        """
    filename = Model.config.cfg_file
    if old_value.lower() == 'none':
        old_value = None
    if new_value.lower() == 'none':
        new_value = None
    if filename.lower() == 'none':
        filename = None
    if append.lower() == 'false':
        append = False
    elif append.lower() == 'true':
        append = True
    elif append.lower() == 'none':
        append = None
    return Model.config._edit_static_file(attribute=attribute, new_value=new_value, old_value=old_value, filename=filename, append=append)


def reload_nagios():
    """ Reloads nagios. Returns "Success" on Success """
    daemon = Control.daemon(
        nagios_cfg=Model.config.cfg_file,
        nagios_init=adagios.settings.nagios_init_script,
        nagios_bin=adagios.settings.nagios_binary
    )
    result = {}
    if daemon.reload() == 0:
        result['status'] = "success"
        result['message'] = 'Nagios Successfully reloaded'
    else:
        result['status'] = "error"
        result['message'] = "Failed to reload nagios (do you have enough permissions?)"
    return result


def needs_reload():
    """ Returns True if Nagios server needs to reload configuration """
    return Model.config.needs_reload()


def dnslookup(host_name):
    try:
        (name, aliaslist, addresslist) = gethostbyname_ex(host_name)
        return {'host': name, 'aliaslist': aliaslist, 'addresslist': addresslist}
    except Exception, e:
        return {'error': str(e)}


def contactgroup_hierarchy(**kwargs):
    result = []
    try:
        groups = Model.Contactgroup.objects.all
        for i in groups:
            display = {}
            display['v'] = i.contactgroup_name
            display['f'] = '%s<div style="color:green; font-style:italic">%s contacts</div>' % (
                i.contactgroup_name, 0)
            arr = [display, i.contactgroup_members or '', str(i)]
            result.append(arr)
        return result
    except Exception, e:
        return {'error': str(e)}


def add_object(object_type, filename=None, **kwargs):
    """ Create one specific object definition and store it in nagios.

    Arguments:
        object_type  -- What kind of object to create (host, service,contactgroup, etc)
        filename     -- Which configuration file to store the object in. If filename=None pynag will decide
                     -- where to store the file
        **kwargs     -- Any other arguments will be treated as an attribute for the new object definition

    Returns:
        {'filename':XXX, 'raw_definition':XXX}
    Examples:
        add_object(object_type=host, host_name="localhost.example", address="127.0.0.1", use="generic-host"
    """
    my_object = Model.string_to_class.get(object_type)()
    if filename is not None:
        my_object.set_filename(filename)
    for k, v in kwargs.items():
        my_object[k] = v
    my_object.save()
    return {"filename": my_object.get_filename(), "raw_definition": str(my_object)}


def check_command(host_name, service_description, name=None, check_command=None, **kwargs):
    """ Returns all macros of a given service/host
        Arguments:
            host_name           -- Name of host
            service_description -- Service description
            check_command       -- Name of check command

            Any **kwargs will be treated as arguments or custom macros that will be changed on-the-fly before returning
        Returns:
            dict similar to the following:
            { 'host_name': ...,
              'service_description': ...,
              'check_command': ...,
              '$ARG1$': ...,
              '$SERVICE_MACROx$': ...,
            }
    """
    if host_name in ('None', None, ''):
        my_object = Model.Service.objects.get_by_name(name)
    elif service_description in ('None', None, '', u''):
        my_object = Model.Host.objects.get_by_shortname(host_name)
    else:
        short_name = "%s/%s" % (host_name, service_description)
        my_object = Model.Service.objects.get_by_shortname(short_name)
    if check_command in (None, '', 'None'):
        command = my_object.get_effective_check_command()
    else:
        command = Model.Command.objects.get_by_shortname(check_command)

    # Lets put all our results in a nice little dict
    macros = {}
    cache = Model.ObjectFetcher._cache_only
    try:
        Model.ObjectFetcher._cache_only = True
        macros['check_command'] = command.command_name
        macros['original_command_line'] = command.command_line
        macros['effective_command_line'] = my_object.get_effective_command_line()

        # Lets get all macros that this check command defines:
        regex = re.compile("(\$\w+\$)")
        macronames = regex.findall(command.command_line)
        for i in macronames:
            macros[i] = my_object.get_macro(i) or ''

        if not check_command:
            # Argument macros are special (ARGX), lets display those as is, without resolving it to the fullest
            ARGs = my_object.check_command.split('!')
            for i, arg in enumerate(ARGs):
                if i == 0:
                    continue

                macronames = regex.findall(arg)
                for m in macronames:
                    macros[m] = my_object.get_macro(m) or ''
                macros['$ARG{i}$'.format(i=i)] = arg
    finally:
        Model.ObjectFetcher._cache_only = cache
    return macros


def verify_configuration():
    """ Verifies nagios configuration and returns the output of nagios -v nagios.cfg
    """
    binary = adagios.settings.nagios_binary
    config = adagios.settings.nagios_config
    command = "%s -v '%s'" % (binary, config)
    code, stdout, stderr = Utils.runCommand(command)

    result = {}
    result['return_code'] = code
    result['output'] = stdout
    result['errors'] = stderr

    return result


def get_object_statistics():
    """ Returns a list of all object_types with total number of configured objects

    Example result:
    [
      {"object_type":"host", "total":50},
      {"object_type":"service", "total":50},
    ]
    """
    object_types = []
    Model.ObjectDefinition.objects.reload_cache()
    for k, v in Model.ObjectFetcher._cached_object_type.items():
        total = len(v)
        object_types.append({"object_type": k, "total": total})
    return object_types


def autocomplete(q):
    """ Returns a list of {'hosts':[], 'hostgroups':[],'services':[]} matching search query q
    """
    if q is None:
        q = ''
    result = {}

    hosts = Model.Host.objects.filter(host_name__contains=q)
    services = Model.Service.objects.filter(service_description__contains=q)
    hostgroups = Model.Hostgroup.objects.filter(hostgroup_name__contains=q)

    result['hosts'] = sorted(set(map(lambda x: x.host_name, hosts)))
    result['hostgroups'] = sorted(set(map(lambda x: x.hostgroup_name, hostgroups)))
    result['services'] = sorted(set(map(lambda x: x.service_description, services)))

    return result
