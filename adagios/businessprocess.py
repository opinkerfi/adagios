from pynag.Utils import PynagError

__author__ = 'palli'
import simplejson as json
import pynag.Model
import pynag.Parsers

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
    _default_filename = '/etc/adagios/bpi.json'
    def __init__(self, name, **kwargs):
        self.data = kwargs
        self.errors = []
        self.data['name'] = name
        self._original_name = name
        if 'processes' not in self.data:
            self.data['processes'] = []

        if 'rules' not in self.data:
            self.data['rules'] = []
            self.data['rules'].append( ('mission critical',1,'major') )
            self.data['rules'].append( ('not critical',1,'minor') )

        for i in ('name', 'display_name', 'processes', 'rules'):
            self._add_property(i)
    def get_status(self):
        try:
            worst_status = -1
            processes = self.get_processes()
            if not processes:
                return 3
            for i in self.get_processes():
                if i.get('name') == self.name:
                    continue
                worst_status = max(worst_status, i.get_status())
            return worst_status
        except Exception, e:
            self.errors.append(e)
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
        for i,data in enumerate(json_data):
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
        return state.get( self.get_status(), "unknown")



    def _read_file(self, filename=None):
        if not filename:
            filename = self._default_filename
        return open(filename,'r').read()
    def _write_file(self, string, filename=None):
        if not filename:
            filename = self._default_filename
        return open(filename,'w').write(string)
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
        setattr( self.__class__, name, property(fget,fset,fdel,fdoc))
    def set(self, key, value):
        """ Same as self[name] = value """
        self[key] = value
    def get(self, key, default=None):
        """ Same as dict.get """
        if key == 'get_processes':
            return self.get_processes()
        elif key == 'get_status':
            return self.get_status()
        elif key == 'css_hint':
            return self.css_hint()
        elif key == 'get_human_friendly_status':
            return self.get_human_friendly_status()
        return self.data.get(key,default)
    def css_hint(self):
        """ Return a bootstrap friendly hint on what css class is applicate for this object """
        css_hint = {}
        css_hint[0] = 'success'
        css_hint[1] = 'warning'
        css_hint[2] = 'danger'
        css_hint[3] = 'unknown'
        return css_hint.get(self.get_status(), "unknown")
    def __repr__(self):
        return "%s: %s" % (self.process_type,self.get('name'))
    def __str__(self):
        display_name = self.get('display_name')
        if not display_name:
            return self.__repr__()
        else:
            return display_name.encode('utf-8')
    def __getitem__(self, key):
        return self.get(key, None)
    def __setitem__(self,key,value):
        return self.data.__setitem__(key, value)


class Hostgroup(BusinessProcess):
    """ Business Process object that represents the state of one hostgroup
    """
    process_type = 'hostgroup'
    def load(self):
        self._livestatus = pynag.Parsers.mk_livestatus()
        self._hostgroup = self._livestatus.get_hostgroup(self.name)
        self.display_name  = self._hostgroup.get('alias')
        self.notes = self._hostgroup.get('notes')

        # Get information about child hostgroups
        self._pynag_object = pynag.Model.Hostgroup.objects.get_by_shortname(self.name)
        subgroups = self._pynag_object.hostgroup_members or ''
        subgroups = subgroups.split(',')

        for i in subgroups:
            if not i or i == self._hostgroup:
                continue
            self.add_process( i, self.process_type )
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
    def __init__(self, name):
        self._livestatus = pynag.Parsers.mk_livestatus(nagios_cfg_file=adagios.settings.nagios_config)
        self._servicegroup = self._livestatus.get_servicegroup(name)
        self.servicegroup_name = name
        self.notes = self.servicegroup.get('notes')
        self._pynag_object = pynag.Model.Hostgroup.objects.get_by_shortname(name)
        if not display_name:
            display_name  = self._servicegroup.get('alias')
        self.display_name = display_name
        # Get information about child servicegroups
        subgroups = self._pynag_object.servicegroup_members or ''
        subgroups = subgroups.split(',')
        self.process_type = 'servicegroup'

        for i in subgroups:
            if not i:
                continue
            subprocess = Servicegroup(i)
            self.add_process( subprocess )
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


def get_class(process_type):
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
    return dictionary.get(process_type, BusinessProcess)


def get_all_json(filename=None):
    """ Return contents of a particular file after json parsing them  """
    if not filename:
        filename = BusinessProcess._default_filename
    try:
        raw_data = open(filename,'r').read()
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






import unittest



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

        self.assertEqual(b.display_name,new_display_name)
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
        b.add_process(hostgroup_name,'hostgroup')
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



