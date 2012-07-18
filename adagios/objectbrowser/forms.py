# -*- coding: utf-8 -*-
#
# Copyright 2010, Pall Sigurdsson <palli@opensource.is>
#
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from django import forms
#from django.forms import *
from pynag import Model
from pynag.Model.all_attributes import object_definitions
from django.utils.encoding import smart_str
from pynag.Model import ObjectDefinition


# These fields are special, they are a comma seperated list, and may or may not have +/- in front of them.
MULTICHOICE_FIELDS = ('servicegroups','hostgroups','contacts','contact_groups', 'contactgroups', 'use', 'notification_options')

NOTIFICATION_OPTIONS = (
                        ('w','warning'),
                        ('c','critical'),
                        ('r','recovery'),
                        ('u','unreachable'),
                        ('d','downtime'),
                        ('f','flapping'),
                        )

BOOLEAN_CHOICES = ( ('', 'not set'),('1','1'),('0','0'))

# List of all host_names
ALL_HOSTS = map(lambda x: (x.host_name, x.host_name),
                Model.Host.objects.filter(host_name__contains="", register="1"))
ALL_HOSTS.sort()
# List of all unregistered services (templates)
INACTIVE_SERVICES = map(lambda x: (x.name, x.name),
                        Model.Service.objects.filter(service_description__contains="", name__contains="", register="0"))
INACTIVE_SERVICES.sort()

class PynagChoiceField(forms.MultipleChoiceField):
    ''' multichoicefields that accepts comma seperated input as values '''
    def __init__(self, *args, **kwargs):
        self.__prefix = ''
        self.data = kwargs.get('data')
        super(PynagChoiceField, self).__init__(*args, **kwargs)
    def clean(self,value):
        return self.__prefix + ','.join(value)
    def prepare_value(self, value):
        if type(value) == type(''):
            if value.startswith('+'): self.__prefix = '+'
            value = value.strip('+')
            return value.split(',')
        return value

class PynagForm(forms.Form):
    def clean(self):
        for k,v in self.cleaned_data.items():
            if k in MULTICHOICE_FIELDS and self.simple == False:
                if self.pynag_object.get(k,'').startswith('+'):
                    v = self.cleaned_data[k] = "+%s"%(v)
            if k not in self.data.keys(): self.cleaned_data.pop(k)
            elif k in self.undefined_attributes and v == '': self.cleaned_data.pop(k)
            elif v == self.pynag_object[k]: self.cleaned_data.pop(k)
            elif v == '' and self.pynag_object[k] is None: self.cleaned_data.pop(k)
            else:
                self.cleaned_data[k] = smart_str(v)
        return self.cleaned_data
    def save(self):
        for k,v in self.cleaned_data.items():
            k,v = str(k), str(v)
            if self.pynag_object[k] != v:
                self.pynag_object[k] = v
                self.fields[k] = self.get_pynagField(k, css_tag="defined_attribute")
                self.fields[k].value = v
        self.pynag_object.save()
    def __init__(self, pynag_object, simple=False,show_defined_attributes=True,show_inherited_attributes=True,show_undefined_attributes=True, show_radiobuttons=True,*args, **kwargs):
        self.pynag_object = pynag_object
        self.simple = simple
        super(forms.Form,self).__init__(*args, **kwargs)
        # Lets find out what attributes to create
        object_type = pynag_object['object_type']
        defined_attributes = sorted( self.pynag_object._defined_attributes.keys() )
        inherited_attributes = sorted( self.pynag_object._inherited_attributes.keys() )
        all_attributes = sorted( object_definitions.get(object_type).keys() )
        # Calculate what attributes are "undefined"
        self.undefined_attributes = []
        for i in all_attributes:
            if i in defined_attributes: continue
            if i in inherited_attributes: continue
            self.undefined_attributes.append( i )
        # Find out which attributes to show
        for field_name in defined_attributes + inherited_attributes + self.undefined_attributes:
            if self.simple:
                self.fields[field_name] = self.get_pynagField(field_name)
            else:
                self.fields[field_name] = self.get_pynagField(field_name)
        return
    def get_pynagField(self, field_name, css_tag=""):
        """ Takes a given field_name and returns a forms.Field that is appropriate for this field """
        # Lets figure out what type of field this is, default to charfield
        object_type = self.pynag_object['object_type']
        definitions = object_definitions.get( object_type ) or {}
        options = definitions.get(field_name) or {}
        
        # Find out what type of field to create from the field_name
        # If this is the advanved_edit form, then all fields are charfields
        if self.simple == True:
            field = forms.CharField()
        elif field_name in ('contact_groups','contactgroups','contactgroup_members'):
                all_groups = Model.Contactgroup.objects.filter(contactgroup_name__contains="")
                choices = map(lambda x: (x.contactgroup_name, x.contactgroup_name), all_groups)
                field = PynagChoiceField(choices=choices)
        elif field_name == 'use':
            all_objects = self.pynag_object.objects.filter(name__contains='')
            choices = sorted( map(lambda x: (x.name, x.name), all_objects) )
            field = PynagChoiceField(choices=choices)
        elif field_name == 'servicegroups':
            all_groups = Model.Servicegroup.objects.filter(servicegroup_name__contains='')
            choices = map(lambda x: (x.servicegroup_name, x.servicegroup_name), all_groups)
            field = PynagChoiceField(choices=choices)
        elif field_name == 'hostgroups':
            all_groups = Model.Hostgroup.objects.filter(hostgroup_name__contains='')
            choices = map(lambda x: (x.hostgroup_name, x.hostgroup_name), all_groups)
            field = PynagChoiceField(choices=choices)
        elif field_name in ('contacts','members'):
            all = Model.Contact.objects.filter(contact_name__contains='')
            choices = sorted( map(lambda x: (x.contact_name, x.contact_name), all) )
            field = PynagChoiceField(choices=choices)
        elif field_name.endswith('_period'):
            all = Model.Timeperiod.objects.filter(timeperiod_name__contains='')
            choices = map(lambda x: (x.timeperiod_name, x.timeperiod_name), all)
            field = forms.ChoiceField(choices=choices)
        elif field_name.endswith('notification_commands'):
            all = Model.Command.objects.filter(command_name__contains='')
            choices = map(lambda x: (x.command_name, x.command_name), all)
            field = forms.ChoiceField(choices=choices)            
        elif field_name.endswith('notification_options'):
            field = PynagChoiceField(choices=NOTIFICATION_OPTIONS)
        elif options.get('value') == '[0/1]':
            field = forms.ChoiceField(choices=BOOLEAN_CHOICES, widget=forms.RadioSelect)
        else:
            # Fallback to a default charfield
            field = forms.CharField()
        
        # No prettyprint for macros
        if field_name.startswith('_'):
            field.label = field_name
        
        # If any CSS tag was given, add it to the widget
        self.add_css_tag(field=field, css_tag=css_tag)
        
        if options.has_key('required'):
            self.add_css_tag(field=field, css_tag=options['required'])
            field.required = options['required'] == 'required'
        else:
            field.required = False
        # At the moment, our database of required objects is incorrect
        field.required = False
        
        if field_name in MULTICHOICE_FIELDS:
            self.add_css_tag(field=field, css_tag="multichoice")
        
        return field
    def add_css_tag(self, field, css_tag):
        ''' Add a CSS tag to the widget of a specific field '''
        if not field.widget.attrs.has_key('class'):
            field.widget.attrs['class'] = ''
            field.css_tag = ''
        field.widget.attrs['class'] += " " + css_tag 
        field.css_tag += " " + css_tag
        
