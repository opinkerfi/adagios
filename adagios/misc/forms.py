# -*- coding: utf-8 -*-
#
# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2010, Pall Sigurdsson <palli@opensource.is>
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

from django import forms

from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _

import os.path
from adagios import settings
import adagios.utils
from pynag import Model
from django.core.mail import EmailMultiAlternatives
import pynag.Parsers
import pynag.Control.Command
import adagios.daemon


TOPIC_CHOICES = (
    ('general', _('General Suggestion')),
    ('bug', _('I think i have found a bug')),
    ('suggestion', _('I have a particular task in mind that i would like to do with Adagios')),
    ('easier', _('I have an idea how make a certain task easier to do')),
)

pnp_loglevel_choices = [
    ('0', _('0 - Only Errors')),
    ('1', _('1 - Little logging')),
    ('2', _('2 - Log Everything')),
    ('-1', _('-1 Debug mode (log all and slower processing'))
]
pnp_log_type_choices = [('syslog', 'syslog'), ('file', 'file')]

COMMAND_CHOICES = [('reload', 'reload'), ('status', 'status'),
                   ('restart', 'restart'), ('stop', 'stop'), ('start', 'start')]


initial_paste = """
define service {
    host_name  host01.example.com
    service_description http://host01.example.com
    use     template-http
}

define service {
    name        template-http
    check_command   okc-check_http
}
"""

class ContactUsForm(forms.Form):
    topic = forms.ChoiceField(choices=TOPIC_CHOICES)
    sender = forms.CharField(
        required=False,
        help_text=_("Optional email address if you want feedback from us"),
    )
    message = forms.CharField(
        widget=forms.widgets.Textarea(
            attrs={'rows': 15, 'cols': 40}),
        help_text=_("See below for examples of good suggestions"),
    )

    def save(self):
        from_address = 'adagios@adagios.opensource.is'
        to_address = ["palli@ok.is"]
        subject = _("Suggestion from Adagios")

        sender = self.cleaned_data['sender']
        topic = self.cleaned_data['topic']
        message = self.cleaned_data['message']

        msg = _("""
        topic: %(topic)s
        from: %(sender)s

        %(message)s
        """) % {'topic': topic, 'sender': sender, 'message': message}
        send_mail(subject, msg, from_address, to_address, fail_silently=False)


class UserdataForm(forms.Form):
    language = forms.ChoiceField(
        choices=settings.LANGUAGES,
        required=False
    )
    theme = forms.ChoiceField(
        choices=[(x, x) for x in adagios.utils.get_available_themes()],
        required=False
    )
    refresh_rate = forms.IntegerField(
        help_text="For pages that auto-reload. Set the number of seconds to wait between page refreshes. "
                  "Set refresh rate to 0 to disable automatic refreshing.",
        required=False,
    )


