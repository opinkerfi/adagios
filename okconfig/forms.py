from django import forms

class ScanNetworkForm(forms.Form):
    network_address = forms.CharField()


class AddGroupForm(forms.Form):
    group_name = forms.CharField()
    alias = forms.CharField()
    force = forms.BooleanField()

class AddHostForm(forms.Form):
    host_name = forms.CharField()
    description = forms.CharField()
    address = forms.CharField()
    force = forms.BooleanField()
    group = forms.CharField()

class AddTemplateForm(forms.Form):
    template_name = forms.ChoiceField()
    host_name = forms.ChoiceField()
    force = forms.BooleanField()
        