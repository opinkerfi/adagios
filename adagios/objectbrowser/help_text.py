# -*- coding: utf-8 -*-
#
# Copyright 2012, Pall Sigurdsson <palli@opensource.is>
#
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" objectbrowser/all_attributes.py

This is an extends of pynag's all_attributes with friendly help message for all attributes.
"""

from pynag.Model.all_attributes import object_definitions
from django.utils.translation import ugettext as _


object_definitions["any"]["use"][
    "help_text"] = "Specifies which object to inherit settings from"
object_definitions["any"]["register"][
    "help_text"] = "Specifies if object is active (registered) or not"
object_definitions["any"]["name"][
    "help_text"] = "Generic name of this objects. Only used for templates."
object_definitions["host"]["host_name"]["help_text"] = "e.g. web01.example.com"
object_definitions["host"]["alias"]["help_text"] = "e.g. My Monitored Host"
object_definitions["host"]["display_name"]["help_text"] = ""
object_definitions["host"]["address"]["help_text"] = "e.g. 127.0.0.1"
object_definitions["host"]["parents"][
    "help_text"] = "Network parents of this host. No notification will be sent if parent is down."
object_definitions["host"]["hostgroups"][
    "help_text"] = "Which hostgroups this host belongs to"
object_definitions["host"]["check_command"][
    "help_text"] = "Command to execute when this object is checked"
object_definitions["host"]["initial_state"][
    "help_text"] = 'By default Nagios will assume that all hosts are in UP states when it starts. You can override the initial state for a host by using this directive. Valid options are: o = UP, d = DOWN, and u = UNREACHABLE.'
object_definitions["host"]["max_check_attempts"][
    "help_text"] = "How many failures do occur before notifications will be sent"
object_definitions["host"]["check_interval"][
    "help_text"] = "How many minutes to wait between checks"
object_definitions["host"]["retry_interval"][
    "help_text"] = "How many minutes to wait between checks when object goes to warning or critical state"
object_definitions["host"]["active_checks_enabled"][
    "help_text"] = "Whether Nagios actively checks this host"
object_definitions["host"]["passive_checks_enabled"][
    "help_text"] = "Whether Nagios passively accepts check results from an external source"
object_definitions["host"]["check_period"][
    "help_text"] = "When nagios checks for this host"
object_definitions["host"]["obsess_over_host"][
    "help_text"] = 'This directive determines whether or not checks for the host will be "obsessed" over using the ochp_command.'
object_definitions["host"]["check_freshness"]["help_text"] = ""
object_definitions["host"]["freshness_threshold"]["help_text"] = ""
object_definitions["host"]["event_handler"]["help_text"] = ""
object_definitions["host"]["event_handler_enabled"]["help_text"] = ""
object_definitions["host"]["low_flap_threshold"]["help_text"] = ""
object_definitions["host"]["high_flap_threshold"]["help_text"] = ""
object_definitions["host"]["flap_detection_enabled"]["help_text"] = ""
object_definitions["host"]["flap_detection_options"]["help_text"] = ""
object_definitions["host"]["process_perf_data"]["help_text"] = ""
object_definitions["host"]["retain_status_information"]["help_text"] = ""
object_definitions["host"]["retain_nonstatus_information"]["help_text"] = ""
object_definitions["host"]["contacts"]["help_text"] = ""
object_definitions["host"]["contact_groups"]["help_text"] = ""
object_definitions["host"]["notification_interval"]["help_text"] = ""
object_definitions["host"]["first_notification_delay"]["help_text"] = ""
object_definitions["host"]["notification_period"]["help_text"] = ""
object_definitions["host"]["notification_options"]["help_text"] = ""
object_definitions["host"]["notifications_enabled"]["help_text"] = ""
object_definitions["host"]["stalking_options"]["help_text"] = ""
object_definitions["host"]["notes"]["help_text"] = ""
object_definitions["host"]["notes_url"]["help_text"] = ""
object_definitions["host"]["action_url"]["help_text"] = ""
object_definitions["host"]["icon_image"]["help_text"] = ""
object_definitions["host"]["icon_image_alt"]["help_text"] = ""
object_definitions["host"]["vrml_image"]["help_text"] = ""
object_definitions["host"]["statusmap_image"]["help_text"] = ""
object_definitions["host"]["2d_coords"]["help_text"] = ""
object_definitions["host"]["3d_coords"]["help_text"] = ""
object_definitions["hostgroup"]["hostgroup_name"][
    "help_text"] = "Unique name for this hostgroup (e.g. webservers)"
object_definitions["hostgroup"]["alias"][
    "help_text"] = "Human friendly name (e.g. My Web Servers)"
object_definitions["hostgroup"]["members"][
    "help_text"] = "List of hosts that belong to this group"
object_definitions["hostgroup"]["hostgroup_members"][
    "help_text"] = "List of hostgroups that belong to this group"
object_definitions["hostgroup"]["notes"][
    "help_text"] = "You can put your custom notes here for your hostgroup"
object_definitions["hostgroup"]["notes_url"][
    "help_text"] = "Type in an url for example to a documentation site for this hostgroup"
object_definitions["hostgroup"]["action_url"]["help_text"] = ""
object_definitions["service"]["host_name"][
    "help_text"] = "e.g. web01.example.com"
object_definitions["service"]["hostgroup_name"][
    "help_text"] = "Hostgroup this service belongs to"
object_definitions["service"]["service_description"][
    "help_text"] = "e.g. 'Disk Status'"
object_definitions["service"]["display_name"]["help_text"] = ""
object_definitions["service"]["servicegroups"][
    "help_text"] = "Servicegroups that this service belongs to"
object_definitions["service"]["is_volatile"]["help_text"] = ""
object_definitions["service"]["check_command"][
    "help_text"] = "Command that is executed when this service is checked"
object_definitions["service"]["initial_state"]["help_text"] = ""
object_definitions["service"]["max_check_attempts"][
    "help_text"] = "How many times to try before failure notifications are sent out"
object_definitions["service"]["check_interval"][
    "help_text"] = "How many minutes to wait between checks"
object_definitions["service"]["retry_interval"][
    "help_text"] = "How many minutes to wait between checks when failure occurs"
object_definitions["service"]["active_checks_enabled"][
    "help_text"] = "Enable if you want nagios to actively check this service"
object_definitions["service"]["passive_checks_enabled"][
    "help_text"] = "Enable if you want nagios to passively accept check results from an external source"
object_definitions["service"]["check_period"][
    "help_text"] = "Period which this service is checked."
object_definitions["service"]["obsess_over_service"]["help_text"] = ""
object_definitions["service"]["check_freshness"]["help_text"] = ""
object_definitions["service"]["freshness_threshold"]["help_text"] = ""
object_definitions["service"]["event_handler"]["help_text"] = ""
object_definitions["service"]["event_handler_enabled"]["help_text"] = ""
object_definitions["service"]["low_flap_threshold"]["help_text"] = ""
object_definitions["service"]["high_flap_threshold"]["help_text"] = ""
object_definitions["service"]["flap_detection_enabled"]["help_text"] = ""
object_definitions["service"]["flap_detection_options"]["help_text"] = ""
object_definitions["service"]["process_perf_data"]["help_text"] = ""
object_definitions["service"]["retain_status_information"]["help_text"] = ""
object_definitions["service"]["retain_nonstatus_information"]["help_text"] = ""
object_definitions["service"]["notification_interval"]["help_text"] = ""
object_definitions["service"]["first_notification_delay"]["help_text"] = ""
object_definitions["service"]["notification_period"][
    "help_text"] = "Period which notifications are sent out for this service"
object_definitions["service"]["notification_options"]["help_text"] = ""
object_definitions["service"]["notifications_enabled"]["help_text"] = ""
object_definitions["service"]["contacts"][
    "help_text"] = "Which contacts to notify if service fails"
object_definitions["service"]["contact_groups"][
    "help_text"] = "Which contactgroups to send notifications to if service fails"
object_definitions["service"]["stalking_options"]["help_text"] = ""
object_definitions["service"]["notes"]["help_text"] = ""
object_definitions["service"]["notes_url"]["help_text"] = ""
object_definitions["service"]["action_url"]["help_text"] = ""
object_definitions["service"]["icon_image"]["help_text"] = ""
object_definitions["service"]["icon_image_alt"]["help_text"] = ""
object_definitions["servicegroup"]["servicegroup_name"][
    "help_text"] = "Unique name for this service group"
object_definitions["servicegroup"]["alias"][
    "help_text"] = "Human friendly name for this servicegroup"
object_definitions["servicegroup"]["members"][
    "help_text"] = "List of services that belong to this group (Example: localhost,CPU Utilization,localhost,Disk Usage)"
object_definitions["servicegroup"]["servicegroup_members"][
    "help_text"] = "Servicegroups that are members of this servicegroup"
object_definitions["servicegroup"]["notes"][
    "help_text"] = "Arbitrary notes or description of this servicegroup"
object_definitions["servicegroup"]["notes_url"][
    "help_text"] = "Arbitrary url to a site of your choice"
object_definitions["servicegroup"]["action_url"][
    "help_text"] = "Arbitrary url to a site of your choice"
object_definitions["contact"]["contact_name"][
    "help_text"] = "Unique name for this contact (e.g. username@domain.com)"
object_definitions["contact"]["alias"][
    "help_text"] = "Human Friendly Name for this contact (e.g. Full Name)"
object_definitions["contact"]["contactgroups"][
    "help_text"] = "List of groups that this contact is a member of."
object_definitions["contact"]["host_notifications_enabled"][
    "help_text"] = "If this contact will receive host notifications."
object_definitions["contact"]["service_notifications_enabled"][
    "help_text"] = "If this contact will receive service notifications."
object_definitions["contact"]["host_notification_period"][
    "help_text"] = "When will this contact receive host notifications"
object_definitions["contact"]["service_notification_period"][
    "help_text"] = "When will this contact receive service notifications"
object_definitions["contact"]["host_notification_options"][
    "help_text"] = "Which host notifications this contact will receive"
object_definitions["contact"]["service_notification_options"][
    "help_text"] = "Which service notifications this contact will receive"
object_definitions["contact"]["host_notification_commands"][
    "help_text"] = "What command will be used to send host notifications to this contact"
object_definitions["contact"]["service_notification_commands"][
    "help_text"] = "What command will be used to send service notifications to this contact"
object_definitions["contact"]["email"][
    "help_text"] = "E-mail address of this contact"
object_definitions["contact"]["pager"][
    "help_text"] = "Pager number of this contact"
object_definitions["contact"]["address"][
    "help_text"] = "Address of this contact"
object_definitions["contact"]["can_submit_commands"][
    "help_text"] = "If this contact is able to submit commands to nagios command pipe"
object_definitions["contact"]["retain_status_information"]["help_text"] = ""
object_definitions["contact"]["retain_nonstatus_information"]["help_text"] = ""
object_definitions["contactgroup"]["contactgroup_name"][
    "help_text"] = "Unique name for this contact group (e.g. 'webservers')"
object_definitions["contactgroup"]["alias"][
    "help_text"] = "Human Friendly Name (e.g. 'My Web Servers')"
object_definitions["contactgroup"]["members"][
    "help_text"] = "Every Contact listed here will be a member of this contactgroup"
object_definitions["contactgroup"]["contactgroup_members"][
    "help_text"] = "Every Contactgroup listed here will be a member of this contactgroup"
object_definitions["timeperiod"]["timeperiod_name"][
    "help_text"] = "Unique name for this timeperiod (.e.g. 'workhours')"
object_definitions["timeperiod"]["alias"][
    "help_text"] = "Human Friendly name for this timeperiod"
object_definitions["timeperiod"]["[weekday]"]["help_text"] = ""
object_definitions["timeperiod"]["[exception]"]["help_text"] = ""
object_definitions["timeperiod"]["exclude"]["help_text"] = ""
object_definitions["command"]["command_name"][
    "help_text"] = "Unique name for this command"
object_definitions["command"]["command_line"][
    "help_text"] = "Command line of the command that will be executed"
object_definitions["servicedependency"][
    "dependent_host_name"]["help_text"] = ""
object_definitions["servicedependency"][
    "dependent_hostgroup_name"]["help_text"] = ""
object_definitions["servicedependency"][
    "dependent_service_description"]["help_text"] = ""
object_definitions["servicedependency"]["host_name"]["help_text"] = ""
object_definitions["servicedependency"]["hostgroup_name"]["help_text"] = ""
object_definitions["servicedependency"][
    "service_description"]["help_text"] = ""
object_definitions["servicedependency"]["inherits_parent"]["help_text"] = ""
object_definitions["servicedependency"][
    "execution_failure_criteria"]["help_text"] = ""
object_definitions["servicedependency"][
    "notification_failure_criteria"]["help_text"] = ""
object_definitions["servicedependency"]["dependency_period"]["help_text"] = ""
object_definitions["serviceescalation"]["help_text"] = ""
object_definitions["serviceescalation"]["host_name"]["help_text"] = ""
object_definitions["serviceescalation"]["hostgroup_name"]["help_text"] = ""
object_definitions["serviceescalation"][
    "service_description"]["help_text"] = ""
object_definitions["serviceescalation"]["contacts"]["help_text"] = ""
object_definitions["serviceescalation"]["contact_groups"]["help_text"] = ""
object_definitions["serviceescalation"]["first_notification"]["help_text"] = ""
object_definitions["serviceescalation"]["last_notification"]["help_text"] = ""
object_definitions["serviceescalation"][
    "notification_interval"]["help_text"] = ""
object_definitions["serviceescalation"]["escalation_period"]["help_text"] = ""
object_definitions["serviceescalation"]["escalation_options"]["help_text"] = ""
object_definitions["hostdependency"]["dependent_host_name"]["help_text"] = ""
object_definitions["hostdependency"][
    "dependent_hostgroup_name"]["help_text"] = ""
object_definitions["hostdependency"]["host_name"]["help_text"] = ""
object_definitions["hostdependency"]["hostgroup_name"]["help_text"] = ""
object_definitions["hostdependency"]["inherits_parent"]["help_text"] = ""
object_definitions["hostdependency"][
    "execution_failure_criteria"]["help_text"] = ""
object_definitions["hostdependency"][
    "notification_failure_criteria"]["help_text"] = ""
object_definitions["hostdependency"]["dependency_period"]["help_text"] = ""
object_definitions["hostescalation"]["host_name"]["help_text"] = ""
object_definitions["hostescalation"]["hostgroup_name"]["help_text"] = ""
object_definitions["hostescalation"]["contacts"]["help_text"] = ""
object_definitions["hostescalation"]["contact_groups"]["help_text"] = ""
object_definitions["hostescalation"]["first_notification"]["help_text"] = ""
object_definitions["hostescalation"]["last_notification"]["help_text"] = ""
object_definitions["hostescalation"]["notification_interval"]["help_text"] = ""
object_definitions["hostescalation"]["escalation_period"]["help_text"] = ""
object_definitions["hostescalation"]["escalation_options"]["help_text"] = ""
object_definitions["hostextinfo"]["host_name"]["help_text"] = ""
object_definitions["hostextinfo"]["notes"]["help_text"] = ""
object_definitions["hostextinfo"]["notes_url"]["help_text"] = ""
object_definitions["hostextinfo"]["action_url"]["help_text"] = ""
object_definitions["hostextinfo"]["icon_image"]["help_text"] = ""
object_definitions["hostextinfo"]["icon_image_alt"]["help_text"] = ""
object_definitions["hostextinfo"]["vrml_image"]["help_text"] = ""
object_definitions["hostextinfo"]["statusmap_image"]["help_text"] = ""
object_definitions["hostextinfo"]["2d_coords"]["help_text"] = ""
object_definitions["hostextinfo"]["3d_coords"]["help_text"] = ""
object_definitions["serviceextinfo"]["host_name"]["help_text"] = ""
object_definitions["serviceextinfo"]["service_description"]["help_text"] = ""
object_definitions["serviceextinfo"]["notes"]["help_text"] = ""
object_definitions["serviceextinfo"]["notes_url"]["help_text"] = ""
object_definitions["serviceextinfo"]["action_url"]["help_text"] = ""
object_definitions["serviceextinfo"]["icon_image"]["help_text"] = ""
object_definitions["serviceextinfo"]["icon_image_alt"]["help_text"] = ""
