/*
Allow radio inputs as button in regular form
http://dan.doezema.com/2012/03/twitter-bootstrap-radio-button-form-inputs/

This stops regular posting for buttons and assigns values to a hidden input
to enable buttons as a radio.
*/
jQuery(function($) {
    $('div.btn-group[data-toggle-name=*]').each(function(){
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

// ObjectBrowser fade in of bulk action
function ob_mass_select_change() {
    $('#bulk').fadeIn();
}

/* Object Browser, This runs whenever "Run Check Plugin" is clicked

 It resets the color of the OK/WARNING/CRITICAL/UNKOWN button
 Runs a REST call to run the check_command and fetch the results

 Calling button/href needs to have data-object-id="12312abc...."
  */
function ob_run_check_command() {
    // Fetch the calling object
    modal = $(this);
    // Get the object_id
    id = modal.attr('data-object-id');

    // Reset the class on the button
    $('#run_check_plugin #pluginstate').removeClass("label-important");
    $('#run_check_plugin #pluginstate').removeClass("label-warning");
    $('#run_check_plugin #pluginstate').removeClass("label-success");
    $('#run_check_plugin #pluginstate').html("Pending");
    $('#run_check_plugin #pluginoutput').html("Executing check plugin");

    // Run the command and fetch the output JSON via REST
    $.getJSON("/rest/pynag/json/run_check_command",
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
        $('#run_check_plugin #pluginstate').addClass(statusLabel);

        // Fill it up with the correct status
        $('#run_check_plugin #pluginstate').html(statusString);

        // Put the plugin output in the correct div
        $('#run_check_plugin #pluginoutput').html(data[1]);

        // Show the refresh button
	    $('#run_check_plugin_refresh').show();

        // Assign this command to the newly shown refresh button
        $('#run_check_plugin_refresh').click(ob_run_check_command);
	});
    // Stop the button from POST'ing
    return false;
}