class AdagiosSettingsForm(forms.Form):
    nagios_config = forms.CharField(
        required=False, initial=settings.nagios_config,
        help_text=_("Path to nagios configuration file. i.e. /etc/nagios/nagios.cfg"))
    destination_directory = forms.CharField(
        required=False, initial=settings.destination_directory, help_text=_("Where to save new objects that adagios creates."))
    nagios_url = forms.CharField(required=False, initial=settings.nagios_url,
                                 help_text=_("URL (relative or absolute) to your nagios webcgi. Adagios will use this to make it simple to navigate from a configured host/service directly to the cgi."))
    nagios_service = forms.CharField(
        required=False,
        help_text=_("The name of the nagios service, commonly nagios or nagios3. Adagios will use this when stopping/starting/reloading nagios"))
    nagios_init_script = forms.CharField(
        required=False,
        help_text=_("You should define either 'Nagios service' or 'Nagios init script'. Path to you nagios init script. Adagios will use this when stopping/starting/reloading nagios"))
    nagios_binary = forms.CharField(
        help_text=_("Path to you nagios daemon binary. Adagios will use this to verify config with 'nagios -v nagios_config'"))
    livestatus_path = forms.CharField(
        help_text=_("Path to MK Livestatus socket. If left empty Adagios will try to autodiscover from your nagios.cfg"),
        required=False,
    )
    livestatus_limit = forms.IntegerField(
        help_text=_("Limit the number of rows shown per page in the status view to this."),
    )
    enable_githandler = forms.BooleanField(
        required=False, initial=settings.enable_githandler, help_text=_("If set. Adagios will commit any changes it makes to git repository."))
    enable_loghandler = forms.BooleanField(
        required=False, initial=settings.enable_loghandler, help_text=_("If set. Adagios will log any changes it makes to a file."))
    enable_authorization = forms.BooleanField(
        required=False, initial=settings.enable_authorization,
        help_text=_("If set. Users in Status view will only see hosts/services they are a contact for. Unset means everyone will see everything."))
    enable_status_view = forms.BooleanField(
        required=False, initial=settings.enable_status_view,
        help_text=_("If set. Enable status view which is an alternative to nagios legacy web interface. You will need to restart web server for the changes to take effect"))
    enable_local_logs = forms.BooleanField(
        required=False, initial=settings.enable_local_logs,
        help_text=_("If set, allow adagios to read logfiles from the monitoring engine. Might be performance sensitive)"))
    auto_reload = forms.BooleanField(
        required=False, initial=settings.auto_reload,
        help_text=_("If set. Nagios is reloaded automatically after every change."))
    warn_if_selinux_is_active = forms.BooleanField(
        required=False, help_text=_("Adagios does not play well with SElinux. So lets issue a warning if it is active. Only disable this if you know what you are doing."))
    pnp_filepath = forms.CharField(
        help_text=_("Full path to your pnp4nagios/index.php file. Adagios will use this to generate graphs"))
    pnp_url = forms.CharField(
        help_text=_("Full or relative url to pnp4nagios web interface, adagios can use this to link directly to pnp"))
    map_center = forms.CharField(
        help_text=_("Default coordinates when opening up the world map. This should be in the form of longitude,latitude"))
    map_zoom = forms.CharField(
        help_text=_("Default Zoom level when opening up the world map. 10 is a good default value"))
    language = forms.ChoiceField(choices=settings.LANGUAGES, required=False)
    theme = forms.ChoiceField(required=False, choices=[(x,x) for x in adagios.utils.get_available_themes()])
    refresh_rate = forms.IntegerField(
        help_text="For pages that auto-reload. Set the number of seconds to wait between page refreshes. "
                  "Set refresh rate to 0 to disable automatic refreshing."
    )
    enable_pnp4nagios = forms.BooleanField(required=False, help_text="If set, include pnp4nagios graphs in status views")
    enable_graphite = forms.BooleanField(required=False, help_text="If set, include graphite graphs in status views")
    graphite_url = forms.CharField(help_text="Path to your graphite install.", required=False)
    graphite_querystring = forms.CharField(help_text="Querystring that is passed into graphite's /render method. {host} is replaced with respective hostname while {host_} will apply common graphite escaping. i.e. example.com -> example_com", required=False)
    graphite_title = forms.CharField(help_text="Use this title on all graphs coming from graphite", required=False)
    default_host_template = forms.CharField(help_text="Use this template by default when adding new hosts.")
    default_service_template = forms.CharField(help_text="Use this template by default when adding new services.")
    default_contact_template = forms.CharField(help_text="Use this template by default when adding new contacts.")
    include = forms.CharField(
        required=False, help_text=_("Include configuration options from files matching this pattern"))

    def save(self):
        # First of all, if configfile does not exist, lets try to create it:
        if not os.path.isfile(settings.adagios_configfile):
            open(settings.adagios_configfile, 'w').write(
                _("# Autocreated by adagios"))
        for k, v in self.cleaned_data.items():
            Model.config._edit_static_file(
                attribute=k, new_value=v, filename=settings.adagios_configfile)
            self.adagios_configfile = settings.adagios_configfile
            #settings.__dict__[k] = v

    def __init__(self, *args, **kwargs):
        # Since this form is always bound, lets fetch current configfiles and
        # prepare them as post:
        if 'data' not in kwargs or kwargs['data'] == '':
            kwargs['data'] = settings.__dict__
        super(self.__class__, self).__init__(*args, **kwargs)

    def clean_pnp_filepath(self):
        filename = self.cleaned_data['pnp_filepath']
        return self.check_file_exists(filename)

    def clean_destination_directory(self):
        filename = self.cleaned_data['destination_directory']
        return self.check_file_exists(filename)

    def clean_nagios_init_script(self):
        filename = self.cleaned_data['nagios_init_script']
        if filename.startswith('sudo'):
            self.check_file_exists(filename.split()[1])
        elif filename:
            self.check_file_exists(filename)
        return filename

    def clean_nagios_binary(self):
        filename = self.cleaned_data['nagios_binary']
        return self.check_file_exists(filename)

    def clean_nagios_config(self):
        filename = self.cleaned_data['nagios_config']
        return self.check_file_exists(filename)

    def check_file_exists(self, filename):
        """ Raises validation error if filename does not exist """
        if not os.path.exists(filename):
            raise forms.ValidationError('No such file or directory')
        return filename

    def clean(self):
        cleaned_data = super(self.__class__, self).clean()
        for k, v in cleaned_data.items():
            # Convert all unicode to quoted strings
            if type(v) == type(u''):
                cleaned_data[k] = str('''"%s"''' % v)
            # Convert all booleans to True/False strings
            elif type(v) == type(False):
                cleaned_data[k] = str(v)
        return cleaned_data


