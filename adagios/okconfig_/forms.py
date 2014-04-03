from django import forms
import okconfig
from adagios.misc import helpers
import re
from django.core.exceptions import ValidationError
import socket
from pynag import Model
from adagios.forms import AdagiosForm
from django.utils.translation import ugettext as _


def get_all_hosts():
    return [('', 'Select a host')] + map(lambda x: (x, x), helpers.get_host_names())


def get_all_templates():
    all_templates = okconfig.get_templates()
    service_templates = filter(lambda x: 'host' not in x, all_templates)
    return map(lambda x: (x, "Standard " + x + " checks"), service_templates)


def get_all_groups():
    return map(lambda x: (x, x), okconfig.get_groups())


def get_inactive_services():
    """ List of all unregistered services (templates) """
    inactive_services = [('', 'Select a service')]
    inactive_services += map(lambda x: (x.name, x.name),
                             Model.Service.objects.filter(service_description__contains="", name__contains="", register="0"))
    inactive_services.sort()
    return inactive_services


class ScanNetworkForm(AdagiosForm):
    network_address = forms.CharField()

    def clean_network_address(self):
        addr = self.cleaned_data['network_address']
        if addr.find('/') > -1:
            addr, mask = addr.split('/', 1)
            if not mask.isdigit():
                raise ValidationError("not a valid netmask")
            if not self.isValidIPAddress(addr):
                raise ValidationError("not a valid ip address")
        else:
            if not self.isValidIPAddress(addr):
                raise ValidationError("not a valid ip address")
        return self.cleaned_data['network_address']

    def isValidHostname(self, hostname):
        if len(hostname) > 255:
            return False
        if hostname[-1:] == ".":
            # strip exactly one dot from the right, if present
            hostname = hostname[:-1]
        allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        for x in hostname.split("."):
            if allowed.match(x) is False:
                return False
        return True

    def isValidIPAddress(self, ipaddress):
        try:
            socket.inet_aton(ipaddress)
        except Exception:
            return False
        return True


class AddGroupForm(AdagiosForm):
    group_name = forms.CharField(help_text="Example: databases")
    alias = forms.CharField(help_text="Human friendly name for the group")
    force = forms.BooleanField(
        required=False, help_text="Overwrite group if it already exists.")


class AddHostForm(AdagiosForm):
    host_name = forms.CharField(help_text="Name of the host to add")
    address = forms.CharField(help_text="IP Address of this host")
    group_name = forms.ChoiceField(
        initial="default", help_text="host/contact group to put this host in")
    templates = forms.MultipleChoiceField(
        required=False, help_text="Add standard template of checks to this host")
    force = forms.BooleanField(
        required=False, help_text="Overwrite host if it already exists.")

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.fields['group_name'].choices = choices = get_all_groups()
        self.fields['templates'].choices = get_all_templates()

    def clean(self):
        cleaned_data = super(AddHostForm, self).clean()
        force = self.cleaned_data.get('force')
        host_name = self.cleaned_data.get('host_name')
        templates = self.cleaned_data.get('templates')
        for i in templates:
            if i not in okconfig.get_templates().keys():
                self._errors['templates'] = self.error_class(
                    ['template %s was not found' % i])
        if not force and host_name in okconfig.get_hosts():
            self._errors['host_name'] = self.error_class(
                ['Host name already exists. Use force to overwrite'])
        return cleaned_data


