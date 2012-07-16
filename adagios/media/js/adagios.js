/*
Allow radio inputs as button in regular form
http://dan.doezema.com/2012/03/twitter-bootstrap-radio-button-form-inputs/
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

function mass_select_change() {
    $('#bulk').fadeIn();
}
function run_check_command(modal) {

    id = modal.attr('data-object-id');
    $.getJSON("/rest/pynag/json/run_check_command",
	{
		object_id: id
	},
	function(data) {
        console.log('fle');

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
        $('#run_check_plugin_refresh').click(check_plugin_refresh);

	});
};

function check_plugin_refresh() {
    modal = $(this);
    // Reset the class on the button
    $('#run_check_plugin #pluginstate').removeClass("label-important");
    $('#run_check_plugin #pluginstate').removeClass("label-warning");
    $('#run_check_plugin #pluginstate').removeClass("label-success");
    $('#run_check_plugin #pluginstate').html("Pending");
    $('#run_check_plugin #pluginoutput').html("Executing check plugin");

    // Rerun the command
    run_check_command(modal);

    // Disable button posting page
    return false;
};

