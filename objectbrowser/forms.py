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
    def clean(self):
        cleaned = self.cleaned_data
        if cleaned == True:
            return "1"
        else:
            return "0"

        
class PynagForm(forms.Form):
    def create_fields(self):
        "Populate form with all fields that are normally seen in this type of an object"
        object_type = self.extra['object_type']
        inherited = self.extra._inherited_attributes.keys()
        defined = self.extra._defined_attributes.keys()
        if object_definitions.has_key(object_type):
            for name,hash in object_definitions[object_type].items():
                fieldClass = forms.CharField
                if hash['value'] == '[0/1]':
                    fieldClass = ZeroOneField
                elif hash['value'] == '#':
                    fieldClass = forms.IntegerField
                # Create a radiobutton go with it
                if name in self.extra._defined_attributes.keys():
                    initial="defined"
                elif name in self.extra._inherited_attributes.keys():
                    initial='inherited'
                else:
                    initial='undefined'
                self.fields['defined_%s' % name] = DefinitionStatusField(initial=initial)
                self.fields['defined_%s' % name].widget.attrs['class'] = "definiton_choices"
                
                # Here the field is created
                self.fields['%s' % name] = fieldClass()
                self.fields[name].widget.attrs['class'] = "definition_field is_%s" % initial
    def clean(self):
        for k,v in self.cleaned_data.items():
            if k in self.undefined_attributes and v == '': self.cleaned_data.pop(k)
            elif v == self.pynag_object[k]: self.cleaned_data.pop(k)
            elif v == '' and self.pynag_object[k] is None: self.cleaned_data.pop(k)
            else: pass
        return self.cleaned_data
    def save(self):
        for k,v in self.cleaned_data.items():
            print "saving, %s=%s" % (k,v)
            self.pynag_object[k] = v
            #self.pynag_object.save()
                #for k,v in request.POST.items():
            #    if k == "csrfmiddlewaretoken": continue
            #    if o[k] != v:
            #        o[k] = v
            #o.save()
    def __init__(self, pynag_object, show_defined_attributes=True,show_inherited_attributes=True,show_undefined_attributes=True, show_radiobuttons=True,*args, **kwargs):
        self.pynag_object = pynag_object
        super(forms.Form,self).__init__(*args, **kwargs)
        # Lets find out what attributes to create
        object_type = pynag_object['object_type']
        defined_attributes = sorted( self.pynag_object._defined_attributes.keys() )
        inherited_attributes = sorted( self.pynag_object._inherited_attributes.keys() )
        all_attributes = sorted( object_definitions.get(object_type).keys() )
        undefined_attributes = []
        for i in all_attributes:
            if i in defined_attributes: continue
            if i in inherited_attributes: continue
            undefined_attributes.append( i )
        if show_defined_attributes:
            for field_name in defined_attributes:
                self.fields[field_name] = self.get_pynagField(field_name, css_tag="defined_attribute")
        if show_inherited_attributes:
            for field_name in inherited_attributes:
                if field_name in defined_attributes: continue
                self.fields[field_name] = self.get_pynagField(field_name, css_tag="inherited_attribute")
        if show_undefined_attributes:
            for field_name in undefined_attributes:
                self.fields[field_name] = self.get_pynagField(field_name, css_tag="undefined_attribute")
        self.undefined_attributes = undefined_attributes
        return
    def get_pynagField(self, field_name, css_tag=""):
        """ Takes a given field_name and returns a forms.Field that is appropriate for this field """
        field = forms.CharField()
        
        if css_tag == 'inherited_attribute':
            field.help_text = "Inherited from template"
        elif css_tag == 'undefined_attribute':
            field.help_text = 'Undefined'
        try:
            options = object_definitions[ self.pynag_object['object_type'] ][field_name]
        except: options = {}
        if options.has_key('required'):
            css_tag = css_tag + " " + options['required']
            field.required = options['required'] == 'required'
        else:
            field.required = False
        # At the moment, our required database is incorrect
        field.required = False
        
        if css_tag:
            field.widget.attrs['class'] = css_tag
            field.css_tag = css_tag
        return field
        
    def __old_init__(self):
        'Just a placeholder for deprecated __init__'
        # TODO: Remove this function
        for k,v  in extra._original_attributes.items():
            if k == 'meta': continue
            extra_arguments = {}
            if attribute_types.has_key(k):
                friendly_name,fieldClass = attribute_types[k]
            else:
                friendly_name,fieldClass = k, forms.CharField
                print "not recognized:", k
            if k == 'check_command':
                commands = Model.Command.objects.all
                commands = map(lambda x: (x.command_name, x.command_name), commands)
                extra_arguments['choices'] = commands
                extra_arguments['initial'] = 'check-host-alive'
            if k == 'contact_groups':
                # TODO: Make sure already initial values are selected
                contact_groups = []
                for cg in Model.Contactgroup.objects.all:
                    if not cg['contactgroup_name']: continue
                    contact_groups.append( (cg.get_shortname(), cg.get_shortname() )  )
                extra_arguments['choices'] = ( contact_groups )
            if k == 'servicegroups':
                # TODO: Make sure already initial values are selected
                groups = []
                for i in Model.Servicegroup.objects.all:
                    if not i['servicegroup_name']: continue
                    groups.append( (i.get_shortname(), i.get_shortname() )  )
                extra_arguments['choices'] = ( groups )
            if k == 'use':
                # TODO: Make sure already initial values are selected
                templates = []
                for obj in extra.objects.all:
                    if not obj['name']: continue
                    #templates.append( (obj['name'], obj['name'])  )
                extra_arguments['choices'] = ( templates )
            if k == 'timeperiod_name':
                # TODO: Make sure already initial values are selected
                templates = []
                for obj in Model.Timeperiod.objects.all:
                    if not obj['timeperiod_name']: continue
                    templates.append( (obj['timeperiod_name'], obj['timeperiod_name'])  )
                extra_arguments['choices'] = ( templates )
            
            # 
            if fieldClass is UseField:
                extra_arguments['object'] = extra 
                extra_arguments['initial'] = ['windows-server']
            self.fields['%s' % k] = fieldClass(label=friendly_name, **extra_arguments)
                
                
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
        print "cleaning definition %s" % self.cleaned_data['definition']
        definition = self.cleaned_data['definition']
        definition = definition.replace('\r\n', '\n')
        definition = definition.replace('\r', '\n')
        return definition
    def save(self):
        definition = self.cleaned_data['definition']
        print [definition]
        self.pynag_object.rewrite( str_new_definition=definition )
