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
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _

from pynag import Model
from pynag.Utils import AttributeList
from adagios.objectbrowser.help_text import object_definitions
from pynag.Model import ObjectDefinition
from adagios.forms import AdagiosForm
import adagios.misc.rest


# These fields are special, they are a comma seperated list, and may or
# may not have +/- in front of them.
MULTICHOICE_FIELDS = ('servicegroups', 'hostgroups', 'contacts',
                      'contact_groups', 'contactgroups', 'use', 'notification_options')

SERVICE_NOTIFICATION_OPTIONS = (
    ('w', 'warning'),
    ('c', 'critical'),
    ('r', 'recovery'),
    ('u', 'unreachable'),
    ('d', 'downtime'),
    ('f', 'flapping'),
)

HOST_NOTIFICATION_OPTIONS = (
    ('d', 'down'),
    ('u', 'unreachable'),
    ('r', 'recovery'),
    ('f', 'flapping'),
    ('s', 'scheduled_downtime')
)


BOOLEAN_CHOICES = (('', 'not set'), ('1', '1'), ('0', '0'))


class PynagChoiceField(forms.MultipleChoiceField):

    """ multichoicefields that accepts comma seperated input as values """

    def __init__(self, inline_help_text="Select some options", *args, **kwargs):
        self.__prefix = ''
        self.data = kwargs.get('data')
        super(PynagChoiceField, self).__init__(*args, **kwargs)
        self.widget.attrs['data-placeholder'] = inline_help_text

    def clean(self, value):
        """
        Changes list into a comma separated string. Removes duplicates.
        """
        if not value:
            return "null"
        tmp = []
        for i in value:
            if i not in tmp:
                tmp.append(i)
        value = self.__prefix + ','.join(tmp)
        return value

    def prepare_value(self, value):
        """
        Takes a comma separated string, removes + if it is prefixed so. Returns a list
        """
        if isinstance(value, str):
            self.attributelist = AttributeList(value)
            self.__prefix = self.attributelist.operator
            return self.attributelist.fields
        return value


class PynagRadioWidget(forms.widgets.HiddenInput):

    """ Special Widget designed to make Nagios attributes with 0/1 values look like on/off buttons """

    def render(self, name, value, attrs=None):
        output = super(PynagRadioWidget, self).render(name, value, attrs)
        one, zero, unset = "", "", ""
        if value == "1":
            one = "active"
        elif value == "0":
            zero = "active"
        else:
            unset = "active"
        prefix = """
        <div class="btn-group" data-toggle-name="%s" data-toggle="buttons-radio">
          <button type="button" value="1" class="btn btn %s">On</button>
          <button type="button" value="0" class="btn btn %s">Off</button>
          <button type="button" value="" class="btn %s">Not set</button>
        </div>
        """ % (name, one, zero, unset)
        output += prefix
        return mark_safe(output)


