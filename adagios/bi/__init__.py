# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Pall Sigurdsson <palli@opensource.is>
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

from pynag.Utils import PynagError, defaultdict

__author__ = 'palli'
import simplejson as json
import pynag.Model
import pynag.Parsers
import adagios.daemon
import adagios.pnp.functions
import adagios.settings
import time
import adagios.status.utils
from django.utils.translation import ugettext as _
import socket


class BusinessProcess(object):

    """ Wrapper class around pynag Business Processes.

     Essentially BusinessProcesses are nothing more than a grouping of nagios
     objects, and some rules on what state a whole group should have. All business
     processes have at least the following attributes:

     name           - Unique name for the process
     display_name   - Human Friendly name for the process
     processes      - Sub Processeses of this business process
    """
    process_type = 'businessprocess'
    status_calculation_methods = ['use_business_rules',
                                  'use_worst_state',
                                  'use_best_state',
                                  'always_ok',
                                  'always_minor',
                                  'always_major'
                                  ]
    _default_status_calculation_method = 'use_business_rules'
    _default_filename = '/etc/adagios/bpi.json'
    _macros = [
        'num_state_0',
        'num_state_1',
        'num_state_2',
        'num_state_3',
        'num_problems',

        'percent_state_0',
        'percent_state_1',
        'percent_state_2',
        'percent_state_3',
        'percent_problems',

        'current_state',
        'friendly_state',
    ]

    def __init__(self, name, **kwargs):
        self.data = kwargs
        self.errors = []
        self.data['name'] = name
        self._macro_cache = {}
        self._original_name = name
        if 'processes' not in self.data:
            self.data['processes'] = []

        for i in ('name', 'display_name', 'processes', 'rules', 'tags',
                  'status_method', 'graphs', 'notes',
                  'state_0', 'state_1', 'state_2', 'state_3'):
            self._add_property(i)

        # Default status messages if none are configured
        self.state_0 = self.state_0 or 'normal'
        self.state_1 = self.state_1 or 'minor problems'
        self.state_2 = self.state_2 or 'major problems'
        self.state_3 = self.state_3 or 'unknown'

        if 'rules' not in self.data:
            self.data['rules'] = []
            self.data['rules'].append(('mission critical', 1, 'major'))
            self.data['rules'].append(('not critical', 1, 'minor'))
        if not self.status_method:
            self.status_method = self._default_status_calculation_method
        self.tags = self.data.get('tags', '')

    def get_status(self):
        """ Get a status for this Business Process. How status is calculated depends on
            what self.status_method is defined as.
        """
        try:
            if self.status_method not in self.status_calculation_methods:
                self.errors.append(
                    _("Unknown state calculation method %s") % str(self.status_method))
                return 3
            elif self.status_method == 'always_ok':
                return 0
            elif self.status_method == 'always_minor':
                return 1
            elif self.status_method == 'always_major':
                return 2
            elif self.status_method == 'use_worst_state':
                return self.get_worst_state()
            elif self.status_method == 'use_best_state':
                return self.get_best_state()
            elif self.status_method == 'use_business_rules':
                return self.run_business_rules()
            else:
                self.errors.append(
                    _("We have not implemented how to use status method %s") % str(self.status_method))
                return 3
        except Exception, e:
            self.errors.append(e)
            return 3

    def get_state_summary(self):
        """ Returns a list of state statistics i.e. totals of: [ok,warn,crit,unknown]

        """
        result = [0, 0, 0, 0]
        for i in self.get_all_states():
            result[i] += 1
        return result

    def get_all_states(self):
        """ Returns a list of all subprocess states """
        return map(lambda x: x.get_status(), self.get_processes())

    def get_worst_state(self):
        """ Returns the worst state of any sub items
        """
        try:
            return int(max(self.get_all_states()))
        except Exception, e:
            self.errors.append(e)
            return 3

    def get_best_state(self):
        """ Returns the best state of any sub items
        """
        try:
            return int(min(self.get_all_states()))
        except Exception, e:
            self.errors.append(e)
            return 3

    def run_business_rules(self):
        """ Iterate through the business rules in self.data['rules'] and returns
         the calculated status
        """
        # First we create a dict tags, with all tags
        # and a list of states. It should look something like this:
        # tags['mission critical'] = [0,0,0,0]
        # tags['non critical'] = [0,0]
        #
        # Where the keys are tags, and the values are a list of statuses
        # untagged processes go in with the tag ''
        # and every processes will also go in with the tag '*'
        processes = self.get_processes()
        if not processes:
            return 3
        tags = defaultdict(list)
        for i in processes:
            i_status = i.get_status()
            i_tags = i.data.get('tags', '').split(',')
            for tag in i_tags:
                tags[tag].append(i_status)
            tags['*'].append(i_status)

        # Now we will iterate through the process rules
        # and return the status of the worst rule
        worst_status = 0
        for rule in self.rules:
            tag = rule[0]
            num_problems = rule[1]
            return_status = rule[2]

            states = tags[tag]

            # Filter out states ok
            states = filter(lambda x: x > 0, states)
            if not states:  # Nothing more to do
                continue
            if len(states) >= num_problems:
                status = self.get_computer_friendly_status(return_status)
                worst_status = max(status, worst_status)
        return worst_status

    def get_computer_friendly_status(self, value):
        """ Return an nagios-style exit code for value

         Examples:
            get_computer_friendly_status('major')
            2
            get_computer_friendly_status('critical')
            2
            get_computer_friendly_status('ok')
            0
        """
        try:
            value = int(value)
            return value
        except Exception:
            pass
        try:
            value = str(value)
            value = value.lower()
        except Exception:
            return 3

        if value in ('major', 'critical', 'crit'):
            return 2
        elif value in ('minor', 'warning', 'warn'):
            return 1
        elif value in ('ok', 'no problems'):
            return 0
        else:
            return 3

    def get_all_macros(self):
        """ Return a list of all supported macros """
        return self._macros

    def resolve_all_macros(self):
        """ Returns a dict with all macros resolved in a {'macroname:macrovalue} format """
        if not self._macro_cache:
            for macro in self.get_all_macros():
                self._macro_cache[macro] = self.resolve_macro(macro)
        return self._macro_cache

    def resolve_macrostring(self, string):
        """ Resolve all macros in a given string, and  return the resolved string

        >>> bp = get_business_process('test business process')
        >>> bp.resolve_macrostring("number of problems: {num_problems}")
        'number of problems: 0'

        For a list of supported macros, call self.resolve_all_macros()
        """
        if '{' not in string:
            return string
        all_macros = self.resolve_all_macros()
        try:
            return string.format(**all_macros)
        except KeyError, e:
            raise PynagError(_("Invalid macro in string. %s") % str(e))

    def resolve_macro(self, macroname, default='raise exception'):
        """ Returns the resolved value of a given macro.

        Arguments:
          macroname - the name of the macro, e.g. num_problems
          default   - If given, return this when macroname is not found
                      If default is not specified, exception will be
                      raised if macro could not be resolved
        """
        state_summary = self.get_state_summary()
        if macroname not in self.get_all_macros():
            if default == 'raise exception':
                raise PynagError(_("Could not resolve macro '%s'") % macroname)
            else:
                return default
        elif macroname == 'num_state_0':
            return state_summary[0]
        elif macroname == 'num_state_1':
            return state_summary[1]
        elif macroname == 'num_state_2':
            return state_summary[2]
        elif macroname == 'num_state_3':
            return state_summary[3]
        elif macroname == 'num_problems':
            return sum(state_summary[1:])
        elif macroname == 'num_problems':
            return sum(state_summary[1:])
        elif macroname == 'percent_state_0':
            if len(self.get_all_states()) == 0:
                return 0
            return 100.0 * state_summary[0] / sum(state_summary)
        elif macroname == 'percent_state_1':
            if len(self.get_all_states()) == 0:
                return 0
            return 100.0 * state_summary[1] / sum(state_summary)
        elif macroname == 'percent_state_2':
            if len(self.get_all_states()) == 0:
                return 0
            return 100.0 * state_summary[2] / sum(state_summary)
        elif macroname == 'percent_state_3':
            if len(self.get_all_states()) == 0:
                return 0
            return 100.0 * state_summary[3] / sum(state_summary)
        elif macroname == 'percent_problems':
            if len(self.get_all_states()) == 0:
                return 0
            return 100.0 * sum(state_summary[1:]) / sum(state_summary)
        elif macroname == 'current_state':
            return self.get_status()
        elif macroname == 'friendly_state':
            return self.get_human_friendly_status(resolve_macros=False)
        else:
            raise PynagError(
                _("Dont know how to resolve macro named '%s'") % macroname)

    def add_process(self, process_name, process_type=None, **kwargs):
        """ Add one business process to self.data """
        new_process = kwargs
        new_process['process_name'] = process_name
        new_process['process_type'] = process_type
        if 'processes' not in self.data:
            self.data['processes'] = []
        self.data['processes'].append(new_process)
        self._macro_cache = {}

    def remove_process(self, process_name, process_type=None):
        """ Remove one specific subprocess from this process.

            returns None
        """
        for i in self.processes:
            if i.get('process_name') != process_name:
                continue
            if i.get('process_type') != process_type:
                continue
            self.processes.remove(i)
            return

    def get_processes(self):
        """ Return a list of BusinessProcess with all sub processes in this Process
        """
        result = []
        if not self.processes:
            return result
        for i in self.processes:
            bp = get_business_process(
                i.get('process_name'), i.get('process_type'))
            # If we have specific overwrites in our local config, lets apply
            # them here
            bp.data.update(i)
            result.append(bp)
        return result

    def add_pnp_graph(self, host_name, service_description, metric_name, notes=''):
        """ Adds one graph to this business process. The graph must exist in PNP, metric_name equals pnp's ds_name
        """
        data = {}
        data['graph_type'] = "pnp"
        data['host_name'] = host_name
        data['service_description'] = service_description
        data['metric_name'] = metric_name
        data['notes'] = notes
        if not self.graphs:
            self.graphs = []
        self.graphs.append(data)

    def remove_pnp_graph(self, host_name, service_description, metric_name):
        data = {}
        data['graph_type'] = "pnp"
        data['host_name'] = host_name
        data['service_description'] = service_description
        data['metric_name'] = metric_name
        if not self.graphs:
            return
        self.graphs = filter(
            lambda x: frozenset(x) != frozenset(data), self.graphs)

    def get_pnp_last_value(self, host_name, service_description, metric_name):
        """ Looks up current nagios perfdata via mk-livestatus and returns the last value for a specific metric (str)
        """
        l = adagios.status.utils.livestatus(request=None)
        try:
            service = l.get_service(host_name, service_description)
        except Exception:
            return None
        raw_perfdata = service.get('perf_data') or ''
        perfdata = pynag.Utils.PerfData(raw_perfdata)
        for i in perfdata.metrics:
            if i.label == metric_name:
                return "%s %s" % (i.value, i.uom or '')

    def load(self):
        """ Load information about this businessprocess from file
        """
        for i in get_all_processes():
            if i.get('name') == self.name:
                self.data = i.data
            if 'processes' not in self.data:
                self.data['processes'] = []

    def save(self):
        """ Save this businessprocess to a file
        """
        json_data = get_all_json()

        # If we are renaming a process, take special
        # Precautions that we are not overwriting a current one
        if self.name != self._original_name and self.name in get_all_process_names():
            raise PynagError(
                _("Cannot rename process to %s. Another process with same name already exists") % (self.name))
        # Look for a json object that matches our name
        for i, data in enumerate(json_data):
            current_name = data.get('name', None)
            if not current_name:
                continue
            # We found our item, lets save it
            if current_name == self._original_name:
                json_data[i] = self.data
                break
        else:
            # If we get here, object was not found, so lets assume
            # We are saving a new one
            json_data.append(self.data)

        # Once we get here, all we need to do is save our item
        json_string = json.dumps(json_data, indent=4)
        self._write_file(json_string)

    def delete(self):
        """ Delete this business process
        """
        json_data = get_all_json()
        for i in json_data:
            if self.name == i.get('name'):
                json_data.remove(i)
                continue
            # Remove this process if its referenced in other processes:
            sub_processes = i.get('processes', [])
            i['processes'] = [x for x in sub_processes
                              if x['process_name'] != self.name or x['process_type'] != self.process_type]

        json_string = json.dumps(json_data, indent=4)
        self._write_file(json_string)

    def get_human_friendly_status(self, resolve_macros=True):
        state = {}
        state[0] = self.state_0
        state[1] = self.state_1
        state[2] = self.state_2
        state[3] = self.state_3
        human_friendly_state = state.get(self.get_status(), "unknown")
        if resolve_macros:
            human_friendly_state = self.resolve_macrostring(
                human_friendly_state)
        return human_friendly_state

    def _read_file(self, filename=None):
        if not filename:
            filename = self._default_filename
        return open(filename, 'r').read()

    def _write_file(self, string, filename=None):
        if not filename:
            filename = self._default_filename
        return open(filename, 'w').write(string)

    def _add_property(self, name):
        """ Create a dynamic property specific BusinessProcess

        in short:
          self.name = x -> self.data['name'] = x

        Returns: None
        """

        fget = lambda self: self.data.get(name)
        fset = lambda self, value: self.set(name, value)
        fdel = lambda self: self.set(name, None)
        fdoc = _("This is the %s attribute for object definition")
        setattr(self.__class__, name, property(fget, fset, fdel, fdoc))

    def set(self, key, value):
        """ Same as self[name] = value """
        self[key] = value

    def get(self, key, default=None):
        """ Same as dict.get """
        if key == 'get_processes':
            return self.get_processes()
        elif key == 'get_status':
            return self.get_status()
        elif key == 'status_calculation_methods':
            return self.status_calculation_methods
        elif key == 'process_type':
            return self.process_type
        elif key == 'css_hint':
            return self.css_hint()
        elif key == 'get_human_friendly_status':
            return self.get_human_friendly_status()
        return self.data.get(key, default)

    def css_hint(self):
        """ Return a bootstrap friendly hint on what css class is applicate for this object """
        css_hint = {}
        css_hint[0] = 'success'
        css_hint[1] = 'warning'
        css_hint[2] = 'danger'
        css_hint[3] = 'unknown'
        return css_hint.get(self.get_status(), "unknown")

    def __repr__(self):
        return "%s: %s" % (self.process_type, self.get('name'))

    def __str__(self):
        display_name = self.get('display_name')
        if not display_name:
            return self.__repr__()
        else:
            return display_name.encode('utf-8')

    def __getitem__(self, key):
        return self.get(key, None)

    def __setitem__(self, key, value):
        return self.data.__setitem__(key, value)


