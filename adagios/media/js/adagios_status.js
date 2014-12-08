
window.adagios = window.adagios || {};
adagios.status = adagios.status || {};
adagios.objectbrowser = adagios.objectbrowser || {};
adagios.misc = adagios.misc || {};
adagios.bi = adagios.bi || {};

adagios.misc.__notification_id_counter = 0;

// When saved search items are added to the left sidebar, this is what they look like:
adagios.misc._saved_search_element = '<li><div><a  href="URL">NAME</a><button type="button" class="pull-right close" onclick=\'adagios.misc.delete_saved_search("NAME");\'>&times;</button></div></li>';


$(document).ready(function() {

    // Create good default behaviour for bootstrap tabs
    adagios.misc.init_tab_selection();

    // Disable all links that have the class 'disabled'
    adagios.status.make_disabled_links_unclickable();

    // Put keyboard focus on the search box
    adagios.status.enable_search_box();

    // Configure what happens when user clicks a selectable row or checkbox
    adagios.status.enable_clickable_rows();

    // Enable/disable toolbar and action buttons
    adagios.status.count_selected_objects();

    // Flash a warning if nagios needs a reload
    adagios.objectbrowser.check_nagios_needs_reload();

    // If there are any notifications from server, display them
    adagios.misc.get_server_notifications();

    // change all table with class datatable into datatables
    adagios.misc.turn_tables_into_datatables();

    // Multiselect checkboxes at the top-left of status-tables
    adagios.status.initilize_multiselect_checkboxes();

    // Input boxes with the class pynag-autocomplete get select2 autocomplete magic.
    adagios.objectbrowser.autocomplete_for_multichoicefields();

    // Fix console logging for internet explorer
    adagios.misc.internet_explorer_console_fix();

    // Make search dialog option match current query:
    adagios.misc.populate_search_with_querystring_fields($('#search_dialog'));

    // Populate all the fields in saved_search_modal.
    adagios.misc.prepare_saved_search_modal($('#saved_searches_header'));

    // If we have any saved searches, show them in the side menu:
    adagios.misc.populate_saved_searches_sidemenu();

    // Handle user contributed ssi overwrites
    adagios.misc.ssi_overwrites();

    // Handle user contributed ssi overwrites
    adagios.misc.modal_resize();

});



adagios.status.service_detail_update_servicestate_icon = function(host_name, params) {
    var results = {results: []};

    adagios.rest.status.services({
       'host_name': host_name, 
       'fields': 'acknowledged description state last_check host_state scheduled_downtime_depth acknowledged'
    }).done( function(data) {
        var name, item, i;
        var host_services = $("div#host_services");
        for (i in data) {
            var service = data[i];
            var div = {};
            var circle_div = host_services.find("a").filter(function(i) {
                return $(this).text().trim() === service.description;
            }).find("div");
            if (service.last_check != 0) {
                circle_div.removeClass("state_pending");
                circle_div.addClass("state_" + service.state);
                if (service['host_state'] === 0 && service['scheduled_downtime_depth'] === 0 && service['acknowledged'] === 0) {
                    circle_div.addClass("unhandled");
                }
            }
        }
    });
};


