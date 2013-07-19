#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
static_businessprocesses .. This script loads a business process and staticly writes html view for it
"""

#source_template = "/usr/lib/python2.6/site-packages/adagios/status/templates/business_process_view.html"
source_template = "/etc/adagios/pages.d/bi_process.html"
destination_directory = "/var/www/iceland.adagios.org"
pnp_parameters = "&graph_width=350&graph_height=30"

import os
os.environ['DJANGO_SETTINGS_MODULE'] = "adagios.settings"
import simplejson as json

from django.shortcuts import render
from django import template
from django.test.client import Client
from optparse import OptionParser


import adagios.bi
import django.http
from adagios.pnp.functions import run_pnp


# Start by parsing some arguments
parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")

parser.add_option('--all', help="Parse all business processes", dest="all", action="store_true", default=False)
parser.add_option('--graphs', help="", dest="graphs", action="store_true", default=False)
parser.add_option('--destination', help="destination to write static html into", dest="destination", default=destination_directory)
parser.add_option('--source-template', help="Source template used to render business processes", dest="source", default=source_template)
parser.add_option('--verbose', help="verbose output", dest="verbose", action="store_true", default=False)


(options, args) = parser.parse_args()


def verbose(message):
    if options.verbose:
        print message


def businessprocess_to_html(process_name, process_type='businessprocess'):
    bp = adagios.bi.get_business_process(process_name=process_name, process_type=process_type)
    verbose("Rendering business process %s" % bp.name)
    c = {}
    c['bp'] = bp
    c['csrf_token'] = ''
    c['graphs_url'] = "graphs.json"
    c['static'] = True

    directory = "%s/%s" % (options.destination, bp.name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if options.graphs:
        graphs = bi_graphs_to_json(process_name, process_type)
        for i in graphs:
            url = i.get('image_url')
            client = Client()
            verbose("Saving image %s" % url)
            image = client.get("/pnp/image?%s&%s" % (url, pnp_parameters)).content
            graph_filename = "%s/%s.png" % (directory, url)
            open(graph_filename, 'w').write(image)
        graph_json_file = "%s/graphs.json" % (directory)
        for i in graphs:
            i['image_url'] = i['image_url'] + '.png'
        graph_json = json.dumps(graphs, indent=4)
        open(graph_json_file, 'w').write(graph_json)

    content = open(options.source, 'r').read()
    t = template.Template(content)
    c = template.Context(c)
    
    html = t.render(c)
    destination_file = "%s/index.html" % directory
    open(destination_file, 'w').write(html.encode('utf-8'))


def bi_graphs_to_json(process_name, process_type='businessprocess'):
    c = {}
    c['messages'] = []
    c['errors'] = []
    bp = adagios.bi.get_business_process(process_name=process_name, process_type=process_type)

    graphs = []
    if not bp.graphs:
        return []
    for graph in bp.graphs or []:
        if graph.get('graph_type') == 'pnp':
            host_name = graph.get('host_name')
            service_description = graph.get('service_description')
            metric_name = graph.get('metric_name')
            pnp_result = run_pnp('json', host=graph.get('host_name'), srv=graph.get('service_description'))
            json_data = json.loads(pnp_result)
            for i in json_data:
                if i.get('ds_name') == graph.get('metric_name'):
                    notes = graph.get('notes')
                    last_value = bp.get_pnp_last_value(host_name, service_description, metric_name)
                    i['last_value'] = last_value
                    i['notes'] = notes
                    graphs.append(i)
    return graphs


if options.all:
    processlist = adagios.bi.get_all_process_names()
else:
    processlist = args

if not processlist:
    parser.error("Either provide business process name or specify --all")

for i in processlist:
    print "doing ", i
    businessprocess_to_html(i)
