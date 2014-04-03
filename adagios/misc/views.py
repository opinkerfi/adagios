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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.core.context_processors import csrf
from django.forms.formsets import BaseFormSet
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.utils.translation import ugettext as _

from django.shortcuts import HttpResponse
from django.template import RequestContext
from adagios.misc import forms
import os
import mimetypes

import pynag.Model
import pynag.Utils
import pynag.Control
import pynag.Model.EventHandlers
import pynag.Utils
import os.path
from time import mktime, sleep
from datetime import datetime
from os.path import dirname
from subprocess import Popen, PIPE

import adagios.settings
import adagios.objectbrowser
from adagios import __version__
import adagios.status.utils

from collections import defaultdict
from adagios.views import adagios_decorator, error_page

state = defaultdict(lambda: "unknown")
state[0] = "ok"
state[1] = "warning"
state[2] = "critical"

@adagios_decorator
def index(request):
    c = {}
    c['nagios_cfg'] = pynag.Model.config.cfg_file
    c['version'] = __version__
    return render_to_response('frontpage.html', c, context_instance=RequestContext(request))

@adagios_decorator
def settings(request):
    c = {}
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = e = []
    if request.method == 'GET':
        form = forms.AdagiosSettingsForm(initial=request.GET)
        form.is_valid()
    elif request.method == 'POST':
        form = forms.AdagiosSettingsForm(data=request.POST)
        if form.is_valid():
            try:
                form.save()
                m.append("%s successfully saved." % form.adagios_configfile)
            except IOError, exc:
                e.append(exc)
    else:
        raise Exception("We only support methods GET or POST")
    c['form'] = form
    return render_to_response('settings.html', c, context_instance=RequestContext(request))


@adagios_decorator
def nagios(request):
    c = {}
    c['nagios_url'] = adagios.settings.nagios_url
    return render_to_response('nagios.html', c, context_instance=RequestContext(request))


@adagios_decorator
def gitlog(request):
    """ View that displays a nice log of previous git commits in dirname(config.cfg_file) """
    c = {}
    c.update(csrf(request))
    c['messages'] = m = []
    c['errors'] = []

    # Get information about the committer
    author_name = request.META.get('REMOTE_USER', 'anonymous')
    try:
        contact = pynag.Model.Contact.objects.get_by_shortname(author_name)
        author_email = contact.email or None
    except Exception:
        author_email = None
    nagiosdir = dirname(pynag.Model.config.cfg_file or None)
    git = pynag.Utils.GitRepo(
        directory=nagiosdir, author_name=author_name, author_email=author_email)

    c['nagiosdir'] = nagiosdir
    c['commits'] = []
    if request.method == 'POST':

        try:
            if 'git_init' in request.POST:
                git.init()
            elif 'git_commit' in request.POST:
                filelist = []
                commit_message = request.POST.get(
                    'git_commit_message', "bulk commit by adagios")
                for i in request.POST:
                    if i.startswith('commit_'):
                        filename = i[len('commit_'):]
                        git.add(filename)
                        filelist.append(filename)
                if len(filelist) == 0:
                    raise Exception("No files selected.")
                git.commit(message=commit_message, filelist=filelist)
                m.append("%s files successfully commited." % len(filelist))
        except Exception, e:
            c['errors'].append(e)
    # Check if nagiosdir has a git repo or not
    try:
        c['uncommited_files'] = git.get_uncommited_files()
    except pynag.Model.EventHandlers.EventHandlerError, e:
        if e.errorcode == 128:
            c['no_git_repo_found'] = True

    # Show git history
    try:
        c['commits'] = git.log()

        commit = request.GET.get('show', False)
        if commit != False:
            c['diff'] = git.show(commit)
            difflines = []
            for i in c['diff'].splitlines():
                if i.startswith('---'):
                    tag = 'hide'
                elif i.startswith('+++'):
                    tag = 'hide'
                elif i.startswith('index'):
                    tag = 'hide'
                elif i.startswith('-'):
                    tag = "alert-danger"
                elif i.startswith('+'):
                    tag = "alert-success"
                elif i.startswith('@@'):
                    tag = 'alert-unknown'
                elif i.startswith('diff'):
                    tag = "filename"
                else:
                    continue
                difflines.append({'tag': tag, 'line': i})
            c['difflines'] = difflines
            c['commit_id'] = commit
    except Exception, e:
        c['errors'].append(e)
    return render_to_response('gitlog.html', c, context_instance=RequestContext(request))