class EditAllForm(forms.Form):

    """ This form intelligently modifies all attributes of a specific type.


    """

    def __init__(self, object_type, attribute, new_value, *args, **kwargs):
        self.object_type = object_type
        self.attribute = attribute
        self.new_value = new_value
        super(self.__class__, self).__init__(self, args, kwargs)
        search_filter = {}
        search_filter['object_type'] = object_type
        search_filter['%s__isnot' % attribute] = new_value
        items = Model.ObjectDefinition.objects.filter(**search_filter)
        interesting_objects = []
        for i in items:
            if attribute in i._defined_attributes or i.use is None:
                interesting_objects.append(i)
        self.interesting_objects = interesting_objects
        for i in interesting_objects:
            self.fields['modify_%s' % i.get_id()] = forms.BooleanField(
                required=False, initial=True)


class PNPActionUrlForm(forms.Form):

    """ This form handles applying action_url to bunch of hosts and services """
    #apply_action_url = forms.BooleanField(required=False,initial=True,help_text="If set, apply action_url to every service object in nagios")
    action_url = forms.CharField(
        required=False, initial="/pnp4nagios/graph?host=$HOSTNAME$&srv=$SERVICEDESC$",
        help_text=_("Reset the action_url attribute of every service check in your nagios configuration with this one. "))

    def save(self):
        action_url = self.cleaned_data['action_url']
        services = Model.Service.objects.filter(action_url__isnot=action_url)
        self.total_services = len(services)
        self.error_services = 0
        for i in services:
            if 'action_url' in i._defined_attributes or i.use is None:
                i.action_url = action_url
                try:
                    i.save()
                except Exception:
                    self.error_services += 1


class PNPTemplatesForm(forms.Form):

    """ This form manages your pnp4nagios templates """

    def __init__(self, *args, **kwargs):
        self.template_directories = []
        self.templates = []
        tmp = Model.config._load_static_file('/etc/pnp4nagios/config.php')
        for k, v in tmp:
            if k == "$conf['template_dirs'][]":
                # strip all ' and " from directory
                directory = v.strip(";").strip('"').strip("'")
                self.template_directories.append(directory)
                if os.path.isdir(directory):
                    for f in os.listdir(directory):
                        self.templates.append("%s/%s" % (directory, f))

        super(self.__class__, self).__init__(*args, **kwargs)


