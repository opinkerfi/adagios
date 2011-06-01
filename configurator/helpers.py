#!/usr/bin/python

'''
Convenient stateless functions for pynag
'''

import sys

sys.path.insert(1,'/opt/pynag')
from pynag import Model

def _get_dict(x):
    #print "deleted"
    #print type(x)
    x.__delattr__('objects')
    #del x._original_attributes['meta']
    return x._original_attributes
#__dict__
#_get_dict = lambda x: del (x.objects)
''' Fetch some objects '''
timeperiods = map(_get_dict, Model.Timeperiod.objects.all) 
hosts = map(_get_dict, Model.Host.objects.all )
contacts = map(_get_dict, Model.Contact.objects.all )
services = map(_get_dict, Model.Service.objects.all )
contactgroups = map(_get_dict, Model.Contactgroup.objects.all )
hostgroups = map(_get_dict, Model.Hostgroup.objects.all )

''' Get All hosts '''
#host_names = []
#for _h in hosts:
#    if _h.has_key('host_name'):
#        host_names.append( _h[host_name] )

def get_object(id):
    '''Returns one specific ObjectDefinition'''
    o = Model.ObjectDefinition.objects.get_by_id(id)
    del o.objects
    return o

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