class Hostgroup(BusinessProcess):

    """ Business Process object that represents the state of one hostgroup
    """
    process_type = 'hostgroup'
    status_calculation_methods = ['worst_service_state', 'worst_host_state']
    _default_status_calculation_method = 'worst_host_state'
    subitem_methods = ['host', 'service', 'hostgroups']
    subitem_method = 'host'

    def load(self):
        self._livestatus = adagios.status.utils.livestatus(request=None)
        self._hostgroup = self._livestatus.get_hostgroup(self.name)
        self.display_name = self._hostgroup.get('alias')
        self.notes = self._hostgroup.get(
            'notes') or _("You are looking at the hostgroup %s") % (self.name)

        # Get information about child hostgroups
        self._pynag_object = pynag.Model.Hostgroup.objects.get_by_shortname(
            self.name)
        subgroups = self._pynag_object.hostgroup_members or ''
        subgroups = subgroups.split(',')

        for i in subgroups:
            if not i or i == self._hostgroup:
                continue
            self.add_process(i, self.process_type)

    def get_status(self):
        """ Same as BusinessProcess.get_status()

        status for hostgroup is defined in the following way:
         Critical if any host is down
         Critical if any service has state unknown
         Otherwise worst service state
         OK if there are no service or host problems
        """
        try:
            hostgroup = self._livestatus.get_hostgroup(self.name)
            host_status = hostgroup.get('worst_host_state')
            if host_status > 0:
                return 2

            service_status = hostgroup.get('worst_service_state')
            if service_status == 3:
                return 2
            return service_status
        except Exception, e:
            self.errors.append(e)
            return 3

    def get_processes(self):
        result = []
        if self.status_method == 'worst_host_state':
            livestatus_objects = self._hostgroup.get('members_with_state', [])
        else:
            services = self._livestatus.get_services(
                'Filter: host_groups >= %s' % self.name)
            livestatus_objects = map(
                lambda x: [x.get('host_name') + '/' + x.get(
                    'description'), x.get('state')],
                services
            )
        for i in livestatus_objects:
            process = BusinessProcess(i[0])
            process.get_status = lambda: i[1]
            result.append(process)
        return result