adagios.objectbrowser.CheckCommandEditor = function(parameters) {
    var p = parameters || {};
    var self = {};
    self.host_name = p.host_name || $('#check_command_editor_host_name').text();
    self.service_description = p.service_description || $('#check_command_editor_service_description').text();
    self.name = p.name || $('#check_command_editor_service_name').text();
    self.check_command = p.check_command || $('#check_command_editor_check_command').text();
    self.working_div_id = "#check_command_editor";

    // Create the dom structure we need for this script to run
    self.create_dom = function(destination_div) {
        destination_div = destination_div || self.working_div_id;
        var html = '' +
            '<table class="" >' +
            '  <tbody id="check_command_argument_table"></tbody>' +
            '  <tbody id="service_macros_table"></tbody>' +
            '  <tbody id="other_attributes_table"></tbody>' +
            '</table>' +
            '<pre id="command_line_preview">Loading...</pre>' +
            '<pre  id="original_command_line"></pre>' +
            '';
        $(destination_div).html(html);
    };

    // Go through all the relevant input values, and return respective macros
    self.get_all_attributes = function() {
        var my_data = {};
        my_data.host_name = self.host_name;
        my_data.name = self.name;
        my_data.service_description = self.service_description;
        my_data.check_command = self.check_command;
        $(".check_command_parameter").each( function() {
            var item = $(this)[0];
            my_data[item.name] = item.value;
        });
        return my_data;
    };

    // Find the selected attributes, and read through all arguments,
    // and concat it in one field that looks like this:
    // check_command!$ARG1$!$ARG2$
    self.update_check_command_entry = function() {
        var all_attributes =self.get_all_attributes();
        var check_command = all_attributes.check_command || '';
        for (var i in all_attributes) {
            if (i.substring(0,4) == '$ARG') {
               check_command = check_command + '!' + all_attributes[i];
            }
        }
        if (self.check_command == '') {
            check_command = '';
        }
        $('#check_command_actual_entry').attr('value', check_command);
    };

    // This function will look up what macros are related to our check_command
    // and then create correct input boxes for each one.
    self.generate_input_fields = function() {
        var my_data = {
            'host_name': self.host_name,
            'service_description': self.service_description,
            'check_command': self.check_command,
            'name': self.name
        };
        var check_command_editor_location = $('#check_command_editor_tables')

        check_command_editor_location.hide();

        if (my_data.check_command == null || my_data.check_command == '')
        {
            return;
        }
        if (my_data.host_name == null || my_data.host_name == '') {
            console.error("No host_name specified. Not generating any input fields");
            $('#check_command_editor_tables').hide();
            return;
        }

        check_command_editor_location.show();

        adagios.rest.pynag.check_command(my_data)
            .done( function(data) {
                // Generate a table, where each row has an input field with
                // a macroname for us
                var service_macros_input_fields = '';
                var check_command_arguments_input_fields = '';
                var other_input_fields = '';
                var input_field_value;
                var friendly_name;
                var edit_field;
                for (var i in data) {
                    // Create a human friendly label for our attribute
                    friendly_name = i.replace('$_SERVICE','');
                    friendly_name = friendly_name.replace('$ARG','Argument ');
                    friendly_name = friendly_name.split('_').join(' ').split('$').join('');
                    // Fix double quotes in input fields
                    if (data[i] == null) {
                        input_field_value = '';
                    }
                    else {
                        input_field_value = data[i].split('"').join('&quot;');
                    }

                    // Create an edit field for this attribute
                    edit_field = '' +
                        '<tr><td>' + friendly_name + '</td>' +

                        '<td><input class="check_command_parameter";" type="text" class="span11" name="' + i + '" value="' + input_field_value + '">' +
                        '</td></tr>'
                    ;
                    /* Alternative implementation
                     '<div class="control-group">' +
                     '    <label class="control-label" >' +
                     '    ' + friendly_name +
                     '    </label>' +
                     '    <div class="controls">' +
                     '<input class="check_command_parameter";" type="text" class="span11" name="' + i + '" value="' + data[i] + '">' +
                     '    </div>' +
                     '</div>' +
                     '';
                     */
                    if (i.substring(0,9) == '$_SERVICE') {
                        service_macros_input_fields += edit_field;
                    }
                    else if (i.substring(0,4) == '$ARG') {
                        check_command_arguments_input_fields += edit_field ;
                    }
                    else if (i[0] == '$') {
                        other_input_fields += edit_field;
                    }
                    else if (i == "original_command_line") {
                        $('#original_command_line').html( data[i] );
                    }
                }


                $('#service_macros_table').html(service_macros_input_fields);
                $('#other_attributes_table').html(other_input_fields);
                $('#check_command_argument_table').html(check_command_arguments_input_fields);


                // The other input fields are not related to our specific service, and no need
                // To make them editable
                $('#other_attributes_table input').prop('disabled', true);

                // Preview the command line
                self.original_command_line = data.original_command_line;
                self.decorate_original_command_line();
                self.display_effective_command_line();

                // Our newly generated fields will get a keyup event so preview is updated when
                // field is changed.
                $('.check_command_parameter').keyup( function() {
                    self.decorate_original_command_line();
                    self.display_effective_command_line();
                    self.update_check_command_entry();
                });
                self.update_check_command_entry();
            })
            .fail( function(data) {
                self.error(data);
            });
    };

    // Lets resolve all macros and put the result in #command_line_preview
    self.display_effective_command_line = function() {
        var macros = self.get_all_attributes();
        var macronames = self.original_command_line.match(/\$.*?\$/g);
        var effective_command_line = self.original_command_line;

        effective_command_line = self.resolve_macros(effective_command_line, macros, true);
        $('#command_line_preview').text( effective_command_line );

    };

    // Returns input_string with all macros defined in macros replaced
    // If recursive=true, recursively resolve all macros starting with $ARG
    // Example:
    // input_string = "$USER1$/check_ping -H $HOSTNAME$"
    // macros = {'$USER1$':'/bin', '$HOSTNAME$':'localhost'}
    // resolve_macros(input_string, macros);
    //
    //
    self.resolve_macros = function(input_string, macros, recursive) {
        var macronames = input_string.match(/\$.*?\$/g);
        var macrovalue;
        for (var macroname in macros) {
            macrovalue = macros[macroname];
            if (macrovalue === undefined) {
                macrovalue = '';
            }

            if (recursive == true && macroname.search("ARG") == 1)
            {
                macrovalue = self.resolve_macros(macrovalue, macros, false);
            }

            input_string = input_string.replace(macroname, macrovalue);
        }
        return input_string;
    };

    // We have a div that contains the original command-line with all its macros.
    // Lets modify it so all macros are highlighted.
    // If it so happens that decorated command line is the same as effective one
    // Then we will hide this dialog
    self.decorate_original_command_line = function() {
        var macroname, macrovalue;
        var data = self.get_all_attributes();

        var macronames = self.original_command_line.match(/\$.*?\$/g);
        var decorated_command_line =  self.original_command_line;

        var new_str;
        for (var i in macronames) {
            macroname = macronames[i];
            macrovalue = data[macroname];
            if (macroname.search('ARG') == 1) {
                macrovalue = self.resolve_macros(macrovalue, data);
            }
            macrovalue = macrovalue || '';
            new_str = "<a "
                + "class='macro_in_a_text' title='"
                + macrovalue
                + "'>"
                + macroname
                + "</a>";
            decorated_command_line = decorated_command_line.replace(macroname,new_str);
        }
        $('#original_command_line').html( decorated_command_line );
    };

    // Read through all inputs in #input_fields and then save the current service
    // This function reloads the current page on success
    self.save_check_command = function() {
        var my_data = self.get_all_attributes();

        adagios.rest.status.update_check_command(my_data)
            .done( function(data) {
                location.reload();
            })
            .fail( function(data) {
                self.error('Failed to run save_check_command()');
            });
        $('#check_command_save_button').button('loading');


    };

    self.error = function(message) {
        message = message || 'no error message provided';
        console.error('error: ' + message);
    };

    self.debug = function(message) {
        self.debug = self.debug || false;
        if (self.debug) {
            console.log("debug: " + message);
        }
    };

    return self;
};