class PynagForm(AdagiosForm):

    def clean(self):
        cleaned_data = super(PynagForm, self).clean()
        for k, v in cleaned_data.items():
            # change from unicode to str
            v = cleaned_data[k] = smart_str(v)

            # Empty string, or the string None, means remove the field
            if v in ('', 'None'):
                cleaned_data[k] = v = None

            # Maintain operator (+,-, !) for multichoice fields
            if k in MULTICHOICE_FIELDS and v and v != "null":
                operator = AttributeList(self.pynag_object.get(k, '')).operator or ''
                cleaned_data[k] = "%s%s" % (operator, v)
        return cleaned_data

    def save(self):
        changed_keys = map(lambda x: smart_str(x), self.changed_data)
        for k in changed_keys:

            # Ignore fields that did not appear in the POST at all EXCEPT
            # If it it a pynagchoicefield. That is because multichoicefield that
            # does not appear in the post, means that the user removed every attribute
            # in the multichoice field
            if k not in self.data and not isinstance(self.fields.get(k, None), PynagChoiceField):
                continue

            value = self.cleaned_data[k]

            # Sometimes attributes slide in changed_data without having
            # been modified, lets ignore those
            if self.pynag_object[k] == value:
                continue

            # Multichoice fields have a special restriction, sometimes they contain
            # the same values as before but in a different order.
            if k in MULTICHOICE_FIELDS:
                original = AttributeList(self.pynag_object[k])
                new = AttributeList(value)
                if sorted(original.fields) == sorted(new.fields):
                    continue            # If we reach here, it is save to modify our pynag object.

            # Here we actually make a change to our pynag object
            self.pynag_object[k] = value

            # Additionally, update the field for the return form
            self.fields[k] = self.get_pynagField(k, css_tag="defined")
            self.fields[k].value = value
        self.pynag_object.save()
        adagios.misc.rest.add_notification(message="Object successfully saved", level="success", notification_type="show_once")

    def __init__(self, pynag_object, *args, **kwargs):
        self.pynag_object = pynag_object
        super(PynagForm, self).__init__(*args, **kwargs)
        # Lets find out what attributes to create
        object_type = pynag_object['object_type']
        defined_attributes = sorted(
            self.pynag_object._defined_attributes.keys())
        inherited_attributes = sorted(
            self.pynag_object._inherited_attributes.keys())
        all_attributes = sorted(object_definitions.get(object_type).keys())
        all_attributes += ['name', 'use', 'register']

        # Special hack for macros
        # If this is a post and any post data looks like a nagios macro
        # We will generate a field for it on the fly
        macros = filter(lambda x: x.startswith('$') and x.endswith('$'), self.data.keys())
        for field_name in macros:
            # if field_name.startswith('$ARG'):
            #    self.fields[field_name] = self.get_pynagField(field_name, css_tag='defined')
            if object_type == 'service' and field_name.startswith('$_SERVICE'):
                self.fields[field_name] = self.get_pynagField(
                    field_name, css_tag='defined')
            elif object_type == 'host' and field_name.startswith('$_HOST'):
                self.fields[field_name] = self.get_pynagField(
                    field_name, css_tag='defined')

        # Calculate what attributes are "undefined"
        self.undefined_attributes = []
        for i in all_attributes:
            if i in defined_attributes:
                continue
            if i in inherited_attributes:
                continue
            self.undefined_attributes.append(i)
        # Find out which attributes to show
        for field_name in defined_attributes:
            self.fields[field_name] = self.get_pynagField(
                field_name, css_tag='defined')
        for field_name in inherited_attributes:
            self.fields[field_name] = self.get_pynagField(
                field_name, css_tag="inherited")
        for field_name in self.undefined_attributes:
            self.fields[field_name] = self.get_pynagField(
                field_name, css_tag='undefined')
        return

    def get_pynagField(self, field_name, css_tag="", required=None):
        """ Takes a given field_name and returns a forms.Field that is appropriate for this field

          Arguments:
            field_name  --  Name of the field to add, example "host_name"
            css_tag     --  String will make its way as a css attribute in the resulting html
            required    --  If True, make field required. If None, let pynag decide
        """
        # Lets figure out what type of field this is, default to charfield
        object_type = self.pynag_object['object_type']
        definitions = object_definitions.get(object_type) or {}
        options = definitions.get(field_name) or {}

        # Find out what type of field to create from the field_name.
        # Lets assume charfield in the beginning
        field = forms.CharField()

        if False is True:
            pass
        elif field_name in ('contact_groups', 'contactgroups', 'contactgroup_members'):
                all_groups = Model.Contactgroup.objects.filter(
                    contactgroup_name__contains="")
                choices = sorted(
                    map(lambda x: (x.contactgroup_name, x.contactgroup_name), all_groups))
                field = PynagChoiceField(
                    choices=choices, inline_help_text="No %s selected" % (field_name))
        elif field_name == 'use':
            all_objects = self.pynag_object.objects.filter(name__contains='')
            choices = map(lambda x: (x.name, x.name), all_objects)
            field = PynagChoiceField(
                choices=sorted(choices), inline_help_text="No %s selected" % (field_name))
        elif field_name in ('servicegroups', 'servicegroup_members'):
            all_groups = Model.Servicegroup.objects.filter(
                servicegroup_name__contains='')
            choices = map(
                lambda x: (x.servicegroup_name, x.servicegroup_name), all_groups)
            field = PynagChoiceField(
                choices=sorted(choices), inline_help_text="No %s selected" % (field_name))
        elif field_name in ('hostgroups', 'hostgroup_members', 'hostgroup_name') and object_type != 'hostgroup':
            all_groups = Model.Hostgroup.objects.filter(
                hostgroup_name__contains='')
            choices = map(
                lambda x: (x.hostgroup_name, x.hostgroup_name), all_groups)
            field = PynagChoiceField(
                choices=sorted(choices), inline_help_text="No %s selected" % (field_name))
        elif field_name == 'members' and object_type == 'hostgroup':
            all_groups = Model.Host.objects.filter(host_name__contains='')
            choices = map(lambda x: (x.host_name, x.host_name), all_groups)
            field = PynagChoiceField(
                choices=sorted(choices), inline_help_text="No %s selected" % (field_name))
        elif field_name == 'host_name' and object_type == 'service':
            all_groups = Model.Host.objects.filter(host_name__contains='')
            choices = map(lambda x: (x.host_name, x.host_name), all_groups)
            field = PynagChoiceField(
                choices=sorted(choices), inline_help_text="No %s selected" % (field_name))
        elif field_name in ('contacts', 'members'):
            all_objects = Model.Contact.objects.filter(
                contact_name__contains='')
            choices = map(
                lambda x: (x.contact_name, x.contact_name), all_objects)
            field = PynagChoiceField(
                choices=sorted(choices), inline_help_text="No %s selected" % (field_name))
        elif field_name.endswith('_period'):
            all_objects = Model.Timeperiod.objects.filter(
                timeperiod_name__contains='')
            choices = [('', '')] + map(
                lambda x: (x.timeperiod_name, x.timeperiod_name), all_objects)
            field = forms.ChoiceField(choices=sorted(choices))
        elif field_name.endswith('notification_commands'):
            all_objects = Model.Command.objects.filter(
                command_name__contains='')
            choices = [('', '')] + map(
                lambda x: (x.command_name, x.command_name), all_objects)
            field = PynagChoiceField(choices=sorted(choices))
        # elif field_name == 'check_command':
        #    all_objects = Model.Command.objects.all
        #    choices = [('','')] + map(lambda x: (x.command_name, x.command_name), all_objects)
        #    field = forms.ChoiceField(choices=sorted(choices))
        elif field_name.endswith('notification_options') and self.pynag_object.object_type == 'host':
            field = PynagChoiceField(
                choices=HOST_NOTIFICATION_OPTIONS, inline_help_text="No %s selected" % (field_name))
        elif field_name.endswith('notification_options') and self.pynag_object.object_type == 'service':
            field = PynagChoiceField(
                choices=SERVICE_NOTIFICATION_OPTIONS, inline_help_text="No %s selected" % (field_name))
        elif options.get('value') == '[0/1]':
            field = forms.CharField(widget=PynagRadioWidget)

        # Lets see if there is any help text available for our field
        if field_name in object_definitions[object_type]:
            help_text = object_definitions[object_type][field_name].get(
                'help_text', "No help available for this item")
            field.help_text = help_text

        # No prettyprint for macros
        if field_name.startswith('_'):
            field.label = field_name

        # If any CSS tag was given, add it to the widget
        self.add_css_tag(field=field, css_tag=css_tag)

        if 'required' in options:
            self.add_css_tag(field=field, css_tag=options['required'])
            field.required = options['required'] == 'required'
        else:
            field.required = False

        # At the moment, our database of required objects is incorrect
        # So if caller did not specify if field is required, we will not
        # make it required
        if required is None:
            field.required = False
        else:
            field.required = required

        # Put inherited value in the placeholder
        inherited_value = self.pynag_object._inherited_attributes.get(
            field_name)
        if inherited_value is not None:
            self.add_placeholder(
                field, '%s (inherited from template)' % (inherited_value))

        if field_name in MULTICHOICE_FIELDS:
            self.add_css_tag(field=field, css_tag="multichoice")

        return field

    def add_css_tag(self, field, css_tag):
        """ Add a CSS tag to the widget of a specific field """
        if not 'class' in field.widget.attrs:
            field.widget.attrs['class'] = ''
            field.css_tag = ''
        field.widget.attrs['class'] += " " + css_tag
        field.css_tag += " " + css_tag

    def add_placeholder(self, field, placeholder="Insert some value here"):
        field.widget.attrs['placeholder'] = placeholder
        field.placeholder = placeholder