class PNPConfigForm(forms.Form):

    """ This form handles the npcd.cfg configuration file """
    user = forms.CharField(
        help_text=_("npcd service will have privileges of this group"))
    group = forms.CharField(
        help_text=_("npcd service will have privileges of this user"))
    log_type = forms.ChoiceField(
        widget=forms.RadioSelect, choices=pnp_log_type_choices, help_text=_("Define if you want to log to 'syslog' or 'file'"))
    log_file = forms.CharField(
        help_text=_("If log_type is set to file. Log to this file"))
    max_logfile_size = forms.IntegerField(
        help_text=_("Defines the maximum filesize (bytes) before logfile will rotate."))
    log_level = forms.ChoiceField(
        help_text=_("How much should we log?"), choices=pnp_loglevel_choices)
    perfdata_spool_dir = forms.CharField(
        help_text=_("where we can find the performance data files"))
    perfdata_file_run_cmd = forms.CharField(
        help_text=_("execute following command for each found file in perfdata_spool_dir"))
    perfdata_file_run_cmd_args = forms.CharField(
        required=False, help_text=_("optional arguments to perfdata_file_run_cmd"))
    identify_npcd = forms.ChoiceField(widget=forms.RadioSelect, choices=(
        ('1', 'Yes'), ('0', 'No')), help_text=_("If yes, npcd will append -n to the perfdata_file_run_cmd"))
    npcd_max_threads = forms.IntegerField(
        help_text=_("Define how many parallel threads we should start"))
    sleep_time = forms.IntegerField(
        help_text=_("How many seconds npcd should wait between dirscans"))
    load_threshold = forms.FloatField(
        help_text=_("npcd won't start if load is above this threshold"))
    pid_file = forms.CharField(help_text=_("Location of your pid file"))
    perfdata_file = forms.CharField(
        help_text=_("Where should npcdmod.o write the performance data. Must not be same directory as perfdata_spool_dir"))
    perfdata_spool_filename = forms.CharField(
        help_text=_("Filename for the spooled files"))
    perfdata_file_processing_interval = forms.IntegerField(
        help_text=_("Interval between file processing"))

    def __init__(self, initial=None, *args, **kwargs):
        if not initial:
            initial = {}
        my_initial = {}
        # Lets use PNPBrokerModuleForm to find sensible path to npcd config
        # file
        broker_form = PNPBrokerModuleForm()
        self.npcd_cfg = broker_form.initial.get('config_file')
        npcd_values = Model.config._load_static_file(self.npcd_cfg)
        for k, v in npcd_values:
            my_initial[k] = v
        super(self.__class__, self).__init__(
            initial=my_initial, *args, **kwargs)

    def save(self):
        for i in self.changed_data:
            Model.config._edit_static_file(
                attribute=i, new_value=self.cleaned_data[i], filename=self.npcd_cfg)


class EditFileForm(forms.Form):

    """ Manages editing of a single file """
    filecontent = forms.CharField(widget=forms.Textarea(
        attrs={'wrap': 'off', 'rows': '50', 'cols': '2000'}))

    def __init__(self, filename, initial=None, *args, **kwargs):
        if not initial:
            initial = {}
        self.filename = filename
        my_initial = initial.copy()
        if 'filecontent' not in my_initial:
            my_initial['filecontent'] = open(filename).read()
        super(self.__class__, self).__init__(
            initial=my_initial, *args, **kwargs)

    def save(self):
        if 'filecontent' in self.changed_data:
            data = self.cleaned_data['filecontent']
            open(self.filename, 'w').write(data)


class PNPBrokerModuleForm(forms.Form):

    """ This form is responsible for configuring PNP4Nagios. """
    #enable_pnp= forms.BooleanField(required=False, initial=True,help_text="If set, PNP will be enabled and will graph Nagios Performance Data.")
    broker_module = forms.CharField(
        help_text=_("Full path to your npcdmod.o broker module that shipped with your pnp4nagios installation"))
    config_file = forms.CharField(
        help_text=_("Full path to your npcd.cfg that shipped with your pnp4nagios installation"))
    event_broker_options = forms.IntegerField(
        initial="-1", help_text=_("Nagios's default of -1 is recommended here. PNP Documentation says you will need at least bits 2 and 3. Only change this if you know what you are doing."))
    process_performance_data = forms.BooleanField(
        required=False, initial=True, help_text=_("PNP Needs the nagios option process_performance_data enabled to function. Make sure it is enabled."))
    #apply_action_url = forms.BooleanField(required=False,initial=True,help_text="If set, apply action_url to every service object in nagios")
    #action_url=forms.CharField(required=False,initial="/pnp4nagios/graph?host=$HOSTNAME$&srv=$SERVICEDESC$", help_text="Action url that your nagios objects can use to access perfdata")

    def clean_broker_module(self):
        """ Raises validation error if filename does not exist """
        filename = self.cleaned_data['broker_module']
        if not os.path.exists(filename):
            raise forms.ValidationError('File not found')
        return filename

    def clean_config_file(self):
        """ Raises validation error if filename does not exist """
        filename = self.cleaned_data['config_file']
        if not os.path.exists(filename):
            raise forms.ValidationError('File not found')
        return filename

    def __init__(self, initial=None, *args, **kwargs):
        if not initial:
            initial = {}
        my_initial = {}
        Model.config.parse()
        maincfg_values = Model.config.maincfg_values
        self.nagios_configline = None
        for k, v in Model.config.maincfg_values:
            if k == 'broker_module' and v.find('npcdmod.o') > 0:
                self.nagios_configline = v
                v = v.split()
                my_initial['broker_module'] = v.pop(0)
                for i in v:
                    if i.find('config_file=') > -1:
                        my_initial['config_file'] = i.split('=', 1)[1]
            elif k == "event_broker_options":
                my_initial[k] = v
        # If view specified any initial values, they overwrite ours
        for k, v in initial.items():
            my_initial[k] = v
        if 'broker_module' not in my_initial:
            my_initial['broker_module'] = self.get_suggested_npcdmod_path()
        if 'config_file' not in my_initial:
            my_initial['config_file'] = self.get_suggested_npcd_path()
        super(self.__class__, self).__init__(
            initial=my_initial, *args, **kwargs)

    def get_suggested_npcdmod_path(self):
        """ Returns best guess for full path to npcdmod.o file """
        possible_locations = [
            "/usr/lib/pnp4nagios/npcdmod.o",
            "/usr/lib64/nagios/brokers/npcdmod.o",
        ]
        for i in possible_locations:
            if os.path.isfile(i):
                return i
        return possible_locations[-1]

    def get_suggested_npcd_path(self):
        """ Returns best guess for full path to npcd.cfg file """
        possible_locations = [
            "/etc/pnp4nagios/npcd.cfg"
        ]
        for i in possible_locations:
            if os.path.isfile(i):
                return i
        return possible_locations[-1]

    def save(self):
        if 'broker_module' in self.changed_data or 'config_file' in self.changed_data or self.nagios_configline is None:
            v = "%s config_file=%s" % (
                self.cleaned_data['broker_module'], self.cleaned_data['config_file'])
            Model.config._edit_static_file(
                attribute="broker_module", new_value=v, old_value=self.nagios_configline, append=True)

        # We are supposed to handle process_performance_data attribute.. lets
        # do that here
        process_performance_data = "1" if self.cleaned_data[
            'process_performance_data'] else "0"
        Model.config._edit_static_file(
            attribute="process_performance_data", new_value=process_performance_data)

        # Update event broker only if it has changed
        name = "event_broker_options"
        if name in self.changed_data:
            Model.config._edit_static_file(
                attribute=name, new_value=self.cleaned_data[name])