# TODO: Servicegroup implementation in incomplete. Test it, see if hostgroup Host and servicegroup can
# be abstracted
class Servicegroup(BusinessProcess):

    """ Business Process object that represents the state of one hostgroup """
    status_calculation_methods = ['worst_host_state']
    _default_status_calculation_method = 'worst_service_state'

    def __init__(self, name):
        self._livestatus = adagios.status.utils.livestatus(request=None)

        self._servicegroup = self._livestatus.get_servicegroup(name)
        self.servicegroup_name = name
        self.notes = self.servicegroup.get('notes')
        self._pynag_object = pynag.Model.Hostgroup.objects.get_by_shortname(
            name)
        if not self.display_name:
            self.display_name = self._servicegroup.get('alias')
        # Get information about child servicegroups
        subgroups = self._pynag_object.servicegroup_members or ''
        subgroups = subgroups.split(',')
        self.process_type = 'servicegroup'

        for i in subgroups:
            if not i:
                continue
            subprocess = Servicegroup(i)
            self.add_process(subprocess)

    def get_status(self):
        """ Same as BusinessProcess.get_status()

        status for servicegroup is defined in the following way:
         Critical if any service has state unknown
         Otherwise worst service state
         OK if there are no service or host problems
        """
        servicegroup = self._livestatus.get_servicegroup(
            self.servicegroup_name)

        service_status = servicegroup.get('worst_service_state')
        if service_status == 3:
            return 2
        return service_status


