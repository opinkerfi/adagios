
import simplejson
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from adagios.pnp.functions import run_pnp
from adagios.views import adagios_decorator

import adagios.bi
import adagios.bi.forms

from adagios.views import adagios_decorator, error_page


@adagios_decorator
def edit(request, process_name, process_type):
    """ Edit one specific business process
    """

    messages = []
    bp = adagios.bi.get_business_process(process_name)
    errors = bp.errors or []
    status = bp.get_status()
    add_subprocess_form = adagios.bi.forms.AddSubProcess(instance=bp)
    form = adagios.bi.forms.BusinessProcessForm(instance=bp, initial=bp.data)
    add_graph_form = adagios.bi.forms.AddGraphForm(instance=bp)
    if request.method == 'GET':
        form = adagios.bi.forms.BusinessProcessForm(
            instance=bp, initial=bp.data)
    elif request.method == 'POST':
        if 'save_process' in request.POST:
            form = adagios.bi.forms.BusinessProcessForm(
                instance=bp, data=request.POST)
            if form.is_valid():
                form.save()
        elif 'remove_process' in request.POST:
            removeform = adagios.bi.forms.RemoveSubProcessForm(
                instance=bp, data=request.POST)
            if removeform.is_valid():
                removeform.save()
        elif 'add_process' in request.POST:
            if form.is_valid():
                form.add_process()
        elif 'add_graph_submit_button' in request.POST:
            add_graph_form = adagios.bi.forms.AddGraphForm(
                instance=bp, data=request.POST)
            if add_graph_form.is_valid():
                add_graph_form.save()
        elif 'add_subprocess_submit_button' in request.POST:
            add_subprocess_form = adagios.bi.forms.AddSubProcess(
                instance=bp, data=request.POST)
            if add_subprocess_form.is_valid():
                add_subprocess_form.save()

            else:
                errors.append("failed to add subprocess")
                add_subprocess_failed = True
        else:
            errors.append(
                "I don't know what submit button was clicked. please file a bug.")

        # Load the process again, since any of the above probably made changes
        # to it.
        bp = adagios.bi.get_business_process(process_name)

    return render_to_response('business_process_edit.html', locals(), context_instance=RequestContext(request))


@adagios_decorator
def add_graph(request):
    """ Add one or more graph to a single business process
    """
    c = {}
    c['errors'] = []
    c.update(csrf(request))
    if request.method == 'GET':
        source = request.GET
    else:
        source = request.POST
    name = source.get('name', None)
    if name:
        c['name'] = name
    bp = adagios.bi.get_business_process(name)
    c['graphs'] = []
    # Convert every graph= in the querystring into
    # host_name,service_description,metric attribute
    graphs = source.getlist('graph')
    for graph in graphs:
        tmp = graph.split(',')
        if len(tmp) != 3:
            c['errors'].append("Invalid graph string: %s" % (tmp))
        graph_dict = {}
        graph_dict['host_name'] = tmp[0]
        graph_dict['service_description'] = tmp[1]
        graph_dict['metric_name'] = tmp[2]
        graph_dict['notes'] = tmp[2]
        c['graphs'].append(graph_dict)

    #
    # When we get here, we have parsed all the data from the client, if
    # its a post, lets add the graphs to our business process
    if request.method == 'POST':
        if not name:
            raise Exception(
                "Booh! you need to supply name= to the querystring")
        for graph in c['graphs']:
            form = adagios.bi.forms.AddGraphForm(instance=bp, data=graph)
            if form.is_valid():
                form.save()
            else:
                e = form.errors
                raise e
        return redirect('adagios.bi.views.edit', bp.process_type, bp.name)

    return render_to_response('business_process_add_graph.html', c, context_instance=RequestContext(request))


