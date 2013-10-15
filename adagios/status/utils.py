# -*- coding: utf-8 -*-
#
# Utility functions for the status app. These are mostly used by
# adagios.status.views

import pynag.Utils
import pynag.Parsers
import adagios.settings
import simplejson as json

from collections import defaultdict

state = defaultdict(lambda: "unknown")
state[0] = "ok"
state[1] = "warning"
state[2] = "critical"


def livestatus(request):
    """ Returns a new pynag.Parsers.mk_livestatus() object with authauser automatically set from request.META['remoteuser']
    """

    if adagios.settings.enable_authorization == True:
        authuser = request.META.get('REMOTE_USER', None)
    else:
        authuser = None
    livestatus = pynag.Parsers.mk_livestatus(
        nagios_cfg_file=adagios.settings.nagios_config, authuser=authuser)
    return livestatus


def query(request, *args, **kwargs):
    """ Wrapper around pynag.Parsers.mk_livestatus().query(). Any authorization logic should be performed here. """
    l = livestatus(request)
    return l.query(*args, **kwargs)


def get_hosts(request, tags=None, fields=None, *args, **kwargs):
    """ Get a list of hosts from mk_livestatus

     This is a wrapper around pynag.Parsers.mk_livestatus().query()

     Arguments:
        request  - Not in use
        tags     - Not in use
        fields   - If fields=None, return all columns, otherwise return only the columns provided

        Any *args will be passed directly to livestatus
        Any **kwargs will be converted to livestatus "'Filter:' style strings

     Returns:
        A list of dict (hosts)
    """
    if 'q' in kwargs:
        q = kwargs.get('q')
        del kwargs['q']
        if not isinstance(q, list):
            q = [q]
    else:
        q = []

    # If keyword "unhandled" is in kwargs, then we will fetch unhandled
    # services only
    if 'unhandled' in kwargs:
        del kwargs['unhandled']
        kwargs['state__isnot'] = 0
        kwargs['acknowledged'] = 0
        kwargs['scheduled_downtime_depth'] = 0
        #kwargs['host_scheduled_downtime_depth'] = 0
        #kwargs['host_acknowledged'] = 0

    arguments = pynag.Utils.grep_to_livestatus(*args, **kwargs)
    # if "q" came in from the querystring, lets filter on host_name
    for i in q:
        arguments.append('Filter: name ~~ %s' % i)
        arguments.append('Filter: address ~~ %s' % i)
        arguments.append('Filter: plugin_output ~~ %s' % i)
        arguments.append('Or: 3')
    print fields
    if fields is None:
        fields = [
            'name', 'plugin_output', 'last_check', 'state', 'services', 'services_with_info', 'services_with_state',
            'address', 'last_state_change', 'acknowledged', 'downtimes', 'comments_with_info',
            'num_services_crit', 'num_services_warn', 'num_services_unknown', 'num_services_ok', 'num_services_pending']
    # fields should be a list, lets create a Column: query for livestatus
    if isinstance(fields, (str, unicode)):
        fields = fields.split(',')
    if len(fields) > 0:
        argument = 'Columns: %s' % (' '.join(fields))
        arguments.append(argument)
    l = livestatus(request)
    result = l.get_hosts(*arguments)

    # Add statistics to every hosts:
    for host in result:
        try:
            host['num_problems'] = host['num_services_crit'] + \
                host['num_services_warn'] + host['num_services_unknown']
            host['children'] = host['services_with_state']

            if host.get('last_state_change') == 0:
                host['state'] = 3
            host['status'] = state[host['state']]

            ok = host.get('num_services_ok')
            warn = host.get('num_services_warn')
            crit = host.get('num_services_crit')
            pending = host.get('num_services_pending')
            unknown = host.get('num_services_unknown')
            total = ok + warn + crit + pending + unknown
            host['total'] = total
            host['problems'] = warn + crit + unknown
            try:
                total = float(total)
                host['health'] = float(ok) / total * 100.0
                host['percent_ok'] = ok / total * 100
                host['percent_warn'] = warn / total * 100
                host['percent_crit'] = crit / total * 100
                host['percent_unknown'] = unknown / total * 100
                host['percent_pending'] = pending / total * 100
            except ZeroDivisionError:
                host['health'] = 'n/a'
        except Exception:
            host['num_problems'] = 'n/a'
            pass

    # Sort by host and service status
    result.sort(reverse=True, cmp=lambda a, b:
                cmp(a['num_problems'], b['num_problems']))
    result.sort(reverse=True, cmp=lambda a, b: cmp(a['state'], b['state']))
    return result