class PluginOutputForm(forms.Form):
    plugin_output = forms.CharField(
        widget=forms.Textarea(attrs={'wrap': 'off', 'cols': '80'}))

    def parse(self):
        from pynag import Utils
        plugin_output = self.cleaned_data['plugin_output']
        output = Utils.PluginOutput(plugin_output)
        self.results = output


class NagiosServiceForm(forms.Form):

    """ Maintains control of the nagios service / reload / restart / etc """
    #path_to_init_script = forms.CharField(help_text="Path to your nagios init script", initial=NAGIOS_INIT)
    #nagios_binary = forms.CharField(help_text="Path to your nagios binary", initial=NAGIOS_BIN)
    #command = forms.ChoiceField(choices=COMMAND_CHOICES)

    def save(self):
        #nagios_bin = self.cleaned_data['nagios_bin']
        daemon = adagios.daemon.Daemon()
        if "reload" in self.data:
            command = daemon.reload
            self.command = "reload"
        elif "restart" in self.data:
            command = daemon.restart
            self.command = "restart"
        elif "stop" in self.data:
            command = daemon.stop
            self.command = "stop"
        elif "start" in self.data:
            command = daemon.start
            self.command = "start"
        elif "status" in self.data:
            command = daemon.status
            self.command = "status"
        elif "verify" in self.data:
            command = daemon.verify_config
            self.command = "verify"
        else:
            raise Exception(_("Unknown command"))

        code = command()
        self.stdout = daemon.stdout or ""
        self.stderr = daemon.stderr or ""
        self.exit_code = code

    def verify(self):
        """ Run "nagios -v nagios.cfg" and returns errors/warning

        Returns:
        [
            {'errors': []},
            {'warnings': []}
        ]
        """
        nagios_binary = settings.nagios_binary
        nagios_config = settings.nagios_config
        command = "%s -v '%s'" % (nagios_binary, nagios_config)
        code, stdout, stderr = pynag.Utils.runCommand(command)
        self.stdout = stdout or None
        self.stderr = stderr or None
        self.exit_code = code

        for line in stdout.splitlines():
            line = line.strip()
            warnings = []
            errors = []
            if line.lower.startswith('warning:'):
                warning = {}


