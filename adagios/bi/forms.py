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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django import forms
from django.utils.translation import ugettext as _
import adagios.status.utils
import adagios.bi


class RemoveSubProcessForm(forms.Form):

    """ Remove one specific sub process from a business process
    """
    process_name = forms.CharField(max_length=100, required=True)
    process_type = forms.CharField(max_length=100, required=True)

    def __init__(self, instance, *args, **kwargs):
        self.bp = instance
        super(RemoveSubProcessForm, self).__init__(*args, **kwargs)

    def save(self):
        process_name = self.cleaned_data.get('process_name')
        process_type = self.cleaned_data.get('process_type')
        self.bp.remove_process(process_name, process_type)
        self.bp.save()

status_method_choices = map(
    lambda x: (x, x), adagios.bi.BusinessProcess.status_calculation_methods)


class BusinessProcessForm(forms.Form):

    """ Use this form to edit a BusinessProcess """
    name = forms.CharField(max_length=100, required=True,
                           help_text="Unique name for this business process.")
    #processes = forms.CharField(max_length=100, required=False)
    display_name = forms.CharField(max_length=100, required=False,
                                   help_text="This is the name that will be displayed to users on this process. Usually it is the name of the system this business group represents.")
    notes = forms.CharField(max_length=1000, required=False,
                            help_text="Here you can put in any description of the business process you are adding. Its a good idea to write down what the business process is about and who to contact in case of downtimes.")
    status_method = forms.ChoiceField(
        choices=status_method_choices, help_text="Here you can choose which method is used to calculate the global status of this business process")
    state_0 = forms.CharField(max_length=100, required=False,
                              help_text="Human friendly text for this respective state. You can type whatever you want but nagios style exit codes indicate that 0 should be 'ok'")
    state_1 = forms.CharField(max_length=100, required=False,
                              help_text="Typically used to represent warning or performance problems")
    state_2 = forms.CharField(max_length=100, required=False,
                              help_text="Typically used to represent critical status")
    state_3 = forms.CharField(
        max_length=100, required=False, help_text="Use this when status is unknown")
    #graphs = models.ManyToManyField(BusinessProcess, unique=False, blank=True)
    #graphs = models.ManyToManyField(BusinessProcess, unique=False, blank=True)

    def __init__(self, instance, *args, **kwargs):
        self.bp = instance
        super(BusinessProcessForm, self).__init__(*args, **kwargs)

    def save(self):
        c = self.cleaned_data
        self.bp.data.update(c)
        self.bp.save()

    def remove(self):
        c = self.data
        process_name = c.get('process_name')
        process_type = c.get('process_type')
        if process_type == 'None':
            process_type = None
        self.bp.remove_process(process_name, process_type)
        self.bp.save()

    def clean(self):
        cleaned_data = super(BusinessProcessForm, self).clean()

        # If name has changed, look if there is another business process with
        # same name.
        new_name = cleaned_data.get('name')
        if new_name and new_name != self.bp.name:
            if new_name in adagios.bi.get_all_process_names():
                raise forms.ValidationError(
                    "Cannot rename process to %s. Another process with that name already exists" % new_name
                )
        return cleaned_data

    def delete(self):
        """ Delete this business process """
        self.bp.delete()

    def add_process(self):

        process_name = self.data.get('process_name')
        hostgroup_name = self.data.get('hostgroup_name')
        servicegroup_name = self.data.get('servicegroup_name')
        service_name = self.data.get('service_name')

        if process_name:
            self.bp.add_process(process_name, None)
        if hostgroup_name:
            self.bp.add_process(hostgroup_name, None)
        if servicegroup_name:
            self.bp.add_process(servicegroup_name, None)
        if service_name:
            self.bp.add_process(service_name, None)
        self.bp.save()

choices = 'businessprocess', 'hostgroup', 'servicegroup', 'service', 'host'
process_type_choices = map(lambda x: (x, x), choices)


class AddSubProcess(forms.Form):
    process_type = forms.ChoiceField(choices=process_type_choices)
    process_name = forms.CharField(
        widget=forms.HiddenInput(attrs={'style': "width: 300px;"}), max_length=100)
    display_name = forms.CharField(max_length=100, required=False)
    tags = forms.CharField(
        max_length=100, required=False, initial="not critical")

    def __init__(self, instance, *args, **kwargs):
        self.bp = instance
        super(AddSubProcess, self).__init__(*args, **kwargs)

    def save(self):
        self.bp.add_process(**self.cleaned_data)
        self.bp.save()


class AddHostgroupForm(forms.Form):
    pass


class AddGraphForm(forms.Form):
    host_name = forms.CharField(max_length=100,)
    service_description = forms.CharField(max_length=100, required=False)
    metric_name = forms.CharField(max_length=100, required=True)
    notes = forms.CharField(max_length=100, required=False,
                            help_text="Put here a friendly description of the graph")

    def __init__(self, instance, *args, **kwargs):
        self.bp = instance
        super(AddGraphForm, self).__init__(*args, **kwargs)

    def save(self):
        self.bp.add_pnp_graph(**self.cleaned_data)
        self.bp.save()
