#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
static_businessprocesses .. This script loads a business process and staticly writes html view for it
"""

source_template = "/home/palli/workspace/adagios/adagios/status/templates/business_process_view.html"
header = "<html><body>"
footer = "</body></html>"


import os
os.environ['DJANGO_SETTINGS_MODULE'] = "adagios.settings"

from django.shortcuts import render
from django import template
import adagios.businessprocess
import django.http


def businessprocess_to_html(process_name, process_type='businessprocess'):
    bp = adagios.businessprocess.get_business_process(process_name=process_name, process_type=process_type)
    c = {}
    c['bp'] = bp

    content = open(source_template,'r').read()
    t = template.Template(content)
    c = template.Context(c)

    html = t.render(c)
    return html.encode('utf-8')


print businessprocess_to_html('blabla')