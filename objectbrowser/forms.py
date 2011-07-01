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
from adagios.objectbrowser.all_attributes import object_definitions

class UseField(forms.CharField):
    def __init__(self, object, *args,**kwargs):
        kwargs.pop('choices')
        forms.CharField.__init__(self, *args, **kwargs)
    def clean(self, **kwargs):
        print "CLEAN"
        if self.cleaned_data.has_key('use'):
            print self.cleaned_data.get('use')



attribute_types = {
                    'host_name':('Host Name',forms.CharField),
                    'active_checks_enabled':('Enable Active Checks', forms.BooleanField),
                    "obsess_over_service":("Obsess Over Service", forms.BooleanField),
                    "action_url":("Action URL", forms.CharField),
                    "is_volatile":("Is Volatile", forms.BooleanField),
                    "process_perf_data":("Process Perf Data", forms.BooleanField),
                    "check_period":("Check Period", forms.CharField),
                    "notification_interval":("Notification Interval", forms.IntegerField),
                    "notification_period":("Notification Period", forms.CharField),
                    "failure_prediction_enabled":("Enable Failure Prediction", forms.BooleanField),
                    "retain_status_information":("Retain Status Information", forms.BooleanField),
                    "event_handler_enabled":("Enable Event Handler", forms.BooleanField),
                    "flap_detection_enabled":("Enable Flap Detection", forms.BooleanField),
                    "notification_options":("Notification Options", forms.CharField),
                    "retry_check_interval":("Retry Check Interval", forms.IntegerField),
                    "retain_nonstatus_information":("Retain Nonstatus Information", forms.BooleanField),
                    "notifications_enabled":("Enable Notifications", forms.BooleanField),
                    "contact_groups":("Contact Groups", forms.MultipleChoiceField),
                    "name":("Name", forms.CharField),
                    "register":("Register", forms.BooleanField),
                    "parallelize_check":("Parallelize Check", forms.BooleanField),
                    "passive_checks_enabled":("Enable Passive Checks", forms.BooleanField),
                    "normal_check_interval":("Normal Check Interval", forms.IntegerField),
                    "max_check_attempts":("Max Check Attempts", forms.CharField),
                    "check_freshness":("Check Freshness", forms.BooleanField),

                    "use":("Inherit Settings from", UseField),
                    "check_command":("Check Command", forms.ChoiceField),
                    "check_interval":("Check Interval", forms.IntegerField),
                    "retry_interval":("Retry Interval", forms.IntegerField),
                    "alias":("Alias", forms.CharField),
                    "address":("IP Address", forms.IPAddressField),
                    
                    "servicegroup_name": ("Servicegroup Name", forms.CharField),
                    "hostgroup_name": ("Hostgroup Name", forms.CharField),
                    "members": ("Members", forms.CharField),
                    "host_notification_period": ("Host Notification Period", forms.CharField),
                    "service_notification_options": ("Service Notification Options", forms.CharField),
                    "host_notification_commands": ("Host Notification Commands", forms.CharField),
                    "service_notification_period": ("Service Notification Period", forms.CharField),
                    "contact_name": ("Contact Name", forms.CharField),
                    "service_notification_commands": ("Service Notification Commands", forms.CharField),
                    "host_notification_options": ("Host Notification Options", forms.CharField),

                    "freshness_threshold": ("Freshness Threshold", forms.CharField),
                    "service_description": ("Service Description", forms.CharField),
                    "servicegroups": ("Service Groups", forms.MultipleChoiceField),
                    
                    "contactgroup_name": ("Contactgroup Name", forms.CharField),
                    "command_name": ("Command Name", forms.CharField),
                    "command_line": ("Command Line", forms.CharField),
                    "monday" : ("Monday", forms.CharField),
                    "tuesday" : ("Tuesday", forms.CharField),
                    "friday" : ("Friday", forms.CharField),
                    "wednesday" : ("Wednesday", forms.CharField),
                    "thursday" : ("Thursday", forms.CharField),
                    "sunday" : ("Sunday", forms.CharField),
                    "timeperiod_name" : ("Timeperiod Name", forms.ChoiceField),
                    "saturday" : ("Saturday", forms.CharField),
                    "pager" : ("Pager", forms.CharField),
                    "email" : ("E-mail", forms.EmailField),
                    
                    "hostgroups" : ("Host Groups", forms.CharField)
                    }
class ZeroOneField(forms.BooleanField):
    def clean(self, value):
        cleaned = value
        if cleaned == True:
            return "1"
        else:
            return "0"

# These fields are special, they are a comma seperated list, and may or may not have +/- in front of them.
MULTICHOICE_FIELDS = ('servicegroups','hostgroups','contacts','contact_groups', 'contactgroups', 'use')

