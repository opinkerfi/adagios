# -*- coding: utf-8 -*-


from django.shortcuts import render_to_response, redirect, HttpResponse
from django.template import RequestContext
from django.utils.encoding import smart_str
from django import template
from django.core.context_processors import csrf
import adagios.pages
import adagios.settings
import os.path


def index(request):
    pagelist = adagios.pages.get_pagelist(request)
    pages_directory = adagios.settings.extra_pages
    return render_to_response('pages_index.html', locals(), context_instance=RequestContext(request))


def serve_page(request, pagename):
    """ Serve a single custom page in adagios.settings.extra_pages """
    page_directory = adagios.settings.extra_pages
    filename = page_directory + "/" + pagename
    filename = os.path.normpath(filename)
    if not filename.startswith(page_directory):
        raise ValueError(
            "Please only try to load pages within the pages.d directory")

    if not os.path.isfile(filename):
        raise ValueError("Cannot find page %s" % pagename)

    contents = open(filename, 'r').read()
    t = template.Template(contents)
    c = template.Context({})
    html = t.render(c)
    return HttpResponse(html)