def get_services(request=None, tags=None, fields=None, *args, **kwargs):
    """ Get a list of services from mk_livestatus.

        This is a wrapper around pynag.Parsers.mk_livestatus().query()

        Arguments:
            requests - Not in use
            tags     - List of 'tags' that will be passed on as a filter to the services.
                       Example of service tags are: problem, unhandled, ishandled,
            fields   - If fields=None, return all columns, otherwise return only the columns provided.
                       fields can be either a list or a comma seperated string
        Any *args will be passed directly to livestatus

        Any **kwargs passed in will be converted to livestatus 'Filter:' strings

        Examples:
        get_services(host_name='localhost') # same as livestatus.query('GET services','Filter: host_name = localhost')

        get_services('Authuser: admin', host_name='localhost')

    """
    if 'q' in kwargs:
        q = kwargs.get('q')
        del kwargs['q']
    else:
        q = []
    if not isinstance(q, list):
        q = [q]

    # If keyword "unhandled" is in kwargs, then we will fetch unhandled
    # services only
    if 'unhandled' in kwargs:
        del kwargs['unhandled']
        kwargs['state__isnot'] = 0
        kwargs['acknowledged'] = 0
        kwargs['scheduled_downtime_depth'] = 0
        kwargs['host_scheduled_downtime_depth'] = 0
        kwargs['host_acknowledged'] = 0
    arguments = pynag.Utils.grep_to_livestatus(*args, **kwargs)

    # If q was added, it is a fuzzy filter on services
    for i in q:
        arguments.append('Filter: host_name ~~ %s' % i)
        arguments.append('Filter: description ~~ %s' % i)
        arguments.append('Filter: plugin_output ~~ %s' % i)
        arguments.append('Filter: host_address ~~ %s' % i)
        arguments.append('Or: 4')

    if fields is None:
        fields = [
            'host_name', 'description', 'plugin_output', 'last_check', 'host_state', 'state',
            'last_state_change', 'acknowledged', 'downtimes', 'host_downtimes', 'comments_with_info']
    # fields should be a list, lets create a Column: query for livestatus
    if isinstance(fields, (str, unicode)):
        fields = fields.split(',')
    if len(fields) > 0:
        argument = 'Columns: %s' % (' '.join(fields))
        arguments.append(argument)
    l = livestatus(request)
    result = l.get_services(*arguments)

    # Add custom tags to our service list
    try:
        for service in result:
            # Tag the service with tags such as problems and unhandled
            service_tags = []
            if service['state'] != 0:
                service_tags.append('problem')
                service_tags.append('problems')
                if service['acknowledged'] == 0 and service['downtimes'] == [] and service['host_downtimes'] == []:
                    service_tags.append('unhandled')
                    service['unhandled'] = "unhandled"
                else:
                    service_tags.append('ishandled')
                    service['handled'] = "handled"
            elif service.get('last_state_change') == 0:
                service['state'] = 3
                service_tags.append('pending')
            else:
                service_tags.append('ok')
            if service['acknowledged'] == 1:
                service_tags.append('acknowledged')
            if service['downtimes'] != []:
                service_tags.append('downtime')
            service['tags'] = ' '.join(service_tags)
            service['status'] = state[service['state']]

        if isinstance(tags, str):
            tags = [tags]
        if isinstance(tags, list):
            result = pynag.Utils.grep(result, tags__contains=tags)
    except Exception, e:
        pass
    return result


def get_statistics(request):
    """ Return a list of dict. That contains various statistics from mk_livestatus (like service totals and host totals)
    """
    c = {}
    l = livestatus(request)
    # Get host/service totals as an array of [ok,warn,crit,unknown]
    c['service_totals'] = l.query('GET services', 'Stats: state = 0',
                                  'Stats: state = 1', 'Stats: state = 2', 'Stats: state = 3', columns=False)
    c['host_totals'] = l.query(
        'GET hosts', 'Stats: state = 0', 'Stats: state = 1', 'Stats: state = 2', columns=False)

    # Get total number of host/services
    c['total_hosts'] = sum(c['host_totals'])
    c['total_host_problems'] = c['total_hosts'] - c['host_totals'][0]

    c['total_services'] = sum(c['service_totals'])
    c['total_service_problems'] = c['total_services'] - c['service_totals'][0]
    # Calculate percentage of hosts/services that are "ok"
    try:
        c['service_totals_percent'] = map(
            lambda x: float(100.0 * x / c['total_services']), c['service_totals'])
    except ZeroDivisionError:
        c['service_totals_percent'] = [0, 0, 0, 0]
    try:
        c['host_totals_percent'] = map(
            lambda x: float(100.0 * x / c['total_hosts']), c['host_totals'])
    except ZeroDivisionError:
        c['host_totals_percent'] = [0, 0, 0, 0]

    c['unhandled_services'] = l.query('GET services',
                                      'Filter: acknowledged = 0',
                                      'Filter: scheduled_downtime_depth = 0',
                                      'Filter: host_state = 0',
                                      'Stats: state > 0',
                                      columns=False
                                      )[0]
    c['unhandled_hosts'] = l.query('GET hosts',
                                   'Filter: acknowledged = 0',
                                   'Filter: scheduled_downtime_depth = 0',
                                   'Stats: state > 0',
                                   columns=False,
                                   )[0]
    c['total_unhandled_network_problems'] = l.query('GET hosts',
                                                    'Filter: acknowledged = 0',
                                                    'Filter: scheduled_downtime_depth = 0',
                                                    'Filter: childs != ',
                                                    'Stats: state > 0',
                                                    columns=False
                                                    )[0]
    tmp = l.query('GET hosts',
                  'Filter: childs != ',
                  'Stats: state >= 0',
                  'Stats: state > 0',
                  columns=False
                  )
    c['total_network_parents'], c['total_network_problems'] = tmp
    return c