class AdvancedEditForm(AdagiosForm):

    """ A form for pynag.Model.Objectdefinition

    This form will display a charfield for every attribute of the objectdefinition

    "Every" attribute means:
    * Every defined attribute
    * Every inherited attribute
    * Every attribute that is defined in nagios object definition html

    """
    register = forms.CharField(
        required=False, help_text="Set to 1 if you want this object enabled.")
    name = forms.CharField(required=False, label="Generic Name",
                           help_text="This name is used if you want other objects to inherit (with the use attribute) what you have defined here.")
    use = forms.CharField(required=False, label="Use",
                          help_text="Inherit all settings from another object")
    __prefix = "advanced"  # This prefix will go on every field

    def save(self):
        for k in self.changed_data:
            # change from unicode to str
            value = smart_str(self.cleaned_data[k])
            # same as original, lets ignore that
            if self.pynag_object[k] == value:
                continue
            if value == '':
                value = None

            # If we reach here, it is save to modify our pynag object.
            self.pynag_object[k] = value
        self.pynag_object.save()

    def clean(self):
        cleaned_data = super(AdvancedEditForm, self).clean()
        for k, v in cleaned_data.items():
            # change from unicode to str
            cleaned_data[k] = smart_str(v)
        return cleaned_data

    def __init__(self, pynag_object, *args, **kwargs):
        self.pynag_object = pynag_object
        super(AdvancedEditForm, self).__init__(
            *args, prefix=self.__prefix, **kwargs)

        # Lets find out what attributes to create
        object_type = pynag_object['object_type']
        all_attributes = sorted(object_definitions.get(object_type).keys())
        for field_name in self.pynag_object.keys() + all_attributes:
            if field_name == 'meta':
                continue
            help_text = ""
            if field_name in object_definitions[object_type]:
                help_text = object_definitions[object_type][field_name].get(
                    'help_text', "No help available for this item")
            self.fields[field_name] = forms.CharField(
                required=False, label=field_name, help_text=help_text)
        self.fields.keyOrder = sorted(self.fields.keys())