class GeekEditObjectForm(forms.Form):
    definition= forms.CharField( widget=forms.Textarea(attrs={ 'wrap':'off', 'cols':'80'}) )
    def __init__(self,pynag_object=None, *args,**kwargs):
        self.pynag_object = pynag_object
        super(GeekEditObjectForm, self).__init__(*args,**kwargs)
    def clean_definition(self, value=None):
        definition = self.cleaned_data['definition']
        definition = definition.replace('\r\n', '\n')
        definition = definition.replace('\r', '\n')
        if not definition.endswith('\n'):
            definition += '\n'
        return definition
    def save(self):
        definition = self.cleaned_data['definition']
        self.pynag_object.rewrite( str_new_definition=definition )

class AddServiceToHostForm(forms.Form):
    host_name = forms.ChoiceField(choices=ALL_HOSTS)
    service = forms.ChoiceField(choices=INACTIVE_SERVICES)

class EditManyForm(forms.Form):
    """ To make changes to multiple objects at once """
    attribute_name = forms.CharField()
    new_value = forms.CharField()
    def __init__(self, objects=[],*args, **kwargs):
        self.objects = []
        self.all_objects = []
        self.changed_objects = []
        super(EditManyForm, self).__init__(*args,**kwargs)

    def save(self):
        for i in self.changed_objects:
            key = self.cleaned_data['attribute_name']
            value = self.cleaned_data['new_value']
            i[key] = value
            i.save()
    def clean(self):
        #self.cleaned_data = {}
        for k,v in self.data.items():
            print "datum", k, v
            if k.startswith('hidden_'):
                self.cleaned_data[k] = v
                obj = Model.ObjectDefinition.objects.get_by_id(v)
                if obj not in self.all_objects:
                    self.all_objects.append( obj )
            if k.startswith('change_'):
                self.cleaned_data[k] = v
                object_id = k[ len("change_"): ]
                obj = Model.ObjectDefinition.objects.get_by_id(object_id)
                if obj not in self.changed_objects:
                    self.changed_objects.append( obj )
        return self.cleaned_data