class SendEmailForm(forms.Form):

    """ Form used to send email to one or more contacts regarding particular services
    """
    to = forms.CharField(
        required=True,
        help_text=_("E-mail address"),
    )
    message = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'rows': 15, 'cols': 40}),
        required=False,
        help_text=_("Message that is to be sent to recipients"),
    )
    add_myself_to_cc = forms.BooleanField(
        required=False,
        help_text=_("If checked, you will be added automatically to CC")
    )
    acknowledge_all_problems = forms.BooleanField(
        required=False,
        help_text=_("If checked, also acknowledge all problems as they are sent")
    )

    def __init__(self, remote_user, *args, **kwargs):
        """ Create a new instance of SendEmailForm, contact name and email is used as from address.
        """
        self.remote_user = remote_user
        #self.contact_email = contact_email
        self.html_content = _("There is now HTML content with this message.")
        self.services = []
        self.hosts = []
        self.status_objects = []
        self._resolve_remote_user(self.remote_user)
        super(self.__class__, self).__init__(*args, **kwargs)

    def save(self):

        subject = _("%s sent you a a message through adagios") % self.remote_user

        cc_address = []
        from_address = self._resolve_remote_user(self.remote_user)
        # Check if _resolve_remote_user did in fact return an email address - avoid SMTPSenderRefused.
        import re # re built in Py1.5+
        if re.compile('([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)').search(from_address) is None:
            from_address = str(from_address) + '@no.domain'
        to_address = self.cleaned_data['to']
        to_address = to_address.split(',')
        text_content = self.cleaned_data['message']
        text_content = text_content.replace('\n','<br>')

        # self.html_content is rendered in misc.views.mail()
        html_content = smart_str(text_content) + "<p></p>" + smart_str(self.html_content)
        if self.cleaned_data['add_myself_to_cc']:
            cc_address.append(from_address)
        if self.cleaned_data['acknowledge_all_problems']:
            comment = _("Sent mail to %s") % self.cleaned_data['to']
            self.acknowledge_all_services(comment)
            self.acknowledge_all_hosts(comment)
        # Here we actually send some email:

        msg = EmailMultiAlternatives(
            subject=subject, body=text_content, from_email=from_address, cc=cc_address, to=to_address)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def acknowledge_all_hosts(self, comment):
        """ Acknowledge all problems in self.hosts
        """
        for i in self.hosts:
            host_name = i.get('host_name')
            sticky = "1"
            persistent = "0"
            notify = "0"
            author = self.remote_user

            pynag.Control.Command.acknowledge_host_problem(host_name=host_name,
                                                          sticky=sticky,
                                                          persistent=persistent,
                                                          notify=notify,
                                                          author=author,
                                                          comment=comment)
    def acknowledge_all_services(self, comment):
        """ Acknowledge all problems in self.services
        """
        for i in self.services:
            host_name = i.get('host_name')
            service_description = i.get('description')
            sticky = "1"
            persistent = "0"
            notify = "0"
            author = self.remote_user

            pynag.Control.Command.acknowledge_svc_problem(host_name=host_name,
                                                          service_description=service_description,
                                                          sticky=sticky,
                                                          persistent=persistent,
                                                          notify=notify,
                                                          author=author,
                                                          comment=comment)

    def _resolve_remote_user(self, username):
        """ Returns a valid "Full Name <email@example.com>" for remote http authenticated user.
         If Remote user is a nagios contact, then return: Contact_Alias <contact_email>"
         Else if remote user is a valid email address, return that address
         Else return None
        """
        import adagios.status.utils
        livestatus = adagios.status.utils.livestatus(request=None)
        try:
            contact = livestatus.get_contact(username)
            return "%s <%s>" % (contact.get('alias'), contact.get('email'))
        except IndexError:
            # If we get here, then remote_user does not exist as a contact.
            return username





class PasteForm(forms.Form):
    paste = forms.CharField(initial=initial_paste, widget=forms.Textarea())

    def parse(self):
        c = pynag.Parsers.config()
        self.config = c
        c.reset()
        paste = self.cleaned_data['paste']
        # Also convert raw paste into a string so we can display errors at the
        # right place:
        self.pasted_string = paste.splitlines()
        items = c.parse_string(paste)
        c.pre_object_list = items
        c._post_parse()
        all_objects = []
        for object_type, objects in c.data.items():
            model = pynag.Model.string_to_class.get(
                object_type, pynag.Model.ObjectDefinition)
            for i in objects:
                Class = pynag.Model.string_to_class.get(
                    i['meta']['object_type'])
                my_object = Class(item=i)
                all_objects.append(my_object)
        self.objects = all_objects