class GeekEditObjectForm(AdagiosForm):
    definition = forms.CharField(
        widget=forms.Textarea(attrs={'wrap': 'off', 'cols': '80'}))

    def __init__(self, pynag_object=None, *args, **kwargs):
        self.pynag_object = pynag_object
        super(GeekEditObjectForm, self).__init__(*args, **kwargs)

    def clean_definition(self, value=None):
        definition = smart_str(self.cleaned_data['definition'])
        definition = definition.replace('\r\n', '\n')
        definition = definition.replace('\r', '\n')
        if not definition.endswith('\n'):
            definition += '\n'
        return definition

    def save(self):
        definition = self.cleaned_data['definition']
        self.pynag_object.rewrite(str_new_definition=definition)


class DeleteObjectForm(AdagiosForm):

    """ Form used to handle deletion of one single object """

    def __init__(self, pynag_object, *args, **kwargs):
        self.pynag_object = pynag_object
        super(DeleteObjectForm, self).__init__(*args, **kwargs)
        if self.pynag_object.object_type == 'host':
            recursive = forms.BooleanField(
                required=False, initial=True, label="Delete Services",
                help_text="Check this box if you also want to delete all services of this host")
            self.fields['recursive'] = recursive

    def delete(self):
        """ Deletes self.pynag_object. """
        recursive = False
        if 'recursive' in self.cleaned_data and self.cleaned_data['recursive'] is True:
            recursive = True
        self.pynag_object.delete(recursive)