/**
 * Returns array of pynag objects that match search query
 * @param object_type - Object type to look for
 * @param query - part of the objects shortname
 *
 * This function can be used directly with select2 like this:
 * <input type="hidden" id="add_hostgroups" style="width: 500px" />
 * <script>
 * $("#add_hostgroups").select2({
 *  minimumInputLength: 0,
 *  query: function(query) { select2_query("hostgroup", query); }
 * });
 * </script>
 *
 */
adagios.objectbrowser.select2_objects_query = function(object_type, query) {
    var results = {results: []};

    var params = {
        object_type: object_type,
        name__contains:query.term
    };

    adagios.rest.status.get(params)
        .done( function(data) {
            var name, item, i;
            for (i in data) {
                if (object_type == 'service') {
                    name = data[i].host_name + "/" + data[i].description;
                }
                else {
                    name = data[i].name;
                }
                item  = {id: name, text: name};
                results.results.push(item);
            }
            query.callback(results);

        })
};


adagios.objectbrowser.select2_business_process = function(query) {
    var results = {results: []};

    var params = {};

    adagios.rest.status.get_business_process_names(params)
        .done( function(data) {
            var name, item, i;
            for (i in data) {
                name = data[i];
                item  = {id: name, text: name};
                results.results.push(item);
            }
            query.callback(results);

        })
};

adagios.objectbrowser.check_nagios_needs_reload = function() {
    adagios.rest.pynag.needs_reload()
        .done(function(data) {
            if (data === true) {
                $("#nagios_needs_reload_button").show();
                adagios.misc.warning("Configs have changed. You need to reload for changes to take effect.", 'nagios_reload')
            }

        });
};