class PynagChoiceField(forms.MultipleChoiceField):
    ''' multichoicefields that accepts comma seperated input as values '''
    def __init__(self, *args, **kwargs):
        self.__prefix = ''
        self.data = kwargs.get('data')
        super(PynagChoiceField, self).__init__(*args, **kwargs)
    def clean(self,value):
        print "test: '%s' '%s' '%s' 's' "% ( self.__prefix, self.initial, self.data)
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
            if k in MULTICHOICE_FIELDS:
                if self.pynag_object.get(k,'').startswith('+'):
                    v = self.cleaned_data[k] = "+%s"%(v)
            if k not in self.data.keys(): self.cleaned_data.pop(k)
            elif k in self.undefined_attributes and v == '': self.cleaned_data.pop(k)
            elif v == self.pynag_object[k]: self.cleaned_data.pop(k)
            elif v == '' and self.pynag_object[k] is None: self.cleaned_data.pop(k)
            else: pass
        return self.cleaned_data
    def save(self):
        for k,v in self.cleaned_data.items():
            k,v = str(k), str(v)
            if self.pynag_object[k] != v:
                self.pynag_object[k] = v
                self.fields[k] = self.get_pynagField(k, css_tag="defined_attribute")
                self.fields[k].value = v
        self.pynag_object.save()
    def __init__(self, pynag_object, show_defined_attributes=True,show_inherited_attributes=True,show_undefined_attributes=True, show_radiobuttons=True,*args, **kwargs):
        self.pynag_object = pynag_object
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
        if show_defined_attributes:
            for field_name in defined_attributes:
                self.fields[field_name] = self.get_pynagField(field_name,css_tag="defined_attribute")
        if show_inherited_attributes:
            for field_name in inherited_attributes:
                if field_name in defined_attributes: continue
                self.fields[field_name] = self.get_pynagField(field_name, css_tag="inherited_attribute")
        if show_undefined_attributes:
            for field_name in self.undefined_attributes:
                self.fields[field_name] = self.get_pynagField(field_name, css_tag="undefined_attribute")
        return
    def get_pynagField(self, field_name, css_tag=""):
        """ Takes a given field_name and returns a forms.Field that is appropriate for this field """
        # Lets figure out what type of field this is, default to charfield
        object_type = self.pynag_object['object_type']
        definitions = object_definitions.get( object_type ) or {}
        options = definitions.get(field_name) or {}
        # Some fields get special treatment
        if field_name == 'contact_groups' or field_name == 'contactgroups':
                all_groups = Model.Contactgroup.objects.filter(contactgroup_name__contains="")
                choices = map(lambda x: (x.contactgroup_name, x.contactgroup_name), all_groups)
                field = PynagChoiceField(choices=choices)
        elif field_name == 'use':
            all_objects = self.pynag_object.objects.filter(name__contains='')
            choices = map(lambda x: (x.name, x.name), all_objects)
            field = PynagChoiceField(choices=choices)
        elif field_name == 'servicegroups':
            all_groups = Model.Servicegroup.objects.filter(servicegroup_name__contains='')
            choices = map(lambda x: (x.servicegroup_name, x.servicegroup_name), all_groups)
            field = PynagChoiceField(choices=choices)
        elif field_name == 'hostgroups':
            all_groups = Model.Hostgroup.objects.filter(hostgroup_name__contains='')
            choices = map(lambda x: (x.hostgroup_name, x.hostgroup_name), all_groups)
            field = PynagChoiceField(choices=choices)
        elif field_name == 'contacts':
            all = Model.Contact.objects.filter(contact_name__contains='')
            choices = map(lambda x: (x.contact_name, x.contact_name), all)
            field = PynagChoiceField(choices=choices)
        elif field_name == 'check_period' or field_name == 'notification_period':
            all = Model.Timeperiod.objects.filter(timeperiod_name__contains='')
            choices = map(lambda x: (x.timeperiod_name, x.timeperiod_name), all)
            field = forms.ChoiceField(choices=choices)
        elif options.get('value') == '[0/1]':
            choices = ( ('', 'not set'),('1','1'),('0','0'))
            field = forms.ChoiceField(choices=choices)
        else:
            ''' Fallback to a default charfield '''
                field = forms.CharField()
        if field_name.startswith('_'):
            field.label = field_name
        if options.has_key('required'):
            css_tag = css_tag + " " + options['required']
            field.required = options['required'] == 'required'
        else:
            field.required = False
        # At the moment, our database of required objects is incorrect
        field.required = False
        if css_tag:
            field.widget.attrs['class'] = css_tag
            field.css_tag = css_tag
        return field
                
                
class DynamicForm(forms.Form):
    def __init__(self, *args, **kwargs):
        extra_fields = kwargs.pop('extra')
        super(forms.Form, self).__init__(*args, **kwargs)
        choices = ( ('value1','value1'), ('value2','value2')   ) 
        for k,v in extra_fields.items():
            self.fields[k] = forms.MultipleChoiceField(choices=choices )
        
class ManualEditObjectForm(forms.Form):
    definition= forms.CharField( widget=forms.Textarea(attrs={ 'wrap':'off', 'cols':'80'}) )
    def __init__(self,pynag_object=None, *args,**kwargs):
        self.pynag_object = pynag_object
        super(ManualEditObjectForm, self).__init__(*args,**kwargs)
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