@adagios_decorator
def nagios_service(request):
    """ View to restart / reload nagios service """
    c = {}
    c['errors'] = []
    c['messages'] = []
    nagios_bin = adagios.settings.nagios_binary
    nagios_init = adagios.settings.nagios_init_script
    nagios_cfg = adagios.settings.nagios_config
    if request.method == 'GET':
        form = forms.NagiosServiceForm(initial=request.GET)
    else:
        form = forms.NagiosServiceForm(data=request.POST)
        if form.is_valid():
            form.save()
            c['stdout'] = form.stdout
            c['stderr'] = form.stderr
            c['command'] = form.command

            for i in form.stdout.splitlines():
                if i.strip().startswith('Error:'):
                    c['errors'].append(i)
    c['form'] = form
    service = pynag.Control.daemon(
        nagios_bin=nagios_bin, nagios_cfg=nagios_cfg, nagios_init=nagios_init)
    c['status'] = s = service.status()
    if s == 0:
        c['friendly_status'] = "running"
    elif s == 1:
        c['friendly_status'] = "not running"
    else:
        c['friendly_status'] = 'unknown (exit status %s)' % (s, )
    needs_reload = pynag.Model.config.needs_reload()
    c['needs_reload'] = needs_reload
    return render_to_response('nagios_service.html', c, context_instance=RequestContext(request))


@adagios_decorator
def pnp4nagios(request):
    """ View to handle integration with pnp4nagios """
    c = {}
    c['errors'] = e = []
    c['messages'] = m = []

    c['broker_module'] = forms.PNPBrokerModuleForm(initial=request.GET)
    c['templates_form'] = forms.PNPTemplatesForm(initial=request.GET)
    c['action_url'] = forms.PNPActionUrlForm(initial=request.GET)
    c['pnp_templates'] = forms.PNPTemplatesForm(initial=request.GET)

    try:
        c['npcd_config'] = forms.PNPConfigForm(initial=request.GET)
    except Exception, e:
        c['errors'].append(e)
    #c['interesting_objects'] = form.interesting_objects
    if request.method == 'POST' and 'save_broker_module' in request.POST:
        c['broker_module'] = broker_form = forms.PNPBrokerModuleForm(
            data=request.POST)
        if broker_form.is_valid():
            broker_form.save()
            m.append("Broker Module updated in nagios.cfg")
    elif request.method == 'POST' and 'save_action_url' in request.POST:
        c['action_url'] = forms.PNPActionUrlForm(data=request.POST)
        if c['action_url'].is_valid():
            c['action_url'].save()
            m.append('Action_url updated for %s services' %
                     c['action_url'].total_services)
            if c['action_url'].error_services > 0:
                e.append(
                    "%s services could not be updated (check permissions?)" %
                    c['action_url'].error_services)
    elif request.method == 'POST' and 'save_npcd_config' in request.POST:
        c['npcd_config'] = forms.PNPConfigForm(data=request.POST)
        if c['npcd_config'].is_valid():
            c['npcd_config'].save()
            m.append("npcd.cfg updated")

    return render_to_response('pnp4nagios.html', c, context_instance=RequestContext(request))


@adagios_decorator
def edit_file(request, filename):
    """ This view gives raw read/write access to a given filename.

     Please be so kind as not to give direct url access to this function, because it will allow
     Editing of any file the webserver has access to.
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    try:
        c['form'] = forms.EditFileForm(filename=filename, initial=request.GET)
        c['filename'] = filename
        if request.method == 'POST':
            c['form'] = forms.EditFileForm(
                filename=filename, data=request.POST)
            if c['form'].is_valid():
                c['form'].save()
    except Exception, e:
        c['errors'].append(e)
    return render_to_response('editfile.html', c, context_instance=RequestContext(request))


@adagios_decorator
def edit_nagios_cfg(request):
    """ Allows raw editing of nagios.cfg configfile
    """
    return edit_file(request, filename=adagios.settings.nagios_config)


@adagios_decorator
def pnp4nagios_edit_template(request, filename):
    """ Allows raw editing of a pnp4nagios template.

     Will throw security exception if filename is not a pnp4nagios template
    """

    form = forms.PNPTemplatesForm(initial=request.GET)
    if filename in form.templates:
        return edit_file(request, filename=filename)
    else:
        raise Exception(
            "Security violation. You are not allowed to edit %s" % filename)


@adagios_decorator
def icons(request, image_name=None):
    """ Use this view to see nagios icons/logos
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    image_path = '/usr/share/nagios3/htdocs/images/logos/'
    filenames = []
    for root, subfolders, files in os.walk(image_path):
        for filename in files:
            filenames.append(os.path.join(root, filename))
    # Cut image_path out of every filename
    filenames = map(lambda x: x[len(image_path):], filenames)

    # Filter out those silly .gd2 files that don't display inside a browser
    filenames = filter(lambda x: not x.lower().endswith('.gd2'), filenames)

    filenames.sort()
    if not image_name:
        # Return a list of images
        c['images'] = filenames
        return render_to_response('icons.html', c, context_instance=RequestContext(request))
    else:
        if image_name in filenames:
            file_extension = image_name.split('.').pop()
            mime_type = mimetypes.types_map.get(file_extension)
            fsock = open("%s/%s" % (image_path, image_name,))
            return HttpResponse(fsock, mimetype=mime_type)
        else:
            raise Exception("Not allowed to see this image")