// Reload nagios and display a nice status message on top of screen
adagios.misc.reload_nagios = function() {
    $("#nagios_is_reloading").show();
    adagios.rest.pynag.reload_nagios()
        .done(function(data) {
            if (data['status'] == "success") {
                $("#nagios_needs_reload_button").hide();
                adagios.misc.success("Nagios Successfully reloaded", 'nagios_reload', 5000);
            }
            else {
                var message = data['message'];
                message += ' <a href="URLmisc/service">details</a>';
                message = message.replace("URL", BASE_URL);
                adagios.misc.error(message, 'nagios_reload');

            }
        })
        .fail(function(data) {
                var message = data['message'];
                message += ' <a href="URL">Go to Nagios Service page</a>';
                message = message.replace("URL", BASE_URL);
                adagios.misc.error(message, 'nagios_reload');
        })
        .always(function(data) {
            $('#nagios_is_reloading').hide();
        });
};

// Get all serverside notifications and display them to our user.
adagios.misc.get_server_notifications = function() {
    var message_div = $("#error_messages");
    adagios.rest.adagios.get_notifications()
        .done(function(data) {
            var timeout, i;
            for (var k=0; k < data.length; k=k+1) {
                i = data[k];
                if (i['notification_type'] == 'show_once') {
                    timeout = 5000;
                }
                else {
                    timeout = undefined;
                }
                adagios.misc.add_notification(i['message'], i['level'], i['notification_id'], timeout);
            }

        });
};

// Display a notification in element "#error_messages"
adagios.misc.add_notification = function(message, level, notification_id, timeout) {
    var notification = $("#typical_notification").html();
    var message_div = $("#error_messages");
    if (notification_id === undefined) {
        adagios.misc.__notification_id_counter += 1;
        notification_id = adagios.misc.__notification_id_counter;
    }
    notification_id = "notification_" + notification_id;

    // If notification with same ID already exists. Remove the old one.
    $("#" + notification_id).remove();

    if (timeout > 0) {
        var div_id = notification_id + "-close";
        setTimeout(function() { $("#" + div_id).click(); }, timeout);
    }
    var html = notification
        .replace(/MESSAGE/g, message)
        .replace(/NOTIFICATION_ID/g, notification_id)
        .replace(/LEVEL/g, level);
    return message_div.html(message_div.html() + html);
};

// Display an info message in #error_messages div
adagios.misc.info = function(message, notification_id, timeout) {
    return adagios.misc.add_notification(message, 'info', notification_id, timeout);
};

// Display an info message in #error_messages div
adagios.misc.warning = function(message, notification_id, timeout) {
    return adagios.misc.add_notification(message, 'warning', notification_id, timeout);
};

// Display an info message in #error_messages div
adagios.misc.success = function(message, notification_id, timeout) {
    return adagios.misc.add_notification(message, 'success', notification_id, timeout);
};

// Display an info message in #error_messages div
adagios.misc.error = function(message, notification_id, timeout) {
    return adagios.misc.add_notification(message, 'danger', notification_id, timeout);
};

// Initilize all bootstrap tabs, so that
// By default it is possible to link to a specific tab
// Also show first tab by default.
adagios.misc.init_tab_selection = function() {

    var tabs = $('ul.nav.nav-tabs');
    var anchor = document.location.href.split('#')[1] || '';
    anchor = anchor.split('_tab')[0];
    var current_tab = tabs.find('a[href="#' + anchor + '"]');
    if (current_tab.length === 0) {
        current_tab = tabs.find('a[data-toggle=tab]:first');
    }
    current_tab.tab('show');

    $('a[data-toggle="tab"]').on('shown', function (e) {
        var id = $(e.target).attr('href').split("_tab")[0];
        document.location.hash = id + "_tab";
    });

};

