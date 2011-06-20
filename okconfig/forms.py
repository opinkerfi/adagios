from django import forms
from configurator import okconfig
from configurator import helpers




class ScanNetworkForm(forms.Form):
    network_address = forms.CharField()


class AddGroupForm(forms.Form):
    group_name = forms.CharField()
    alias = forms.CharField()
    force = forms.BooleanField(required=False)

class AddHostForm(forms.Form):
    host_name = forms.CharField()
    address = forms.CharField()
    #description = forms.CharField()
    groups = map( lambda x: (x,x), okconfig.get_groups() )
    group_name = forms.ChoiceField(initial="default",choices=groups)
    force = forms.BooleanField(required=False)
    def clean(self):
        if self.cleaned_data.has_key('host_name'):
            host_name = self.cleaned_data['host_name']
            force = self.cleaned_data['force']
            if not force and host_name in helpers.get_host_names():
                raise forms.ValidationError("Host name %s already exists, use force to overwrite" % host_name)
        return forms.Form.clean(self)

class AddTemplateForm(forms.Form):
    templates = okconfig.get_templates()
    templates = map( lambda x: (x, x), templates )
    hosts = helpers.get_host_names()
    host_list = map(lambda x: (x, x), hosts)
    templates.sort()
    host_list.sort()
    # Attributes
    host_name = forms.ChoiceField(choices=host_list)
    template_name = forms.ChoiceField(choices=templates )
    force = forms.BooleanField(required=False)
    def clean(self):
        cleaned_data = self.cleaned_data
        result = forms.Form.clean(self)
        host_name = cleaned_data['host_name']
        template_name = cleaned_data['template_name']
        force = cleaned_data['force']
        if not force: 
            if host_name not in okconfig.get_hosts():
                err = "Host does not exist. Use force to overwrite" % (host_name)
                self._errors['host_name'] = self.error_class(err)
            if template_name not in okconfig.get_templates().keys():
                err = "Template %s not found. Use force to overwrite" % (template_name)
                self._errors['template_name'] = self.error_class(err)
        return result

        