@adagios_decorator
def mail(request):
    """ Send a notification email to one or more contacts regarding hosts or services """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c.update(csrf(request))
    c['http_referer'] = request.META.get("HTTP_REFERER")
    c['http_origin'] = request.META.get("HTTP_ORIGIN")
    remote_user = request.META.get('REMOTE_USER', 'anonymous adagios user')
    hosts = []
    services = []
    if request.method == 'GET':
        c['form'] = forms.SendEmailForm(remote_user, initial=request.GET)
        hosts = request.GET.getlist('host') or request.GET.getlist('host[]')
        services = request.GET.getlist(
            'service') or request.GET.getlist('service[]')
        if not services and not hosts:
            c['form'].services = adagios.status.utils.get_services(
                request, host_name='localhost')
    elif request.method == 'POST':
        c['form'] = forms.SendEmailForm(remote_user, data=request.POST)
        services = request.POST.getlist('service') or request.POST.getlist('service[]')
        hosts = request.POST.getlist('host') or request.POST.getlist('host[]')
        c['acknowledged_or_not'] = request.POST.get('acknowledge_all_problems') == 'true'

    for host_name in hosts:
        host_object = adagios.status.utils.get_hosts(request, host_name=host_name)
        if not host_object:
            c['errors'].append(
                "Host %s not found. Maybe a typo or you do not have access to it." % host_name
            )
            continue
        for item in host_object:
            item['host_name'] = item['name']
            item['description'] = "Host Status"
            c['form'].status_objects.append(item)
            c['form'].hosts.append(item)

    for i in services:
        try:
            host_name, service_description = i.split('/', 1)
            service = adagios.status.utils.get_services(request,
                                                        host_name=host_name,
                                                        service_description=service_description
                                                        )
            if not service:
                c['errors'].append(
                    'Service "%s"" not found. Maybe a typo or you do not have access to it ?' % i)
            for x in service:
                c['form'].status_objects.append(x)
                c['form'].services.append(x)
        except AttributeError, e:
            c['errors'].append("AttributeError for '%s': %s" % (i, e))
        except KeyError, e:
            c['errors'].append("Error adding service '%s': %s" % (i, e))

    c['services'] = c['form'].services
    c['hosts'] = c['form'].hosts
    c['status_objects'] = c['form'].status_objects
    c['form'].html_content = render(
        request, "snippets/misc_mail_objectlist.html", c).content
    if request.method == 'POST' and c['form'].is_valid():
        c['form'].save()
    return render_to_response('misc_mail.html', c, context_instance=RequestContext(request))


@adagios_decorator
def test(request):
    """ Generic test view, use this as a sandbox if you like
    """
    c = {}
    c['messages'] = []
    c.update(csrf(request))
    # Get some test data

    if request.method == 'POST':
        c['form'] = forms.PluginOutputForm(data=request.POST)
        if c['form'].is_valid():
            c['form'].parse()
    else:
        c['form'] = forms.PluginOutputForm(initial=request.GET)

    return render_to_response('test.html', c, context_instance=RequestContext(request))


@adagios_decorator
def paste(request):
    """ Generic test view, use this as a sandbox if you like
    """
    c = {}
    c['messages'] = []
    c.update(csrf(request))
    # Get some test data

    if request.method == 'POST':
        c['form'] = forms.PasteForm(data=request.POST)
        if c['form'].is_valid():
            c['form'].parse()
    else:
        c['form'] = forms.PasteForm(initial=request.GET)

    return render_to_response('test2.html', c, context_instance=RequestContext(request))