// Puts keyboard focus on search box, and enables live filtering of
// objects in the status table.
adagios.status.enable_search_box = function() {
    var searchbox = $('#search_field');
    searchbox.focus();

    // When someone is typing in the searchbox, make sure searchtable is updated
    var $rows;
    searchbox.keyup(function() {
        if ($rows === undefined) {
            $rows = $('.searchtable tbody .mainrow');
        }

        var val = $.trim($(this).val()).replace(/ +/g, ' ').toLowerCase();
        $rows.show().filter(function() {
            var text = $(this).text().replace(/\s+/g, ' ').toLowerCase();

            return !~text.indexOf(val);
        }).hide();

        // Some views like status view hide repeated occurances of host_names
        // That does not work well if something is being filtered
        if (val == '')
            $('.repeated_content').hide();
        else
            $('.repeated_content').show();
    });

};

// When row in datatable is clicked. Select it.
adagios.status.enable_clickable_rows = function() {
    var _last_selected = 0;
    var rows = $( ".mainrow" );
    var all_checkboxes = $(".chkbox", rows);
    rows.click(function(e) {
        var checkbox = $(':checkbox', this);
        var index = rows.index(this);

        // If we clicked something else than a link or the checkbox,
        // Trigger an actual click on the checkbox
        if (e.target.type !== 'checkbox' && e.target.tagName != 'A') {
                checkbox.prop('checked', ! checkbox.prop('checked'));
        }


        // If shift is down while clicking a row, we select (or unselect)
        // Everything from last row we clicked til here
        if ( e.shiftKey && index != _last_selected ) {

            all_checkboxes
                    .slice(Math.min( _last_selected, index ), Math.max( _last_selected, index )+1 )
                    .each(function(i, e) {
                        this.checked = checkbox.prop('checked') || false;
                        adagios.status.update_row_color($(this));
                    });
        }
        else {

        }
        adagios.status.update_row_color(checkbox);
        checkbox.focus();
        _last_selected = index;
        adagios.status.count_selected_objects();
    });
};

// Given a checkbox, update the color of the selected row
adagios.status.update_row_color = function(checkbox) {
            if (checkbox.prop('checked') == true) {
                checkbox.parent().parent().addClass('row_selected');
            }
            else {
                checkbox.parent().parent().removeClass('row_selected');
            }
};

// Return a list of all objects that have been checked and have the selectable class. This is used for
// Acknowledge, downtime, etc.
adagios.status.get_selected_objects = function() {
    var result = [];
    var primary = $( ".chkbox-primary:checked " );
    var checked_boxes = $( ".selectable :checked:visible" );

    if (checked_boxes.length == 0) {
        checked_boxes = primary;
    }
    checked_boxes.each(function() {
        result.push($(this).data());
    });
    return result;

};

// Links that have the class 'disabled' should not be clickable by default
adagios.status.make_disabled_links_unclickable = function() {
    // Disable a links as well as buttons using the disabled class since disabling links is not
    // supported by default.
    jQuery.fn.extend({
            disable: function(state) {
            return this.each(function() {
                    var $this = $(this);
                    $this.toggleClass('disabled', state);
            });
            }
    });
        // Disable clicking on disabled links
        $('body').on('click', 'a.disabled', function(event) {
            event.preventDefault();
        });
};



// adagios.status.count_selected_objects()
// Enables or disabled the action_buttons and toolbar buttons depending on if
// Any objects are selected or not
adagios.status.count_selected_objects = function() {

    var selected_objects = adagios.status.get_selected_objects();

    // Treat acknowledge button depending on if acknowledgements are needed
    if (selected_objects.length > 0) {
        $('#action_buttons button.adagios_service_multi').attr('disabled', null);
        if (selected_objects.length > 1) {
            $('#action_buttons button.adagios_service_single').attr('disabled', 'disabled');
        } else {
            $('#action_buttons button.adagios_service_single').attr('disabled', null);
        }
        $('.enable_on_select').attr('disabled', null);
        $('#action_buttons').attr('title',null);
        $('#action_buttons_more a').disable(false);
    }
    else {
        $('#action_buttons button').attr('disabled', 'disabled');
        $('.enable_on_select').attr('disabled', 'disabled');
        $('#action_buttons_more a').disable(true);
    }
};


// When a user clicks the remove acknowledgement button, this is called
// to remove acknowledgements of all "selected" objects
adagios.status.remove_acknowledgements = function() {
    var selected_objects = adagios.status.get_selected_objects();
    var args;
    var objects_done = 0;
    $.each(selected_objects, function(i, item) {
        args = {};
        args['host_name'] = item['host_name'];
        args['service_description'] = item['service_description'];
        adagios.rest.status.remove_acknowledgement(args)
                .done(function() {
                    objects_done += 1;
                    if (objects_done == selected_objects.length) {
                        location.reload();
                    }
            })
    });
};