class CopyObjectForm(AdagiosForm):

    """ Form to assist a user to copy a single object definition
    """

    def __init__(self, pynag_object, *args, **kwargs):
        self.pynag_object = pynag_object
        super(CopyObjectForm, self).__init__(*args, **kwargs)
        object_type = pynag_object['object_type']

        # For templates we assume the new copy will have its generic name changed
        # otherwise we display different field depending on what type of an
        # object it is
        if pynag_object['register'] == '0':
            if pynag_object.name is None:
                new_generic_name = "%s-copy" % pynag_object.get_description()
            else:
                new_generic_name = '%s-copy' % pynag_object.name
            self.fields['name'] = forms.CharField(
                initial=new_generic_name, help_text="Select a new generic name for this %s" % object_type)
        elif object_type == 'host':
            new_host_name = "%s-copy" % pynag_object.get_description()
            self.fields['host_name'] = forms.CharField(
                help_text="Select a new host name for this host", initial=new_host_name)
            self.fields['address'] = forms.CharField(
                help_text="Select a new ip address for this host")
            self.fields['recursive'] = forms.BooleanField(
                required=False, label="Copy Services", help_text="Check this box if you also want to copy all services of this host.")
        elif object_type == 'service':
            service_description = "%s-copy" % pynag_object.service_description
            self.fields['host_name'] = forms.CharField(
                help_text="Select a new host name for this service", initial=pynag_object.host_name)
            self.fields['service_description'] = forms.CharField(
                help_text="Select new service description for this service", initial=service_description)
        else:
            field_name = "%s_name" % object_type
            initial = "%s-copy" % pynag_object[field_name]
            help_text = object_definitions[
                object_type][field_name].get('help_text')
            if help_text == '':
                help_text = "Please specify a new %s" % field_name
            self.fields[field_name] = forms.CharField(
                initial=initial, help_text=help_text)

    def save(self):
        # If copy() returns a single object, lets transform it into a list
        tmp = self.pynag_object.copy(**self.cleaned_data)
        if not type(tmp) == type([]):
            tmp = [tmp]
        self.copied_objects = tmp

    def _clean_shortname(self):
        """ Make sure shortname of a particular object does not exist.

        Raise validation error if shortname is found
        """
        object_type = self.pynag_object.object_type
        field_name = "%s_name" % object_type
        value = smart_str(self.cleaned_data[field_name])
        try:
            self.pynag_object.objects.get_by_shortname(value)
            raise forms.ValidationError(
                "A %s with %s='%s' already exists." % (object_type, field_name, value))
        except KeyError:
            return value

    def clean_host_name(self):
        if self.pynag_object.object_type == 'service':
            return smart_str(self.cleaned_data['host_name'])
        return self._clean_shortname()

    def clean_timeperiod_name(self):
        return self._clean_shortname()

    def clean_command_name(self):
        return self._clean_shortname()

    def clean_contactgroup_name(self):
        return self._clean_shortname()

    def clean_hostgroup_name(self):
        return self._clean_shortname()

    def clean_servicegroup_name(self):
        return self._clean_shortname()

    def clean_contact_name(self):
        return self._clean_shortname()


