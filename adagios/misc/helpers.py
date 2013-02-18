#!/usr/bin/python

'''

Convenient stateless functions for pynag. This module is used by the /rest/ interface of adagios.

'''



from pynag import Model
from pynag import Parsers
from pynag import Control
from pynag import __version__
from socket import gethostbyname_ex
import adagios.settings

_config = Parsers.config(adagios.settings.nagios_config)
_config.parse()
maincfg_values = _config.maincfg_values
cfg_file = _config.cfg_file
version = __version__

def _get_dict(x):
    x.__delattr__('objects')
    return x._original_attributes
#__dict__
#_get_dict = lambda x: del (x.objects)
#timeperiods = map(_get_dict, Model.Timeperiod.objects.all) 
#hosts = map(_get_dict, Model.Host.objects.all )
#contacts = map(_get_dict, Model.Contact.objects.all )
#services = map(_get_dict, Model.Service.objects.all )
#contactgroups = map(_get_dict, Model.Contactgroup.objects.all )
#hostgroups = map(_get_dict, Model.Hostgroup.objects.all )

def get_objects(object_type=None, with_fields="id,shortname,object_type", **kwargs):
    ''' Get any type of object definition in a dict-compatible fashion

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
    '''
    tmp = Model.ObjectDefinition.objects.filter(object_type=object_type, **kwargs)
    return map( lambda x: object_to_dict(x, attributes=with_fields), tmp)

def servicestatus(with_fields="host_name,service_description,current_state,plugin_output"):
    """ Returns a list of all active services and their current status """
    s = Parsers.status()
    s.parse()
    fields = with_fields.split(',')
    result_list = []
    for serv in s.data['servicestatus']:
        current_object = {}
        for k,v in serv.items():
            if fields == ['*'] or k in fields:
                current_object[k] = v
        result_list.append( current_object )
    return result_list

def object_to_dict(object, attributes="id,shortname,object_type"):
    """ Takes in a specific object definition, returns a hash maps with "attributes" as keys"""
    result = {}
    if not attributes or attributes == '*':
        attributes=object.keys()
    else:
        attributes=attributes.split(',')
    for k in attributes:
        result[k] = object[k]
    return result
def get_object(id):
    '''Returns one specific ObjectDefinition'''
    o = Model.ObjectDefinition.objects.get_by_id(id)
    del o.objects
    return o
def delete_object(object_id, cascade=False):
    '''Delete one specific ObjectDefinition'''
    try:
        o = Model.ObjectDefinition.objects.get_by_id(id)
        o.delete(cascade=cascade)
        return True
    except Exception:
        return False
def get_host_names(invalidate_cache=False):
    """ Returns a list of all hosts """
    if invalidate_cache is True:
        raise NotImplementedError()
    all_hosts = Model.Host.objects.all
    hostnames = []
    for i in all_hosts:
        if not i['host_name'] is None:
            hostnames.append( i['host_name'])
    return sorted( hostnames )
def change_attribute(id, attribute_name, new_value):
    '''Changes object with the designated ID to file
    
    Arguments:
        id                -- object_id of the definition to be saved
        attribute_name    -- name of the attribute (i.e. "host_name")
        new_value         -- new value (i.e. "host.example.com")
    '''
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
        raise ValueError("identifier must be in the form of host_name::service_description::attribute_name (got %s)" % identifier)
    host_name,service_description,attribute_name = tmp
    try:
        service = Model.Service.objects.get_by_shortname("%s/%s" % (host_name,service_description))
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
    ''' Runs the check_command for one specified object
    
    Arguments:
        object_id         -- object_id of the definition (i.e. host or service)
    Returns:
        [return_code,stdout,stderr]
    '''
    o = Model.ObjectDefinition.objects.get_by_id(object_id)
    return o.run_check_command()

def set_maincfg_attribute(attribute,new_value, old_value='None', append=False):
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
    filename = _config.cfg_file
    if old_value.lower() == 'none': old_value=None
    if new_value.lower() == 'none': new_value=None
    if filename.lower() == 'none': filename=None
    if append.lower() == 'false': append=False
    elif append.lower() == 'true': append=True
    elif append.lower() == 'none': append=None
    return _config._edit_static_file(attribute=attribute,new_value=new_value,old_value=old_value,filename=filename, append=append)

def reload_nagios():
    """ Reloads nagios. Returns "Success" on Success """
    daemon = Control.daemon(nagios_cfg=Model.config.cfg_file, nagios_init='/etc/init.d/nagios3', nagios_bin='/usr/sbin/nagios3')
    if daemon.reload() == 0:
        return "Success"
    else:
        return "Failed to reload nagios (do you have enough permission?)"
def needs_reload():
    """ Returns True if Nagios server needs to reload configuration """
    return Model.config.needs_reload()


def dnslookup(host_name):
    try:
        (name, aliaslist, addresslist) = gethostbyname_ex(host_name)
        return { 'host': name, 'aliaslist': aliaslist, 'addresslist': addresslist }
    except Exception, e:
        return { 'error': str(e) }

def contactgroup_hierarchy(**kwargs):
    result = []
    try:
        groups = Model.Contactgroup.objects.all
        for i in groups:
            display = {}
            display['v'] = i.contactgroup_name
            display['f'] = '%s<div style="color:green; font-style:italic">%s contacts</div>' % (i.contactgroup_name, 0)
            arr = [ display, i.contactgroup_members or '', str(i)]
            result.append( arr )
        return result
    except Exception,e :
        return { 'error': str(e) }
