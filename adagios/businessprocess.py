from pynag.Utils import PynagError, defaultdict

__author__ = 'palli'
import simplejson as json
import pynag.Model
import pynag.Parsers
import unittest


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
    status_calculation_methods = ['use_business_rules', 'use_worst_state', 'use_best_state', 'always_ok', 'always_minor', 'always_major']
    _default_status_calculation_method = 'use_business_rules'
    _default_filename = '/etc/adagios/bpi.json'

    def __init__(self, name, **kwargs):
        self.data = kwargs
        self.errors = []
        self.data['name'] = name
        self._original_name = name
        if 'processes' not in self.data:
            self.data['processes'] = []

        for i in ('name', 'display_name', 'processes', 'rules', 'tags', 'status_method', 'graphs'):
            self._add_property(i)

        if 'rules' not in self.data:
            self.data['rules'] = []
            self.data['rules'].append(('mission critical', 1, 'major'))
            self.data['rules'].append(('not critical', 1, 'minor'))
            rule1 = {'tag': 'mission critical', 'return_status': 'major', 'min_number_of_problems': 1, }
        if not self.status_method:
            self.status_method = self._default_status_calculation_method
        self.tags = self.data.get('tags', '')

    def get_status(self):
        """ Get a status for this Business Process. How status is calculated depends on
            what self.status_method is defined as.
        """
        try:
            if self.status_method not in self.status_calculation_methods:
                self.errors.append("Unknown state calculation method %s" % str(self.status_method))
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
                self.errors.append("We have not implemented how to use status method %s" % str(self.status_method))
                return 3
        except Exception, e:
            self.errors.append(e)
            return 3

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
        tags = defaultdict(list)
        for i in self.get_processes():
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
            if len(states) > num_problems:
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

    def add_process(self, process_name, process_type=None, **kwargs):
        """ Add one business process to self.data """
        new_process = kwargs
        new_process['process_name'] = process_name
        new_process['process_type'] = process_type
        if 'processes' not in self.data:
            self.data['processes'] = []
        self.data['processes'].append(new_process)

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
            bp = get_business_process(i.get('process_name'), i.get('process_type'))
            # If we have specific overwrites in our local config, lets apply them here
            bp.data.update(i)
            result.append(bp)
        return result

    def add_pnp_graph(self, host_name, service_description, metric_name, notes=''):
        """ Adds one graph to this business process. The graph must exist in pnp4nagios, metric_name equals pnp's ds_name
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
        self.graphs = filter(lambda x: frozenset(x) != frozenset(data), self.graphs)

    def get_pnp_last_value(self, host_name, service_description, metric_name):
        """ Looks up current nagios perfdata via mk-livestatus and returns the last value for a specific metric (str)
        """
        l = pynag.Parsers.mk_livestatus()
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
            raise PynagError("Can not rename process to %s. Another process with that name already exists" % (self.name))
        # Look for a json object that matches our name
        for i, data in enumerate(json_data):
            current_name = data.get('name', None)
            if not current_name:
                continue
            if current_name == self._original_name:  # We found our item, lets save it
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
        json_string = json.dumps(json_data, indent=4)
        self._write_file(json_string)

    def get_human_friendly_status(self):
        state = {}
        state[0] = "ok"
        state[1] = "warning"
        state[2] = "critical"
        return state.get(self.get_status(), "unknown")

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
        fdoc = "This is the %s attribute for object definition"
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
    _default_status_calculation_method = 'worst_service_state'

    def load(self):
        self._livestatus = pynag.Parsers.mk_livestatus()
        self._hostgroup = self._livestatus.get_hostgroup(self.name)
        self.display_name = self._hostgroup.get('alias')
        self.notes = self._hostgroup.get('notes')

        # Get information about child hostgroups
        self._pynag_object = pynag.Model.Hostgroup.objects.get_by_shortname(self.name)
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


class Servicegroup(BusinessProcess):
    """ Business Process object that represents the state of one hostgroup """
    status_calculation_methods = ['worst_host_state']
    _default_status_calculation_method = 'worst_service_state'

    def __init__(self, name):
        self._livestatus = pynag.Parsers.mk_livestatus(nagios_cfg_file=adagios.settings.nagios_config)
        self._servicegroup = self._livestatus.get_servicegroup(name)
        self.servicegroup_name = name
        self.notes = self.servicegroup.get('notes')
        self._pynag_object = pynag.Model.Hostgroup.objects.get_by_shortname(name)
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
            subprocess = Servicegroup(i)
            self.add_process(subprocess)

    def get_status(self):
        """ Same as BusinessProcess.get_status()

        status for servicegroup is defined in the following way:
         Critical if any service has state unknown
         Otherwise worst service state
         OK if there are no service or host problems
        """
        servicegroup = self._livestatus.get_servicegroup(self.servicegroup_name)

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
            self._livestatus = pynag.Parsers.mk_livestatus()
            self._service = self._livestatus.get_service(host_name, service_description)

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
        try:
            self._livestatus = pynag.Parsers.mk_livestatus()
            self._host = self._livestatus.get_host(host_name)
        except Exception, e:
            self.errors.append(e)

    def get_status(self):
        try:
            self.load()
        except Exception, e:
            self.errors.append(e)
            return 3
        return self._host.get('state', 3)


def get_class(process_type, default=BusinessProcess):
    """ Looks up process_type and return apropriate BusinessProcess Class

     Example:
     >>> get_class('hostgroup')
     Hostgroup
    """
    dictionary = {}
    dictionary['hostgroup'] = Hostgroup
    dictionary['servicegroup'] = Servicegroup
    dictionary['service'] = Service
    dictionary['host'] = Host
    dictionary['process'] = BusinessProcess
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
        import adagios.pnp.functions
        import adagios.settings
        import simplejson as json
        json_str = adagios.pnp.functions.run_pnp('json', host=self.host_name, srv=self.service_description)
        graphs = json.loads(json_str)
        # only use graphs with same label
        graphs = filter(lambda x: x['ds_name'] == self.label, graphs)
        return graphs


class TestGraphs(unittest.TestCase):
    def testPNP4NagiosGraph_get_image_url(self):

        pnp = PNP4NagiosGraph('apc01.acme.com', 'Ping', 'rta')
        pnp.get_image_url()


class TestBusinessProcess(unittest.TestCase):
    def test_save_and_load(self):
        """ This test will test load/save of a business process.

         The procedure is as follows:
         * Load a business process
         * Save it
         * Make changes
         * Load it again, and verify changes were saved.
        """
        bp_name = 'test_business_process'

        b = BusinessProcess(bp_name)
        b.load()

        # Append a dot to the bp name and save
        new_display_name = b.display_name or '' + "."
        b.display_name = new_display_name
        b.save()

        # Load bp again
        b = BusinessProcess(bp_name)
        b.load()

        self.assertEqual(b.display_name, new_display_name)

    def test_add_process(self):
        """ Test adding new processes to a current BP
        """
        bp_name = 'test'
        sub_process_name = 'sub_process'
        sub_process_display_name = 'This is a subprocess of test'
        b = BusinessProcess(bp_name)
        b.add_process(sub_process_name, display_name=sub_process_display_name)
        for i in b.get_processes():
            if i.name == sub_process_name and i.display_name == sub_process_display_name:
                return
        else:
            self.assertTrue(False, 'We tried adding a business process but could not find it afterwards')

    def test_hostgroup_bp(self):
        bp_name = 'test'
        hostgroup_name = 'acme-network'
        b = BusinessProcess(bp_name)
        b.add_process(hostgroup_name, 'hostgroup')

    def test_remove_process(self):
        """ Test removing a subprocess from a businessprocess
        """
        bp_name = 'test'
        sub_process_name = 'sub_process'
        sub_process_display_name = 'This is a subprocess of test'
        b = BusinessProcess(bp_name)
        b.add_process(sub_process_name, display_name=sub_process_display_name)
        self.assertNotEqual([], b.processes)
        b.remove_process(sub_process_name)
        self.assertEqual([], b.processes)

    def test_get_all_processes(self):
        get_all_processes()


if __name__ == '__main__':
    tmp = get_all_processes()
    for i in tmp:
        print i.name
        print i.run_business_rules()