class BaseBulkForm(AdagiosForm):

    """ To make changes to multiple objects at once

    * any POST data that has the name change_<OBJECTID> will be fetched
    and the ObjectDefinition saved in self.changed_objects
    * any POST data that has the name hidden_<OBJECTID> will be fetched
    and the ObjectDefinition saved in self.all_objects
    """

    def __init__(self, objects=None, *args, **kwargs):
        self.objects = []
        self.all_objects = []
        self.changed_objects = []
        if not objects:
            objects = []
        forms.Form.__init__(self, *args, **kwargs)
        for k, v in self.data.items():
            if k.startswith('hidden_'):
                obj = Model.ObjectDefinition.objects.get_by_id(v)
                if obj not in self.all_objects:
                    self.all_objects.append(obj)
            if k.startswith('change_'):
                object_id = k[len("change_"):]
                obj = Model.ObjectDefinition.objects.get_by_id(object_id)
                if obj not in self.changed_objects:
                    self.changed_objects.append(obj)
                if obj not in self.all_objects:
                    self.all_objects.append(obj)

    def clean(self):
        #self.cleaned_data = {}
        for k, v in self.data.items():
            if k.startswith('hidden_'):
                self.cleaned_data[k] = v
                obj = Model.ObjectDefinition.objects.get_by_id(v)
                if obj not in self.all_objects:
                    self.all_objects.append(obj)
            if k.startswith('change_'):
                self.cleaned_data[k] = v
                object_id = k[len("change_"):]
                obj = Model.ObjectDefinition.objects.get_by_id(object_id)
                if obj not in self.changed_objects:
                    self.changed_objects.append(obj)
        for k, v in self.cleaned_data.items():
            self.cleaned_data[k] = smart_str(self.cleaned_data[k])
        return self.cleaned_data


class BulkEditForm(BaseBulkForm):
    attribute_name = forms.CharField()
    new_value = forms.CharField()

    def save(self):
        for i in self.changed_objects:
            key = self.cleaned_data['attribute_name']
            value = self.cleaned_data['new_value']
            i[key] = value
            i.save()


class BulkCopyForm(BaseBulkForm):
    attribute_name = forms.CharField()
    new_value = forms.CharField()

    def __init__(self, *args, **kwargs):
        BaseBulkForm.__init__(self, *args, **kwargs)
        self.fields['attribute_name'].value = "test 2"
        # Lets take a look at the first item to be copied and suggest a field
        # name to change

    def save(self):
        for i in self.changed_objects:
            key = self.cleaned_data['attribute_name']
            value = self.cleaned_data['new_value']
            kwargs = {key: value}
            i.copy(**kwargs)


class BulkDeleteForm(BaseBulkForm):

    """ Form used to delete multiple objects at once """
    yes_i_am_sure = forms.BooleanField(label="Yes, I am sure")

    def delete(self):
        """ Deletes every object in the form """
        for i in self.changed_objects:
            if i.object_type == 'host':
                recursive = True
            else:
                recursive = False
            i.delete(recursive=recursive)


class CheckCommandForm(PynagForm):

    def __init__(self, *args, **kwargs):
        super(AdagiosForm, self).__init__(*args, **kwargs)
        self.pynag_object = Model.Service()
        self.fields['host_name'] = self.get_pynagField('host_name')
        self.fields['service_description'] = self.get_pynagField(
            'service_description')
        self.fields['check_command'] = self.get_pynagField('check_command')


choices_for_all_types = sorted(
    map(lambda x: (x, x), Model.string_to_class.keys()))


class AddTemplateForm(PynagForm):

    """ Use this form to add one template """
    object_type = forms.ChoiceField(choices=choices_for_all_types)
    name = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super(PynagForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddTemplateForm, self).clean()
        if "object_type" not in cleaned_data:
            raise forms.ValidationError('Object type is required')
        object_type = cleaned_data['object_type']
        name = cleaned_data['name']
        if object_type not in Model.string_to_class:
            raise forms.ValidationError(
                "We dont know nothing about how to add a '%s'" % object_type)
        objectdefinition = Model.string_to_class.get(object_type)
        # Check if name already exists
        try:
            objectdefinition.objects.get_by_name(name)
            raise forms.ValidationError(
                "A %s with name='%s' already exists." % (object_type, name))
        except KeyError:
            pass
        self.pynag_object = objectdefinition()
        self.pynag_object['register'] = "0"

        return cleaned_data


