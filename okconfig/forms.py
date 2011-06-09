from django import forms
from configurator import okconfig

class ScanNetworkForm(forms.Form):
    network_address = forms.CharField()


class AddGroupForm(forms.Form):
    group_name = forms.CharField()
    alias = forms.CharField()
    force = forms.BooleanField()

class AddHostForm(forms.Form):
    host_name = forms.CharField()
    address = forms.CharField()
    description = forms.CharField()
    group = forms.CharField()
    force = forms.BooleanField()

class AddTemplateForm(forms.Form):
    templates = okconfig.get_templates()
    list = map( lambda x: (x, x), templates )
    hosts = okconfig.get_hosts()
    host_list = map(lambda x: (x, x), hosts)
    # Attributes
    host_name = forms.ChoiceField(choices=host_list)
    template_name = forms.ChoiceField(choices=list)
    force = forms.BooleanField()
        