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
	