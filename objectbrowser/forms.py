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

class UseField(forms.ChoiceField):
    def __init__(self, *args,**kwargs):
        if not kwargs.has_key('choices'):
            pass
        forms.ChoiceField.__init__(self, *args, **kwargs)

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


class PynagForm(forms.Form):
    test = forms.CharField()
    def __init__(self, *args, **kwargs):
        extra = kwargs.pop('extra')
        initial = {}
        if kwargs.has_key("initial"):
            for k,v in kwargs['initial'].items():
                if k == 'check_command':
                    initial[k] = v.split('!',1)[0]
                elif attribute_types.has_key(k) and attribute_types[k][1] == forms.MultipleChoiceField:
                    initial[k] = v.split(',')
                else:
                    initial[k] = v
            kwargs.pop('initial')
            kwargs['initial'] = initial
        super(forms.Form,self).__init__(*args, **kwargs)
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
                    templates.append( (obj['name'], obj['name'])  )
                extra_arguments['choices'] = ( templates )
            if k == 'timeperiod_name':
                # TODO: Make sure already initial values are selected
                templates = []
                for obj in Model.Timeperiod.objects.all:
                    if not obj['timeperiod_name']: continue
                    templates.append( (obj['timeperiod_name'], obj['timeperiod_name'])  )
                extra_arguments['choices'] = ( templates )
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