class BusinessProcess(object):

    """ Business Process Object
    """
    _default_filename = "/etc/adagios/bpi.json"

    def __init__(self):
        self.data = {}
        attributes = ('process_type', 'notes', 'display_name', 'name')
        for i in attributes:
            self._add_property(i)

        self.process_type = None
        self.processes = []
        self.notes = None
        self.name = None
        self.display_name = None

    def _add_property(self, name):
        """ Create a dynamic property specific BusinessProcess

        in short:
          self.name = x -> self.data['name'] = x

        Returns: None
        """

        fget = lambda self: self.data.get(name)
        fset = lambda self, value: self.set(name, value)
        fdel = lambda self: self.set(name, None)
        fdoc = "This is the %s attribute for object definition"
        setattr(self.__class__, name, property(fget, fset, fdel, fdoc))

    def set(self, key, value):
        """ Same as self[name] = value """
        self[key] = value

    def get_status(self):
        """ Returns nagios-style exit code that represent the state of this whole group """
        status = -1
        for i in self.processes:
            status = max(status, i.get_status())
        return status

    def __repr__(self):
        return "Business Process %s" % (self.display_name or self.name)

    def add_process(self, business_process):
        if not self.processes:
            self.processes = [business_process]
        else:
            self.processes.append(business_process)

    def css_hint(self):
        """ Return a bootstrap friendly hint on what css class is applicate for this object """
        css_hint = {}
        css_hint[0] = 'success'
        css_hint[1] = 'warning'
        css_hint[2] = 'danger'
        css_hint[3] = 'unknown'
        return css_hint.get(self.get_status(), "unknown")

    def get_human_friendly_status(self):
        state = {}
        state[0] = "ok"
        state[1] = "warning"
        state[2] = "critical"
        return state.get(self.get_status(), "unknown")

    def __getitem__(self, key):
        return self.data.get(key, None)

    def __setitem__(self, key, value):
        return self.data.__setitem__(key, value)


class HostgroupBP(BusinessProcess):

    """ Business Process object that represents the state of one hostgroup """

    def __init__(self, name, display_name=None):
        super(self.__class__, self).__init__()
        self._livestatus = pynag.Parsers.mk_livestatus(
            nagios_cfg_file=adagios.settings.nagios_config)
        self._hostgroup = self._livestatus.get_hostgroup(name)
        self.name = name
        if not display_name:
            display_name = self._hostgroup.get('alias')
        self.display_name = display_name
        self.notes = self._hostgroup.get('notes')
        self._pynag_object = pynag.Model.Hostgroup.objects.get_by_shortname(
            name)
        self.process_type = 'hostgroup'
        # Get information about child hostgroups
        subgroups = self._pynag_object.hostgroup_members or ''
        subgroups = subgroups.split(',')

        for i in subgroups:
            if not i or i == self._hostgroup:
                continue
            subprocess = HostgroupBP(i)
            self.add_process(subprocess)

    def get_status(self):
        """ Same as BusinessProcess.get_status()

        status for hostgroup is defined in the following way:
         Critical if any host is down
         Critical if any service has state unknown
         Otherwise worst service state
         OK if there are no service or host problems
        """
        hostgroup = self._livestatus.get_hostgroup(self.hostgroup_name)
        host_status = hostgroup.get('worst_host_state')
        if host_status > 0:
            return 2

        service_status = hostgroup.get('worst_service_state')
        if service_status == 3:
            return 2
        return service_status