class AddTemplateForm(AdagiosForm):
    # Attributes
    host_name = forms.ChoiceField(help_text="Add templates to this host")
    templates = forms.MultipleChoiceField(
        required=False, help_text="Add standard template of checks to this host")
    force = forms.BooleanField(
        required=False, help_text="Overwrites templates if they already exist")

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.fields['templates'].choices = get_all_templates()
        self.fields['host_name'].choices = get_all_hosts()

    def clean(self):
        cleaned_data = super(AddTemplateForm, self).clean()
        force = self.cleaned_data.get('force')
        host_name = self.cleaned_data.get('host_name')
        templates = self.cleaned_data.get('templates')
        for i in templates:
            if i not in okconfig.get_templates().keys():
                self._errors['templates'] = self.error_class(
                    ['template %s was not found' % i])
        if not force and host_name not in okconfig.get_hosts():
            self._errors['host_name'] = self.error_class(
                ['Host name not found Use force to write template anyway'])
        return cleaned_data

    def save(self):
        host_name = self.cleaned_data['host_name']
        templates = self.cleaned_data['templates']
        force = self.cleaned_data['force']
        self.filelist = []
        for i in templates:
            self.filelist += okconfig.addtemplate(
                host_name=host_name, template_name=i, force=force)


class InstallAgentForm(AdagiosForm):
    remote_host = forms.CharField(help_text="Host or ip address")
    install_method = forms.ChoiceField(
        initial='ssh', help_text="Make sure firewalls are not blocking ports 22(for ssh) or 445(for winexe)",
        choices=[('auto detect', 'auto detect'), ('ssh', 'ssh'), ('winexe', 'winexe')])
    username = forms.CharField(
        initial='root', help_text="Log into remote machine with as this user")
    password = forms.CharField(
        required=False, widget=forms.PasswordInput, help_text="Leave empty if using kerberos or ssh keys")
    windows_domain = forms.CharField(
        required=False, help_text="If remote machine is running a windows domain")


class ChooseHostForm(AdagiosForm):
    host_name = forms.ChoiceField(help_text="Select which host to edit")

    def __init__(self, service=Model.Service(), *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        self.fields['host_name'].choices = get_all_hosts()


class AddServiceToHostForm(AdagiosForm):
    host_name = forms.ChoiceField(
        help_text="Select host which you want to add service check to")
    service = forms.ChoiceField(
        help_text="Select which service check you want to add to this host")

    def __init__(self, service=Model.Service(), *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        self.fields['host_name'].choices = get_all_hosts()
        self.fields['service'].choices = get_inactive_services()


class EditTemplateForm(AdagiosForm):

    def __init__(self, service=Model.Service(), *args, **kwargs):
        self.service = service
        super(forms.Form, self).__init__(*args, **kwargs)

        # Run through all the all attributes. Add
        # to form everything that starts with "_"
        self.description = service['service_description']
        fieldname = "%s::%s::%s" % (
            service['host_name'], service['service_description'], 'register')
        self.fields[fieldname] = forms.BooleanField(
            required=False, initial=service['register'] == "1", label='register')
        self.register = fieldname

        macros = []
        self.command_line = None
        try:
            self.command_line = service.get_effective_command_line()
            for macro, value in service.get_all_macros().items():
                if macro.startswith('$_SERVICE') or macro.startswith('S$ARG'):
                    macros.append(macro)
            for k in sorted(macros):
                fieldname = "%s::%s::%s" % (
                    service['host_name'], service['service_description'], k)
                label = k.replace('$_SERVICE', '')
                label = label.replace('_', ' ')
                label = label.replace('$', '')
                label = label.capitalize()
                self.fields[fieldname] = forms.CharField(
                    required=False, initial=service.get_macro(k), label=label)
        # KeyError can occur if service has an invalid check_command
        except KeyError:
            pass

    def save(self):
        for i in self.changed_data:
            # Changed data comes in the format host_name::service_description::$_SERVICE_PING
            # We need to change that to just __PING
            field_name = i.split('::')[2]
            field_name = field_name.replace('$_SERVICE', '_')
            field_name = field_name.replace('$', '')
            data = self.cleaned_data[i]
            if field_name == 'register':
                data = int(data)
            self.service[field_name] = data
        self.service.save()
        self.service.reload_object()
        # Lets also update commandline because form is being returned to the
        # user
        self.command_line = self.service.get_effective_command_line()