// When a user clicks the remove downtimes button, this is called
// to remove downtimes of all "selected" objects
adagios.status.remove_active_downtimes = function() {
    var selected_objects = adagios.status.get_selected_objects();
    var args;
    var objects_done = 0;
    $.each(selected_objects, function(i, item) {
        args = {};
        args['host_name'] = item['host_name'];
        args['service_description'] = item['service_description'];
        args['downtime_id'] = item['downtime_id'];
        adagios.rest.status.remove_downtime(args)
                .done(function() {
                    objects_done += 1;
                    if (objects_done == selected_objects.length) {
                        location.reload();
                    }
                })
    });
};


// Clear all checked checkboxes
adagios.status.clear_all_selections = function() {
       $('.chkbox').each( function(data) {
           this.checked = false;
           adagios.status.update_row_color($(this));
           });
        $('.select_many').each( function(data) {
           this.checked = false;
           });
        $('.chkbox-primary').each( function(data) {
            this.checked = true;
        });
        adagios.status.count_selected_objects();
};

// This event is fired when one or more objects have been rescheduled
adagios.status.reschedule = function() {
    var selected_objects = adagios.status.get_selected_objects();
    var objects_done = 0;
    var total = selected_objects.length;
    var hostlist = '';
    var servicelist = '';
    var host_name, service_description, object_type;
    $.each(selected_objects, function(i, item) {
        host_name =  item['host_name'];
        service_description = item['service_description'] || '';
        object_type = item['object_type'];
        if (object_type == 'host') {
            hostlist = hostlist + ';' + host_name;
        }
        else if (object_type == 'service') {
            servicelist = servicelist + ';' + host_name + ',' + service_description;
        }
    });

    var parameters = {};
    parameters['hostlist'] = hostlist;
    parameters['servicelist'] = servicelist;

    adagios.misc.info("Rescheduling " + selected_objects.length + " items", "reschedule_status");
    adagios.rest.status.reschedule_many(parameters)
        .done(function(data) {
            adagios.misc.success("Reschedule request for " + selected_objects.length + " items has been sent. You should refresh your browser.", "reschedule_status", 5000);
            adagios.status.clear_all_selections();
        })
        .fail(function(data) {
           adagios.misc.error("Error while rescheduling checks. Error output printed in javascript console.", "reschedule_status");
           console.error(data.responseText);
        });

};


// Change all tables with the class "datatable" into a datatable
adagios.misc.turn_tables_into_datatables = function() {
    var oTable = $('.datatable').dataTable( {
        "bPaginate": true,
        "iDisplayLength": 100,
        "sPaginationType": "bootstrap"
    });
    $('.dataTables_length').hide();

};


// All checkboxes with the "select_many" class have a multiselect
// kind of feature.
adagios.status.initilize_multiselect_checkboxes = function() {
    var select_many_boxes = $('.select_many');
    $('.select_all').click(function(e) {
        $( ".chkbox").each( function() {
            this.checked = true;
            adagios.status.update_row_color($(this));
        });
        select_many_boxes.prop('checked',true);
        select_many_boxes.prop('indeterminate',false);
        adagios.status.count_selected_objects();
    });
    $('.select_none').click(function(e) {
        $( ".chkbox").each( function() {
            this.checked = false;
            adagios.status.update_row_color($(this));
        });
        select_many_boxes.prop('checked',false);
        select_many_boxes.prop('indeterminate',false);
        adagios.status.count_selected_objects();
    });
    $('.select_problems').click(function(e) {
        $( "input.problem ").each( function() {
            this.checked = true;
            adagios.status.update_row_color($(this));
        });
        select_many_boxes.prop('checked',false);
        select_many_boxes.prop('indeterminate',true);
        adagios.status.count_selected_objects();
    });
    $('.select_unhandled_problems').click(function(e) {
        $( "input.unhandled ").each( function() {
            this.checked = true;
            adagios.status.update_row_color($(this));
        });
        select_many_boxes.prop('checked',false);
        select_many_boxes.prop('indeterminate',true);
        adagios.status.count_selected_objects();
    });

};