class Service(BusinessProcess):
    process_type = 'service'
    status_calculation_methods = ['service_state']
    _default_status_calculation_method = 'service_state'

    def load(self):
            tmp = self.name.split('/', 1)
            if len(tmp) != 2:
                return
            host_name = tmp[0]
            service_description = tmp[1]
            self._livestatus = adagios.status.utils.livestatus(request=None)
            self._service = self._livestatus.get_service(
                host_name, service_description)
            self.notes = self._service.get('plugin_output', '')
            self.display_name = _("service %(service)s on host %(host)s") % {'service': self._service.get('display_name', service_description),
                                                              'host': host_name}
            perfdata = pynag.Utils.PerfData(self._service.get('perf_data', ''))
            for i in perfdata.metrics:
                notes = '%s %s' % (service_description, i.label)
                self.add_pnp_graph(host_name=host_name, service_description=service_description, metric_name=i.label, notes=notes)

    def get_status(self):
        try:
            self.load()
            return self._service.get('state', 3)
        except Exception, e:
            self.errors.append(e)
            return 3


class Host(BusinessProcess):
    status_calculation_methods = ['worst_service_state', 'host_state']
    _default_status_calculation_method = 'worst_service_state'
    process_type = 'host'

    def load(self):
            self._livestatus = adagios.status.utils.livestatus(request=None)
            self._host = self._livestatus.get_host(self.name, backend=None)
            self.display_name = self._host.get('display_name') or self.name
            self.notes = self._host.get(
                'notes') or 'You are looking at the host %s' % self.name

    def get_status(self):
        try:
            self.load()
        except Exception, e:
            self.errors.append(e)
            return 3
        method = self.status_method
        if method == 'worst_service_state':
            return self._host.get('worst_service_state', 3)
        elif method == 'host_state':
            return self._host.get('state', 3)
        else:
            raise PynagError(
                _("%s is not a status calculation method i know") % method)

    def get_processes(self):
        self.load()
        livestatus_objects = self._host.get('services_with_state', [])
        result = []
        for i in livestatus_objects:
            process_name = "%s/%s" % (self.name, i[0])
            process = Service(process_name)
            process.display_name = i[0]
            #process.get_status = lambda: min(e,3)
            result.append(process)
        return result


