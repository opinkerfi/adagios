#!/usr/bin/python

'''
Convenient stateless functions for pynag
'''



from pynag import Model
from pynag import Parsers
from socket import gethostbyname_ex
_config = Parsers.config()
_config.parse()
maincfg_values = _config.maincfg_values
cfg_file = _config.cfg_file

def _get_dict(x):
    #print "deleted"
    #print type(x)
    x.__delattr__('objects')
    #del x._original_attributes['meta']
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
        
        Examples:
            get_objects(object_type="host", register="1")
        Returns:
            List of ObjectDefinition
    '''
    tmp = Model.ObjectDefinition.objects.filter(object_type=object_type, **kwargs)
    return map( lambda x: object_to_dict(x, attributes=with_fields), tmp)
''' Get All hosts '''
#host_names = []
#for _h in hosts:
#    if _h.has_key('host_name'):
#        host_names.append( _h[host_name] )

def object_to_dict(object, attributes="id,shortname,object_type"):
    """ Takes in a specific object definition, returns a hash maps with "attributes" as keys"""
    result = {}
    for k in attributes.split(','):
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
    except:
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
def run_check_command(object_id):
    ''' Runs the check_command for one specified object
    
    Arguments:
        object_id         -- object_id of the definition (i.e. host or service)
    Returns:
        [return_code,stdout,stderr]
    '''
    o = Model.ObjectDefinition.objects.get_by_id(object_id)
    return o.run_check_command()

def set_maincfg_attribute(attribute,new_value, old_value='None', filename='None', append=False):
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
    if old_value.lower() == 'none': old_value=None
    if new_value.lower() == 'none': new_value=None
    if filename.lower() == 'none': filename=None
    if append.lower() == 'false': append=False
    elif append.lower() == 'true': append=True
    elif append.lower() == 'none': append=None
    return _config._edit_static_file(attribute=attribute,new_value=new_value,old_value=old_value,filename=filename, append=append)


def dnslookup(host_name):
    try:
        (name, aliaslist, addresslist) = gethostbyname_ex(host_name)
        return { 'host': name, 'aliaslist': aliaslist, 'addresslist': addresslist }
    except Exception, e:
        return { 'error': str(e) }