@adagios_decorator
def view(request, process_name, process_type=None):
    """ View one specific business process
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    bp = adagios.bi.get_business_process(
        process_name, process_type=process_type)
    graphs_url = reverse(
        'adagios.bi.views.graphs_json', kwargs={"process_type":process_type, "process_name": process_name})
    c['bp'] = bp
    c['graphs_url'] = graphs_url
    return render_to_response('business_process_view.html', c, context_instance=RequestContext(request))


@adagios_decorator
def json(request, process_name=None, process_type=None):
    """ Returns a list of all processes in json format.

    If process_name is specified, return all sub processes.
    """
    if not process_name:
        processes = adagios.bi.get_all_processes()
    else:
        process = adagios.bi.get_business_process(process_name, process_type)
        processes = process.get_processes()
    result = []
    # Turn processes into nice json
    for i in processes:
        json = {}
        json['state'] = i.get_status()
        json['name'] = i.name
        json['display_name'] = i.display_name
        result.append(json)
    json = simplejson.dumps(result)
    return HttpResponse(json, content_type="application/json")

@adagios_decorator
def graphs_json(request, process_name, process_type):
    """ Get graphs for one specific business process
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    import adagios.businessprocess
    bp = adagios.bi.get_business_process(process_name=process_name, process_type=process_type)

    graphs = []
    if not bp.graphs:
        return HttpResponse('[]')
    for graph in bp.graphs or []:
        if graph.get('graph_type') == 'pnp':
            host_name = graph.get('host_name')
            service_description = graph.get('service_description')
            metric_name = graph.get('metric_name')
            pnp_result = run_pnp('json', host=graph.get(
                'host_name'), srv=graph.get('service_description'))
            json_data = simplejson.loads(pnp_result)
            for i in json_data:
                if i.get('ds_name') == graph.get('metric_name'):
                    notes = graph.get('notes')
                    last_value = bp.get_pnp_last_value(
                        host_name, service_description, metric_name)
                    i['last_value'] = last_value
                    i['notes'] = notes
                    graphs.append(i)
    graph_json = simplejson.dumps(graphs)
    return HttpResponse(graph_json)


@adagios_decorator
def add_subprocess(request):
    """ Add subitems to one specific businessprocess
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    c.update(csrf(request))
    process_list, parameters = _business_process_parse_querystring(request)

    if request.method == 'POST':
        if 'name' not in request.POST:
            raise Exception(
                "You must specify which subprocess to add all these objects to")
        parameters.pop('name')
        bp = adagios.bi.get_business_process(request.POST.get('name'))
        # Find all subprocesses in the post, can for each one call add_process
        # with all parmas as well
        for i in process_list:
            process_name = i.get('name')
            process_type = i.get('process_type')
            bp.add_process(process_name, process_type, **parameters)
            c['messages'].append('%s: %s added to %s' %
                                 (process_type, process_name, bp.name))
        bp.save()
        return redirect('adagios.bi.views.edit', bp.process_type, bp.name)
    c['subprocesses'] = process_list
    c['parameters'] = parameters
    return render_to_response('business_process_add_subprocess.html', c, context_instance=RequestContext(request))


@adagios_decorator
def add(request):
    """ View one specific business process
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    import adagios.businessprocess
    bp = adagios.bi.BusinessProcess("New Business Process")
    if request.method == 'GET':
        form = adagios.bi.forms.BusinessProcessForm(
            instance=bp, initial=bp.data)
    elif request.method == 'POST':
        form = adagios.bi.forms.BusinessProcessForm(
            instance=bp, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('adagios.bi.views.edit', bp.process_type, bp.name)
    return render_to_response('business_process_edit.html', locals(), context_instance=RequestContext(request))


@adagios_decorator
def index(request):
    """ List all configured business processes
    """
    c = {}
    c['messages'] = []
    c['errors'] = []
    processes = adagios.bi.get_all_processes()
    return render_to_response('business_process_list.html', locals(), context_instance=RequestContext(request))


@adagios_decorator
def delete(request, process_name, process_type):
    """ Delete one specific business process """
    import adagios.businessprocess
    bp = adagios.bi.get_business_process(process_name=process_name, process_type=process_type)
    if request.method == 'POST':
        form = adagios.bi.forms.BusinessProcessForm(
            instance=bp, data=request.POST)
        form.delete()
        return redirect('adagios.bi.views.index')

    return render_to_response('business_process_delete.html', locals(), context_instance=RequestContext(request))


@adagios_decorator
def change_status_calculation_method(request, process_name):
    import adagios.businessprocess
    bp = adagios.bi.get_business_process(process_name)
    if request.method == 'POST':
        for i in bp.status_calculation_methods:
            if i in request.POST:
                bp.status_method = i
                bp.save()
        return redirect('adagios.bi.views.index')


def _business_process_parse_querystring(request):
    """ Parses querystring into process_list and parameters

    Returns:
      (parameters,processs_list) where:
         -- process_list is a list of all business processes that were mentioned in the querystring
         -- Parameters is a dict of all other querystrings that were not in process_list and not in exclude list
    """
    ignored_querystring_parameters = ("csrfmiddlewaretoken")
    import adagios.businessprocess
    data = {}
    if request.method == 'GET':
        data = request.GET
    elif request.method == 'POST':
        data = request.POST
    else:
        raise Exception("Booh, use either get or POST")
    parameters = {}
    process_list = []
    for key in data:
        for value in data.getlist(key):
            if key in ignored_querystring_parameters:
                continue
            type_of_process = adagios.bi.get_class(key, None)

            if type_of_process is None:
                parameters[key] = value
            else:
                process_type = type_of_process.process_type
                process = adagios.bi.get_business_process(
                    value, process_type=process_type)
                process_list.append(process)
    return process_list, parameters