class ServicegroupBP(BusinessProcess):

    """ Business Process object that represents the state of one hostgroup """

    def __init__(self, name):
        self._livestatus = pynag.Parsers.mk_livestatus(
            nagios_cfg_file=adagios.settings.nagios_config)
        self._servicegroup = self._livestatus.get_servicegroup(name)
        self.servicegroup_name = name
        self.notes = self.servicegroup.get('notes')
        self._pynag_object = pynag.Model.Hostgroup.objects.get_by_shortname(
            name)
        if not display_name:
            display_name = self._servicegroup.get('alias')
        self.display_name = display_name
        # Get information about child servicegroups
        subgroups = self._pynag_object.servicegroup_members or ''
        subgroups = subgroups.split(',')
        self.process_type = 'servicegroup'

        for i in subgroups:
            if not i:
                continue
            subprocess = ServicegroupBP(i)
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


class ServiceBP(BusinessProcess):

    """ BusinessProcess around one single service
    """
    process_type = 'service'

    def __init__(self, host_name, service_description):
        self._livestatus = pynag.Parsers.mk_livestatus(
            nagios_cfg_file=adagios.settings.nagios_config)
        self._service = self._livestatus.get_service(
            host_name, service_description)

    def get_status(self):
        return self._service.get('state', 3)


class CustomBP(BusinessProcess):

    """ Custom Business Process. Usually a wrapper around other types of Business Processes """
    critical_processes = []
    noncritical_processes = []
    critical_threshold = 0
    noncritical_threshold = 0

    process_type = 'custom'

    def _get_all_json(self, filename=None):
        """ Get all business processes from a specific file
        """
        result = []
        if filename is None:
            filename = self._default_filename
        try:
            raw_data = open(filename).read()
        except IOError:
            return result
        try:
            all_json_data = json.loads(raw_data) or []
        except Exception:
            return result
        result = all_json_data
        return result

    def all(self):
        """ Returns a list of All custom Business Processes """
        all_json = self._get_all_json()
        result = []
        for i in all_json:
            name = i.get('name', None)
            if not name:
                continue
            c = CustomBP(name)
            c.data = i
            result.append(c)
        return result

    def load(self, filename=None):
        if not filename:
            filename = self._default_filename
        all_json = self._get_all_json(filename=filename)
        for i in all_json:
            name = i.get('name', None)
            if not name:
                continue
            if name == self.name:
                self.data = i
                self.processes = []
                for subprocess in self.data.get('processes', []):
                    bp = get_business_process(
                        subprocess['process_type'], subprocess['process_name'])
                    self.processes.append(bp)
                return
        raise Exception(
            "Could not load a BusinessProcess with name: %s" % self.name)

    def save(self, filename=None):
        """ Saves this business process in a json format  to file
        """
        if not filename:
            filename = self._default_filename
        all_json = self._get_all_json(filename=filename)
        index = None
        data = self.data.copy()
        for i, item in enumerate(all_json):
            if item.get('name') == self.name:
                index = i
                break
        if index is None:
            all_json.append(data)
        else:
            all_json[index] = data
        json_string = json.dumps(all_json, indent=4)
        open(filename, 'w').write(json_string)

    def __init__(self, name):
        super(CustomBP, self).__init__()
        self.name = name
        self.process_type = "custom"

    def add_process(self, business_process, critical=True):
        """ Add another business process into this group """
        if not self.processes:
            self.processes = []
        self.processes.append(business_process)
        tmp = {}
        tmp['process_name'] = business_process.name
        tmp['process_type'] = business_process.process_type
        if 'processes' not in self.data:
            self.data['processes'] = []
        self.data['processes'].append(tmp)
        if critical == True:
            self.critical_processes.append(business_process)
        else:
            self.noncritical_processes.append(business_process)

    def get_status(self):
        worst_status = 0
        criticals = 0
        noncriticals = 0
        for i in self.processes:
            i_status = i.get_status()
            worst_status = max(worst_status, i_status)
            if i_status > 0:
                if i in self.critical_processes:
                    criticals += 1
                elif i in self.noncritical_processes:
                    noncriticals += 1
        if criticals > self.critical_threshold:
            return 2
        if noncriticals > self.noncritical_threshold:
            return 2
        return worst_status


def get_business_process(process_type, name):
    """ Returns a BusinessProcess instance """
    if process_type == 'hostgroup':
        return HostgroupBP(name)
    elif process_type == 'servicegroup':
        return HostgroupBP(name)
    elif process_type == 'custom':
        c = CustomBP(name)
        try:
            c.load()
        except Exception:
            pass
        return c
    else:
        raise Exception("Business process of type %s not found" % process_type)
