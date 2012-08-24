/*
 Allow radio inputs as button in regular form
 http://dan.doezema.com/2012/03/twitter-bootstrap-radio-button-form-inputs/

 This stops regular posting for buttons and assigns values to a hidden input
 to enable buttons as a radio.
 */
jQuery(function($) {
    $('div.btn-group[data-toggle-name="*"]').each(function(){
        var group   = $(this);
        var form    = group.parents('form').eq(0);
        var name    = group.attr('data-toggle-name');
        var hidden  = $('input[name="' + name + '"]', form);
        $('button', group).each(function(){
            var button = $(this);
            button.live('click', function(){
                hidden.val($(this).val());
            });
            if(button.val() == hidden.val()) {
                button.addClass('active');
            }
        });
    });
});


$.extend( $.fn.dataTableExt.oStdClasses, {
    "sSortAsc": "header headerSortDown",
    "sSortDesc": "header headerSortUp",
    "sSortable": "header"
} );



(function( $ ) {
    var obIgnoreTables = [
        $('table#service')[0], $('table#contact')[0],$('table#host')[0], $('table#command')[0], $('table#timeperiod')[0]
    ];
    $.fn.dataTableExt.afnFiltering.push(
        function( oSettings, aData, iDataIndex ) {
            // Disable filter for all tables except obIgnoreTables
            if ( $.inArray( oSettings.nTable, obIgnoreTables ) == -1 )
                    {
                        return true;
                    }
            // Default we show nothing
            var filter = false;
            var filter_object = $('div#' + oSettings['sTableId'] + ' a[href="#filter_object"]').hasClass('btn-primary');
            var filter_template = $('div#' + oSettings['sTableId'] + ' a[href="#filter_template"]').hasClass('btn-primary');
            var filter_group = $('div#' + oSettings['sTableId'] + ' a[href="#filter_group"]').hasClass('btn-primary');
            // We are showing templates and this is register=0
            if (filter_template && aData[0] == '0') {
                return true;
            }
            // We are not showing templates and this is register=0
            if (!filter_template && aData[0] == '0') {
                return false;
            }
            // We are filtering on object
            if (filter_object && aData[1] == oSettings.sTableId) {
                return true;
            }
            // We are filtering on groups
            if (filter_group && aData[1] == oSettings.sTableId + 'group') {
                return true;
            }
            // default no
            return false;
        }
    );
    /*
     Creates a dataTable for adagios objects

     aoColumns are used primarily for Titles
     example, aoColumns = [ { 'sTitle': 'Contact Name'}, { 'sTitle': 'Alias' } ]

     */
    $.fn.adagios_ob_configure_dataTable = function (aoColumns, fetch) {
        // Option column
        aoColumns.unshift(
            {
                "sTitle":"register",
                "bVisible":false
            },
            {
                "sTitle":"object_type",
                "bVisible":false
            },
            {
                "sTitle":'<label rel="tooltip" title="Select All" id="selectall" class="checkbox"><input type="checkbox"></label>', 'sWidth':'32px'
            });
        aoColumns.push(
            {
                "sTitle": "Actions",
                "sWidth": '32px',
            }
        );
        var $this = $(this);

        $this.data('fetch', fetch);
        $this.data('aoColumns', aoColumns);

        return $this;
    };

    $.fn.adagios_ob_render_dataTable = function () {
        var $this = $(this);

        $this.dtData = [];
        $this.fetch = $this.data('fetch');
        $this.aoColumns = $this.data('aoColumns');
        $this.jsonqueries = $this.fetch.length;
        $.each($this.fetch, function (f, v) {
            var object_type = v['object_type'];
            $('#log').append('Populating ' + object_type + $(this).attr('id') + '<br/>');

            var json_query_fields = ['id', 'register'];
            $.each(v['rows'], function (k, field) {
                if ('cName' in field) {
                    json_query_fields.push(field['cName']);
                }
                if ("cAltName" in field) {
                    json_query_fields.push(field['cAltName']);
                }
                if ("cHidden" in field) {
                    json_query_fields.push(field['cHidden']);
                }
            });
            $.getJSON("../rest/pynag/json/get_objects",
                {
                    object_type:object_type,
                    with_fields:json_query_fields.join(",")
                },
                function (data) {
                    var count = data.length;
                    $.each(data, function (i, item) {
                        var field_array =
                            [item['register'], object_type, '\
    <input rel="tooltip" title="Select for bulk actions" id="ob_mass_select" name="' + item['id'] + '" type="checkbox">'];
                        $.each(v['rows'], function (k, field) {
                            var cell = '<a href="id=' + item['id'] + '">';
                            var field_value = "";
                            if ("icon" in field) {
                                cell += "<i class=\"" + field.icon + "\"></i> ";
                            }
                            if (item[field['cName']]) {
                                field_value = item[field['cName']];
                            } else {
                                if (item[field['cAltName']]) {
                                    field_value = item[field['cAltName']];
                                }
                            }
                            field_value = field_value.replace("\"", "&quot;");
                            field_value = field_value.replace(">", "&gt;");
                            field_value = field_value.replace("<", "&lt;");
                            if ("truncate" in field && field_value.length > (field['truncate'] + 3)) {
                                cell += "<abbr rel=\"tooltip\" title=\"" + field_value + "\">" + field_value.substr(0, field['truncate']) + " ...</abbr>";
                            } else {
                                cell += field_value;
                            }
                            cell += "</a>";
                            field_array.push(cell);
                            if (field['cName'] == v['rows'][v['rows'].length - 1]['cName']) {
                                $this.dtData.push(field_array);
                                count--;
                            }
                        });
                        field_array.push('\
                            <a rel="tooltip" title="Delete object" href="delete_object/id=' + item['id'] + '">\
                                <i class="icon-trash"></i>\
                            </a>\
                            <a rel="tooltip" title="Copy object" href="copy_object/id=' + item['id'] + '">\
                                    <i class="glyph-tags"></i>\
                                </a>\
                        ');
                    });
                }).success(function () {
                    //targetDataTable.fnAddData(dtData);

                    $this.jsonqueries = $this.jsonqueries - 1;

                    //alert($this.jsonqueries);
                    if ($this.jsonqueries == 0) {
                        $("[rel=tooltip]").tooltip();
                        //alert('predtData: ' + $this.dtData[0])
                        $this.data('dtData', $this.dtData);

                        $this.adagios_ob_dtPopulate();
                    }
                }).error(function (jqXHR) {
                    /* TODO - fix this to a this style */
                    //targetDataTable = $(this).data('datatable');
                    //targetDataTable.parent().parent().parent().html('<div class="alert alert-error"><h3>ERROR</h3><br/>Failed to fetch data::<p>URL: ' + this.url + '<br/>Server Status: ' + jqXHR.status + ' ' + jqXHR.statusText + '</p></div>');
                });
            return this;
        });
    };

    /*
     Populates the datatable

     jsonFields are used for describing which fields to fetch via json and how to handle them
     example, jsonFields = [ { 'cName': "command_name", 'icon_class': "glyph-computer-proces" }, ... ]

     object_type is one of contact, command, host, service, timeperiod
     example, object_type = host
     */
    $.fn.adagios_ob_dtPopulate = function() {
        var $this = $(this);
        var dtData = $this.data('dtData');
        var aoColumns = $this.data('aoColumns');
        $('#' + $this.attr('id') + ' #loading').hide();
        var dt;
        dt = $this.dataTable({
            "aoColumns":aoColumns,
            "sPaginationType":"bootstrap",
            // "sScrollY":"260px",
            // "bAutoWidth":true,
            "bScrollCollapse":false,
            "bPaginate":true,
            "iDisplayLength":200,
            "aaData":dtData,
            //"sDom":'<"toolbar' + $this.attr('id') + '">frtip',
            "sDom": "<'row-fluid'<'span7'<'toolbar_" + $this.attr('id') + "'>>'<'span5'f>r>t<'row-fluid'<'span6'i><'span6'p>>",
            // Callback which assigns tooltips to visible pages
            "fnDrawCallback":function () {
                $("[rel=tooltip]").tooltip();
                $('input').click(function() {
                    var checked = $('input#ob_mass_select:checked').length;
                    $('#bulkselected').html(checked);
                    if (checked > 0) {
                        $('a.bulk').removeClass('inactive');

                    } else {
                        $('a.bulk').addClass('inactive');
                    }
                });
            }
        });
        // Unbind sorting on the first visible column
        $('table#' + $this.attr('id') + ' th:first').unbind('click');

        $(".toolbar_" + $this.attr('id')).html('<div class="btn-group"></div>');
        $(".toolbar_" + $this.attr('id') + ' .btn-group'
            ).append('<a class="btn btn-primary" href="#filter_object"><i class="glyph-computer-service glyph-white"></i> ' + $this.attr('id') + 's</a>');
        if ($this.attr('id') != 'command' && $this.attr('id') != 'timeperiod') {
            $(".toolbar_" + $this.attr('id') + ' .btn-group'
                ).append('<a class="btn" href="#filter_group"><i class="glyph-parents"></i> Groups</a>');
        }
        $(".toolbar_" + $this.attr('id') + ' .btn-group'
            ).append('<a class="btn" href="#filter_template"><i class="glyph-cogwheels"></i> Templates</a>');
        /* $(".toolbar_" + $this.attr('id')).html("<strong>Show:</strong>");
        $(".toolbar_" + $this.attr('id')).append($this.attr('id') + " <input type='checkbox' id='select' data-show='" + $this.attr('id') + "' CHECKED>");
        $(".toolbar_" + $this.attr('id')).append("Templates <input type='checkbox' id='select' data-show='template'>");
        if ($this.attr('id') != 'command' && $this.attr('id') != 'timeperiod') {
           $(".toolbar_" + $this.attr('id')).append("Groups <input type='checkbox' id='select' data-show='group'>");
        } */

        console.log('Assignin click on #' + $this.attr('id') + '.tab-pane label#selectall');
        $('#' + $this.attr('id') + '.tab-pane label#selectall').on('click', function(e) {
            var $checkbox = $('#' + $this.attr('id') + '.tab-pane #selectall input');
            console.log('#' + $this.attr('id') + '.tab-pane #selectall input');

            if ($checkbox.attr('checked') != undefined) {
                //$checkbox.attr('checked', 'checked');
                $('.tab-pane.active .dataTable input').each(function() {
                    $(this).attr('checked', 'checked')

                });
            } else {
                //$checkbox.removeAttr('checked');
                $('.tab-pane.active .dataTable input').each(function() {
                    $(this).removeAttr('checked');
                });
            }
            var checked = $('input#ob_mass_select:checked').length;
            $('#bulkselected').html(checked);
            if (checked > 0) {
                $('a.bulk').removeClass('inactive');

            } else {
                $('a.bulk').addClass('inactive');
            }
        });
        /* When inputs are selected in toolbar, we call redraw on the datatable which calls the filtering routing
        above */
        $('[class^="toolbar_"] .btn-group a').on('click', function (e) {
            var $target = $(this);
            e.preventDefault();
            //alert(e.target.nodeName);
            if ($target.hasClass('btn-primary')) {
                $target.removeClass('btn-primary');
                $target.children().removeClass('glyph-white');
            } else {
                $target.addClass('btn-primary');
                $target.children().addClass('glyph-white');
            }
            var object_type = $target.parentsUntil('.tab-content', '.tab-pane').attr('id');
            $('table#' + object_type).dataTable().fnDraw();

            return false;
        });
        dt.fnSort([
            [3, 'asc'],
            [4, 'asc']
        ]);
        //return this.each(function() {
    };
    /*
     Object Browser, This runs whenever "Run Check Plugin" is clicked

     It resets the color of the OK/WARNING/CRITICAL/UNKNOWN button
     Runs a REST call to run the check_command and fetch the results

     Calling button/href needs to have data-object-id="12312abc...."
     */

    $.fn.adagios_ob_run_check_command = function() {
        // Fetch the calling object
        var modal = $(this);
        // Get the object_id
        var id = modal.attr('data-object-id');

        if (! id) {
            alert("Error, no data-object-id for run command");
            return false;
        }
        // Reset the class on the button
        $('#run_check_plugin #state').removeClass("label-important");
        $('#run_check_plugin #state').removeClass("label-warning");
        $('#run_check_plugin #state').removeClass("label-success");
        $('#run_check_plugin #state').html("Pending");
        $('#run_check_plugin #output pre').html("Executing check plugin");


        var plugin_execution_time = $("#run_check_plugin div.progress").attr('data-timer');
        if (plugin_execution_time > 1) {
            $("#run_check_plugin div.progress").show();
            var bar = $("#run_check_plugin div.bar");
            var step = 0;
            var steps = (plugin_execution_time / 20) * 100;
            function updateTimer() {
                step += 1;
                $("#run_check_plugin div.bar").css('width', step * 5 + "%");
                if (step < 20) {
                    setTimeout(updateTimer, step * steps);
                }
            }
            updateTimer();
        }

        // Run the command and fetch the output JSON via REST
        $.getJSON(BASE_URL + "rest/pynag/json/run_check_command",
            {
                object_id: id
            },
            function(data) {
                // Default to unknown if data[0] is less than 3
                var statusLabel = 'label-inverse';
                var statusString = 'Unknown';
                if (data[0] == 2) {
                    statusLabel = 'label-important';
                    statusString = 'Critical';
                }
                if (data[0] == 1) {
                    statusLabel = 'label-warning';
                    statusString = 'Warning';
                }
                if (data[0] == 0) {
                    statusLabel = 'label-success';
                    statusString = 'OK';
                }
                // Set the correct class for state coloring box
                $('#run_check_plugin #state').addClass(statusLabel);

                // Fill it up with the correct status
                $('#run_check_plugin #state').html(statusString);

                // Put the plugin output in the correct div
                if (data[1]) {
                    $('#run_check_plugin div#output pre').text(data[1]);
                } else {
                    $('#run_check_plugin #output pre').html("No data received on stdout");
                }

                if (data[2]) {
                    $('#run_check_plugin #error pre').text(data[2]);
                    $('#run_check_plugin div#error').show();
                }
                // Show the refresh button
                $('#run_check_plugin_refresh').show();
                $("#run_check_plugin div.progress").hide();

                // Assign this command to the newly shown refresh button
                $('#run_check_plugin_refresh').click(function() {
                    $(this).adagios_ob_run_check_command();
                });
            }).error(function (jqXHR) {
                /* TODO - fix this to a this style */
                alert('Failed to fetch data: URL: "' + this.url + '" Server Status: "' + jqXHR.status + '" Status: "' + jqXHR.statusText + '"');
            });
        // Stop the button from POST'ing
        return this;
    }
})( jQuery );


$(document).ready(function() {
    $("[rel=tooltip]").popover();
    $("#popover").popover();
    $('select').chosen();
});