// Handle SSI (serverside includes) overwrites.
// We will look for objects with class ssi-append or ssi-overwrite and rewrite html accordingly.
//
// Example: this tag: <div class="ssi-overwrite" data-for="#top_navigation_bar" would overwrite
// The markup inside #top_navigation_bar
adagios.misc.ssi_overwrites = function() {
    $(".ssi-overwrite").each(function(data) {
        var dest_selector = $(this).data('for');
        var destination = $(dest_selector);
        destination.html($(this).html());
    });

    $(".ssi-append").each(function(data) {
        var dest_selector = $(this).data('for');
        var destination = $(dest_selector);
        destination.html(destination.html() + $(this).html());
    });


};

// Function to edit a single attribute of an object
adagios.status.change_attribute = function(object_type,short_name,attribute_name,new_value, success, error) {
    var my_data  = {
        "object_type": object_type,
        "short_name": short_name,
        "attribute_name":attribute_name,
        "new_value":new_value
    };
    return adagios.rest.status.edit(my_data)
            .done(function(data) {
                adagios.objectbrowser.check_nagios_needs_reload();
            })
            .fail(function(data) {
                adagios.misc.error("Error saving data.")
            });
    };

adagios.misc.internet_explorer_console_fix = function() {
// Avoid `console` errors in browsers that lack a console.
(function() {
    var method;
    var noop = function () {};
    var methods = [
        'assert', 'clear', 'count', 'debug', 'dir', 'dirxml', 'error',
        'exception', 'group', 'groupCollapsed', 'groupEnd', 'info', 'log',
        'markTimeline', 'profile', 'profileEnd', 'table', 'time', 'timeEnd',
        'timeStamp', 'trace', 'warn'
    ];
    var length = methods.length;
    var console = (window.console = window.console || {});

    while (length--) {
        method = methods[length];

        // Only stub undefined methods.
        if (!console[method]) {
            console[method] = noop;
        }
    }
}());

};

// Given a specific background task id, monitor its status
// And display output on regular intervals.
adagios.misc.subscribe_to_task = function() {
    adagios.rest.adagios.list_tasks()
        .done(function(data) {
           var first_task = data[0]['task_id'];
            adagios.rest.adagios.get_task({'task_id': first_task})
                .done(function(data) {
                   adagios.misc.info(data['task_status'], "task_" + data['task_id']);

                });
        });

};

// Some javascript hacks to log the current user out of basic auth
adagios.misc.logout = function() {
    (function(safeLocation){
        var outcome, u, m = "You should be logged out now.";
        // IE has a simple solution for it - API:
        try { outcome = document.execCommand("ClearAuthenticationCache") }catch(e){}
        // Other browsers need a larger solution - AJAX call with special user name - 'logout'.
        if (!outcome) {
            // Let's create an xmlhttp object
            outcome = (function(x){
                if (x) {
                    // the reason we use "random" value for password is
                    // that browsers cache requests. changing
                    // password effectively behaves like cache-busing.
                    x.open("HEAD", safeLocation || location.href, true, "logout", (new Date()).getTime().toString())
                    x.send("")
                    // x.abort()
                    return 1 // this is **speculative** "We are done."
                } else {
                    return
                }
            })(window.XMLHttpRequest ? new window.XMLHttpRequest() : ( window.ActiveXObject ? new ActiveXObject("Microsoft.XMLHTTP") : u ))
        }
        if (!outcome) {
            m = "Your browser is too old or too weird to support log out functionality. Close all windows and restart the browser."
        }
        console.log(m);
        // return !!outcome
    })(/*if present URI does not return 200 OK for GET, set some other 200 OK location here*/)

};

// Resize modals to relative size to window
adagios.misc.modal_resize = function() {
    $('div.modal').on('show', function() {
        $(this).find('div.modal-body').css({'max-height': ($( window ).height() * 0.7)+"px" });
        $(this).find('div.modal-body').css({'max-width': ($( window ).width() * 0.9)+"px" });
    });
};

// Delete a single host or service comment
adagios.status.delete_comment = function(object_type, comment_id) {
    var parameters = {};
    parameters['comment_id'] = comment_id;
    //parameters['is_service'] = (object_type == 'host');
    return adagios.rest.status.delete_comment(parameters);
};

