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

from django.core.mail import send_mail
import os.path
from adagios import settings
from pynag import Model, Control

TOPIC_CHOICES = (
	('general', 'General Suggestion'),
	('bug', 'I think i have found a bug'),
	('suggestion', 'I have a particular task in mind that i would like to do with Adagios'),
	('easier', 'I have an idea how make a certain task easier to do'),
				)

class ContactUsForm(forms.Form):
	topic = forms.ChoiceField(choices=TOPIC_CHOICES)
	sender = forms.CharField(
							required=False,
							help_text="Optional email address if you want feedback from us",
							)
	message = forms.CharField(
							widget=forms.widgets.Textarea(attrs={'rows':15, 'cols':40}),
							help_text="See below for examples of good suggestions",
							)
	def save(self):
		from_address = 'adagios@adagios.opensource.is'
		to_address = ["palli@ok.is"]
		subject = "Suggestion from Adagios"
		
		sender = self.cleaned_data['sender']
		topic = self.cleaned_data['topic']
		message = self.cleaned_data['message']
		
		msg = """
		topic: %s
		from: %s
		
		%s
		""" % (topic,sender,message)
		send_mail(subject, msg, from_address, to_address, fail_silently=False)
class AdagiosSettingsForm(forms.Form):
	configuration_file = forms.CharField(required=False, initial=settings.nagios_config, help_text="Path to nagios configuration file. Leave empty for automatic discovery.")
	nagios_url = forms.CharField(required=False, initial=settings.nagios_url, help_text="URL (relative or absolute) to your nagios webcgi. Adagios will use this to make it simple to navigate from a configured host/service directly to the cgi.")
	git_commit_on_changes = forms.BooleanField(required=False, initial=settings.enable_githandler, help_text="If set. Adagios will commit any changes it makes to git repository.")
	log_to_file_on_changes = forms.BooleanField(required=False, initial=settings.enable_loghandler, help_text="If set. Adagios will log any changes it makes to a file.")

	
class OkconfigEditTemplateForm(forms.Form):
	register = forms.BooleanField()
	service_description = forms.CharField()

class PerfDataForm(forms.Form):
    perfdata = forms.CharField()
    def save(self):
        from pynag import Model
        perfdata = self.cleaned_data['perfdata']
        perfdata = Model.PerfData(perfdata)
        self.results = perfdata.metrics

COMMAND_CHOICES = [('reload','reload'), ('status','status'),('restart','restart'),('stop','stop'),('start','start')]
if os.path.isfile('/etc/init.d/nagios3'):
    NAGIOS_INIT = '/etc/init.d/nagios3'
else:
    NAGIOS_INIT = "/etc/init.d/nagios"
if os.path.isfile('/usr/bin/nagios'):
    NAGIOS_BIN='/usr/bin/nagios'
else:
    NAGIOS_BIN="/usr/sbin/nagios3"
class NagiosServiceForm(forms.Form):
    """ Maintains control of the nagios service / reload / restart / etc """
    path_to_init_script = forms.CharField(help_text="Path to your nagios init script", initial=NAGIOS_INIT)
    #nagios_binary = forms.CharField(help_text="Path to your nagios binary", initial=NAGIOS_BIN)
    command = forms.ChoiceField(choices=COMMAND_CHOICES)
    def save(self):
        #nagios_bin = self.cleaned_data['nagios_bin']
        nagios_init = self.cleaned_data['path_to_init_script']
        command = self.cleaned_data['command']
        from subprocess import Popen, PIPE
        p = Popen([nagios_init,command], stdout=PIPE, stderr=PIPE)
        self.stdout = p.stdout.read()
        self.stderr = p.stdout.read()
