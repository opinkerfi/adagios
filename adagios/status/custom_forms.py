# -*- coding: utf-8 -*-
#
# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Matthieu Caneill <matthieu.caneill@savoirfairelinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module defines the forms used in the views engine.

The forms are dynamically generated, w.r.t. the data being passed,
the available columns in the current Livestatus instance, and
the available templates and filters in the looked-up directories.

For the configuration, see adagios.settings.CUSTOM_*

The forms generated here are transformed into formsets by views.py,
which allows to have multiple values.
The data is stored in user.views[<viewname>], that's being managed
by views.py as well.
"""

import os

from adagios.status import custom_columns
from adagios.status import custom_filters

from django import forms
from adagios import settings
from django.utils.translation import ugettext as _

#NONE_CHOICE = [('', '(None)')]

def _get_columns_names(datasource='hosts'):
    """
    Returns the list of columns (coming from custom_columns) for the
    specified table (datasource).
    """
    columns = custom_columns.all_columns
    s = [x['name'] for x in columns[datasource]]
    return [(x,x) for x in s]

def _get_html_files_in(path):
    """
    Returns a list of tuples usable in a select/option field.
    The elements are file present in `path` and ending with .html.
    The first element (<option> value) is the file name,
    the second (<option> display) rm's the .html and is title'ised.
    """
    files = sorted([x for x in os.listdir(path) if x.endswith('.html')])
    return [(x, x[:-5].title().replace('_', ' ')) for x in files]

def _get_metadata_templates():
    """
    List of templates for metadataform.template.
    """
    return _get_html_files_in(settings.CUSTOM_TEMPLATES_PATH)

def _get_columns_widgets():
    """
    List of templates for columnsform.widget.
    """
    return _get_html_files_in(settings.CUSTOM_WIDGETS_PATH)

class NumberInput(forms.TextInput):
    """ HTML5 number field (not implemented in Django 1.4) """
    input_type = 'number'

class MetadataForm(forms.Form):
    view_name = forms.CharField(
        help_text=_('Give a unique name to your view.'),)
    data_source = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': True}),
        help_text=_('Where does the data come from?'),)
    template = forms.ChoiceField(
        choices=_get_metadata_templates(),
        initial='table.html',
        help_text=_('The template which will be used to render selected data.'),)
    reload_interval = forms.CharField(
        required=False,
        help_text=_('Number of seconds between two reloads of the view, 0 to disable auto-reload.'),
        initial=0,
        widget=NumberInput(attrs={'min': 0, 'max': 600, 'step': 10}),)
    fullscreen = forms.BooleanField(
        required=False,
        help_text=_("Option to have the view rendered full screen (without the surrounding menus)."),)

class ColumnsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ColumnsForm, self).__init__(*args, **kwargs)
        
        self.fields['name'] = forms.ChoiceField(
            choices=_get_columns_names(datasource=self.datasource),
            help_text=_('The column you want to display.'),)
        self.fields['widget'] = forms.ChoiceField(
            choices=_get_columns_widgets(),
            initial='default.html',
            help_text=_('The widget used to display column data.'),)

class FiltersForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(FiltersForm, self).__init__(*args, **kwargs)
        
        self.fields['column'] = forms.ChoiceField(
            choices=_get_columns_names(datasource=self.datasource),
            )
        # let's get the value of this particular column
        if kwargs.get('initial', False): # GET
            try:
                column = kwargs['initial']['column']
            except KeyError:
                column = None
        else: # POST
            try:
                column = kwargs['data'][kwargs['prefix'] + '-column']
            except KeyError:
                column = None
        
        if column:
            self.fields.update(custom_filters.get_filter(self.datasource, column)().get_fields())

class SortsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SortsForm, self).__init__(*args, **kwargs)

        self.fields['column'] = forms.ChoiceField(
            choices=_get_columns_names(datasource=self.datasource),
            help_text=_('Sort by...'),)
        
        self.fields['reverse'] = forms.BooleanField(
            required=False,
            help_text=_('Descending order?'),)

class StatsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(StatsForm, self).__init__(*args, **kwargs)
        
        self.fields['column'] = forms.ChoiceField(
            choices=_get_columns_names(datasource=self.datasource),
            help_text=_('Stats by...'),)

        self.fields['value'] = forms.CharField(required=False)