class Domain(Host):

    """ Special class that is supposed to represent a whole domain

    Will autocreate the domain if it exists
    """
    _host = None
    _livestatus = None

    def load(self):
        self._livestatus = adagios.status.utils.livestatus(request=None)
        try:
            self._host = self._livestatus.get_host(self.name, backend=None)
        except IndexError:
            self.create_host()
            try:
                self._host = self._livestatus.get_host(self.name, backend=None)
            except IndexError:
                raise Exception(_("Failed to create host %s") % self.name)

        self.display_name = self._host.get('display_name') or self.name
        self.notes = self._host.get('notes') or 'You are looking at the host %s' % self.name
        self.graphs = []
        self._services = self._livestatus.get_services('Filter: host_name = %s' % self.name)
        for service in self._services:
            perfdata = pynag.Utils.PerfData(service.get('perf_data', ''))
            service_description = service.get('description')
            host_name = service.get('host_name')
            self.add_process('%s/%s' % (host_name, service_description), 'service')
            for i in perfdata.metrics:
                notes = '%s %s' % (service_description, i.label)
                self.add_pnp_graph(host_name=host_name, service_description=service_description, metric_name=i.label, notes=notes)

    def create_host(self):
        """ Create a new Host object in nagios config and reload nagios  """
        try:
            socket.gethostbyname(self.name)
        except Exception:
            self.host_not_found = True
            self.errors.append(_("Host not found: ") % self.name)
        all_hosts = pynag.Model.Host.objects.all
        all_hosts = map(lambda x: x.host_name, all_hosts)
        if self.name not in all_hosts:
            host = pynag.Model.Host(use="generic-domain", host_name=self.name, address=self.name)
            host.action_url = "http://%s" % self.name
            #host.hostgroups = 'domains,nameservers,mailservers,http-servers,https-servers'
            host.save()

            daemon = adagios.daemon.Daemon()

            result = daemon.reload()
            time.sleep(1)
            return result

    def reschedule_unchecked_services(self, services):
        """ Iterate through all services, if any of them have not been scheduled, schedule a check

            returns: all services after they have successfully run
        """
        now = str(int(time.now()))
        for i in services:
            if i.get('last_check') == 0:
                pynag.Control.Command.schedule_svc_check(
                    host_name=i.get('host_name'),
                    service_description=i.get('description'),
                    check_time=now,
                )

    def get_processes(self):
        self.load()
        services = self._livestatus.get_services('Filter: host_name = %s' % self.name)
        result = []
        for i in services:
            if i.get('last_check') == 0:
                i['state'] = 3
            process_name = "%s/%s" % (self.name, i.get('description'))
            process = Service(process_name)
            process.display_name = i.get('description')
            #process.get_status = lambda: min(e,3)
            result.append(process)

        return result