class AddObjectForm(PynagForm):

    def __init__(self, object_type, initial=None, *args, **kwargs):
        self.pynag_object = Model.string_to_class.get(object_type)()
        super(AdagiosForm, self).__init__(*args, **kwargs)
        # Some object types we will suggest a template:
        if object_type in ('host', 'contact', 'service'):
            self.fields['use'] = self.get_pynagField('use')
            self.fields['use'].initial = str('generic-%s' % object_type)
            self.fields['use'].help_text = "Inherit attributes from this template"
        if object_type == 'host':
            self.fields['host_name'] = self.get_pynagField('host_name', required=True)
            self.fields['address'] = self.get_pynagField('address', required=True)
            self.fields['alias'] = self.get_pynagField('alias', required=False)
        elif object_type == 'service':
            self.fields['service_description'] = self.get_pynagField('service_description', required=True)
            self.fields['host_name'] = self.get_pynagField('host_name', required=False)
            self.fields['host_name'].help_text = 'Tell us which host this service check will be applied to'
            self.fields['hostgroup_name'] = self.get_pynagField('hostgroup_name', required=False)
            self.fields['hostgroup_name'].help_text = "If you specify any hostgroups, this service will be applied to all hosts in that hostgroup"
        else:
            field_name = "%s_name" % object_type
            self.fields[field_name] = self.get_pynagField(
                field_name, required=True)
        # For some reason calling super()__init__() with initial as a parameter
        # will not work on PynagChoiceFields. This forces initial value to be set:
        initial = initial or {}
        for field_name, field in self.fields.items():
            initial_value = initial.get(field_name, None)
            if initial_value:
                field.initial = str(initial_value)

    def clean(self):
        cleaned_data = super(AddObjectForm, self).clean()
        if self.pynag_object.object_type == 'service':
            host_name = cleaned_data.get('host_name')
            hostgroup_name = cleaned_data.get('hostgroup_name')
            if host_name in (None, 'None', '') and hostgroup_name in (None, 'None', ''):
                raise forms.ValidationError("Please specify either hostgroup_name or host_name")
        return cleaned_data

    def clean_timeperiod_name(self):
        return self._clean_shortname()

    def clean_command_name(self):
        return self._clean_shortname()

    def clean_contactgroup_name(self):
        return self._clean_shortname()

    def clean_servicegroup_name(self):
        return self._clean_shortname()

    def clean_contact_name(self):
        return self._clean_shortname()

    def clean_host_name(self):
        if self.pynag_object.object_type == 'service':
            value = self.cleaned_data['host_name']
            if not value or value == 'null':
                return None
            hosts = value.split(',')
            for i in hosts:
                existing_hosts = Model.Host.objects.filter(host_name=i)
                if not existing_hosts:
                    raise forms.ValidationError(
                        "Could not find host called '%s'" % (i))
                return smart_str(self.cleaned_data['host_name'])
        return self._clean_shortname()

    def clean_hostgroup_name(self):
        if self.pynag_object.object_type == 'service':
            value = self.cleaned_data['hostgroup_name']
            if value in (None, '', 'null'):
                return None
            groups = value.split(',')
            for i in groups:
                existing_hostgroups = Model.Hostgroup.objects.filter(hostgroup_name=i)
                if not existing_hostgroups:
                    raise forms.ValidationError(
                        "Could not find hostgroup called '%s'" % (i))
                return smart_str(self.cleaned_data['hostgroup_name'])
        return self._clean_shortname()

    def _clean_shortname(self):
        """ Make sure shortname of a particular object does not exist.

        Raise validation error if shortname is found
        """
        object_type = self.pynag_object.object_type
        field_name = "%s_name" % object_type
        value = smart_str(self.cleaned_data[field_name])
        try:
            self.pynag_object.objects.get_by_shortname(value)
            raise forms.ValidationError(
                "A %s with %s='%s' already exists." % (object_type, field_name, value))
        except KeyError:
            return value