// Delete a single host or service downtime
adagios.status.delete_downtime = function(object_type, downtime_id) {
    var parameters = {};
    parameters['downtime_id'] = downtime_id;
    parameters['is_service'] = (object_type == 'host');
    return adagios.rest.status.delete_downtime(parameters);
};


// Reload current page in X seconds. (1000 = 1 second). Will not reload if user is
// Interacting with the page. Any value < 0.01 will be ignored.
adagios.misc.timed_reload = function(seconds) {
    var milliseconds = seconds * 1000;
    if (!seconds || milliseconds < 100) {
        return;
    }
    var reload_function = function() { console.log("reloading..."); window.location.reload(); };
    var reload = setInterval(reload_function, milliseconds);
    var reload_has_been_canceled;
    $( ".selectable").change(function(data) {
        if (!reload_has_been_canceled) {
            console.log("checkbox was changed. Canceling reload");
            clearInterval(reload);
        }

    });
    $("div .modal").on('shown', function(data) {
        if (!reload_has_been_canceled) {
            console.log("Canceling reload because of modal shown");
            clearInterval(reload);
        }
    });
    $("#search_field").keyup( function(data) {
       if (!reload_has_been_canceled) {
            console.log("Canceling reload because search_field was modified");
            clearInterval(reload);
        }
    });
};

// Find all fields with the class pynag-autocomplete and turn them into proper select2 fields
adagios.objectbrowser.autocomplete_for_multichoicefields = function() {
    $("input.pynag-autocomplete").each(function() {
        var choices = $(this).data()["choices"] || '';
	    choices = choices.split(',');
	    $(this).select2({tags:choices});
    });
};

// Returns a list of all querystring keys and values in current web page
adagios.misc.get_querystring_list = function() {
    var querystring = window.location.search.substr(1).split('&');
    var key, value, current_querystring_item;
    var result = [];
    for (var i = 0; i < querystring.length; ++i) {
        current_querystring_item = querystring[i].split('=');
        key = current_querystring_item[0];
        value = current_querystring_item[1];
        result.push([key, value]);
    }
    return result;
};

// Reads current querystring and makes sure that when search dialog
// is opened, it will match was was put in querystring.
adagios.misc.populate_search_with_querystring_fields = function(dom) {
    var querystring_list = adagios.misc.get_querystring_list();
    var key, value, check_box_selector;
    for (var i = 0; i < querystring_list.length; ++i) {
        key = querystring_list[i][0];
        value = querystring_list[i][1];
        if (key == 'q') {
            dom.find('#id_search_modal_q').val(value);
            continue;
        }
        // If we find a checkbox with same name and value, make sure it is checked:
        check_box_selector = 'input[name="KEY"][value="VALUE"]';
        check_box_selector = check_box_selector.replace('KEY', key).replace('VALUE', value);
        dom.find(check_box_selector).prop('checked', true);
    }
};


// Prep work for saved_search modal
adagios.misc.prepare_saved_search_modal = function() {
    var save_search_modal = $("#save_search_modal");
    var save_search_form = save_search_modal.find('#save_search_form');

    save_search_modal.on('shown', function () {
        document.getElementById('id_save_search_name').focus();
    });

    save_search_form.submit(function(e) {
        var parameters = {
            'name': $('#save_search_form').find('#id_save_search_name').val(),
            'url': window.location.href
        };

        adagios.rest.adagios.save_search(parameters).always(function() {
            $('#save_search_modal').modal('hide');
            adagios.misc.populate_saved_searches_sidemenu();
        });
        e.preventDefault();
        return false
    });
};

// Add to the left side menu all saved searches for a given user:
adagios.misc.populate_saved_searches_sidemenu = function(dom) {
    dom = dom || $('#saved_searches_header');
    var child_dom = $("#saved_searches_list");
    var search_name, search_url, html;
    child_dom.empty();
    adagios.rest.adagios.get_saved_searches().done( function(data) {
        for (search_name in data) {
            if (data.hasOwnProperty(search_name)) {
                search_url = data[search_name];
                html = adagios.misc._saved_search_element.replace(/URL/g, search_url).replace(/NAME/g, search_name);
                child_dom.append(html);
            }
        }
    });
};

// Removes a single item from saved search menu.
adagios.misc.delete_saved_search = function(name) {
    adagios.rest.adagios.delete_saved_search({'name': name}).done(function() {
        window.location.reload();
    });
};