def get_class(process_type, default=BusinessProcess):
    """ Looks up process_type and return apropriate BusinessProcess Class

     Example:
     >>> get_class('hostgroup')
     <class '__init__.Hostgroup'>
    """
    dictionary = {}
    dictionary['hostgroup'] = Hostgroup
    dictionary['servicegroup'] = Servicegroup
    dictionary['service'] = Service
    dictionary['host'] = Host
    dictionary['process'] = BusinessProcess
    dictionary['domain'] = Domain
    return dictionary.get(process_type, default)


def get_all_json(filename=None):
    """ Return contents of a particular file after json parsing them  """
    if not filename:
        filename = BusinessProcess._default_filename
    raw_data = None
    try:
        raw_data = open(filename, 'r').read()
    except IOError, e:
        if e.errno == 2:  # File does not exist
            return []
    if not raw_data:
        return []
    json_data = json.loads(raw_data)
    return json_data


def get_all_processes(filename=None):
    """ Return all saved business processes
    """
    result = []
    try:
        json_data = get_all_json(filename=filename)
    except IOError, e:
        if e.errno == 2:
            json_data = []
        else:
            raise e
    for i in json_data:
        bp = BusinessProcess(**i)
        result.append(bp)
    return result


def get_all_process_names(filename=None):
    """ Return a list of all process names out there
    """
    return map(lambda x: x.name, get_all_processes(filename=filename))


def get_business_process(process_name, process_type=None, **kwargs):
    """ Create and load a BusinessProcess

     If process_type is not None, it indicates a special businessprocess, i.e. 'hostgroup' og 'servicegroup'

     Any kwargs specified will be added as an attrbribute that is added to the bp after it is loaded
    """
    BPClass = get_class(process_type)
    my_business_process = BPClass(process_name)
    try:
        my_business_process.load()
    except Exception, e:
        my_business_process.errors.append(e)
    my_business_process.data.update(kwargs)
    return my_business_process


class PNP4NagiosGraph:

    """ Represents one single PNP 4 nagios graph
    """

    def __init__(self, host_name, service_description, label):
        """
        """
        self.host_name = host_name
        self.service_description = service_description
        self.label = label

    def get_image_urls(self):
        json_str = adagios.pnp.functions.run_pnp(
            'json', host=self.host_name, srv=self.service_description)
        graphs = json.loads(json_str)
        # only use graphs with same label
        graphs = filter(lambda x: x['ds_name'] == self.label, graphs)
        return graphs
