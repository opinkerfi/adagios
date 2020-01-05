%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%define name adagios
%define release 1

Name: adagios
Version: 1.6.6
Release: %{release}%{?dist}
Summary: Web Based Nagios Configuration
Group: Applications/Internet
License: AGPLv3
URL: https://adagios.opensource.is/
Source0: https://pypi.python.org/packages/source/a/adagios/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Prefix: %{_prefix}

BuildRequires: python2-devel
BuildRequires: python-setuptools

Requires: pynag > 0.9.1
Requires: httpd
Requires: mod_wsgi
Requires: sudo
Requires: python-simplejson

%if 0%{?rhel} == 6
Requires: python-django
# Force django upgrade
Conflicts: Django < 1.4.0
%else
Requires: python2-django16
%endif

%description
Adagios is a web based Nagios configuration interface build to be simple and intuitive in design, exposing less of the clutter under the hood of nagios.

%prep
%setup -qn %{name}-%{version} -n %{name}-%{version}
VERSION=%{version}
echo %{release} | grep -q git && VERSION=$VERSION-%{release}
sed -i "s/^__version__.*/__version__ = '$VERSION'/" adagios/__init__.py

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d/
install %{buildroot}%{python_sitelib}/adagios/apache/adagios.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/adagios.conf

mkdir -p %{buildroot}%{_sysconfdir}/adagios/conf.d/
install %{buildroot}%{python_sitelib}/adagios/etc/adagios/adagios.conf %{buildroot}%{_sysconfdir}/adagios/
install %{buildroot}%{python_sitelib}/adagios/etc/adagios/conf.d/okconfig.conf %{buildroot}%{_sysconfdir}/adagios/conf.d/

mkdir -p %{buildroot}%{_sysconfdir}/sudoers.d/
install %{buildroot}%{python_sitelib}/adagios/etc/sudoers.d/adagios %{buildroot}%{_sysconfdir}/sudoers.d/

mkdir -p "%{buildroot}%{_localstatedir}/lib/adagios/"
mkdir -p "%{buildroot}%{_localstatedir}/lib/adagios/userdata"
cp -r "%{buildroot}%{python_sitelib}/adagios/contrib/lib"  "%{buildroot}%{_localstatedir}/lib/adagios/contrib"

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc README.md
%{python_sitelib}/*
%{_localstatedir}/lib/adagios/contrib/*
%attr(0644, root, root) %config(noreplace) %{_sysconfdir}/httpd/conf.d/adagios.conf
%attr(0775, nagios, nagios) %dir %{_sysconfdir}/adagios
%attr(0775, nagios, nagios) %dir %{_sysconfdir}/adagios/conf.d
%attr(0775, nagios, nagios) %dir %{_localstatedir}/lib/adagios
%attr(0664, nagios, nagios) %config(noreplace) %{_sysconfdir}/adagios/adagios.conf
%attr(0664, nagios, nagios) %config(noreplace) %{_sysconfdir}/adagios/conf.d/*
%attr(0440, root, root) %config(noreplace) %{_sysconfdir}/sudoers.d/adagios

%changelog
* Wed Aug 28 2013 Pall Sigurdsson <palli@opensource.is> 1.2.4-1
- Fix syntax error in adagios.conf (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- More button made part of the action_buttons block (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- status/perfdata2 - fix link to services (palli@opensource.is)
- status/hostgroups - checkboxes next to hostgroups (palli@opensource.is)
- Added more button for extra actions in status view (tommi@tommi.org)
- New view /status/perfdata2 (palli@opensource.is)
- hostgrouplist refactored to use snippet (palli@opensource.is)
- status_detail layout changes (palli@opensource.is)
- Update debian package (palli@opensource.is)
- Moved WSGIProcessGroup within <location /adagios> (tommi@tommi.org)
- Debian package directory created (palli@opensource.is)
- adagios.conf - Clarifications to default values (palli@opensource.is)
- setup.py - python paths for apache fixes (palli@opensource.is)
- setup.py - pep8 cleanup (palli@opensource.is)
- BI - Fix reference to non-existing localhost (palli@opensource.is)
- Updates to status_detail look (palli@opensource.is)
- objectbrowser/forms.py pep8 cleanup (palli@opensource.is)
- BI - cleanup in views.py (palli@opensource.is)
- BI - urls.py allow for any process_type (palli@opensource.is)
- BI: macro resolving updates (palli@opensource.is)
- Performance: adagios.bi resolve macros only once per instance
  (palli@opensource.is)
- Fix: urls for pnp4nagios edit file (palli@opensource.is)
- Minor updates to BI module (palli@opensource.is)
- PEP8 fix (palli@opensource.is)
- BI unit tests moved to tests.py (palli@opensource.is)
- Fix: path issues in bi (palli@opensource.is)
- Business Intelligence moved from status to its own module
  (palli@opensource.is)
- bi: Macro support in human friendly status (palli@opensource.is)
- Fix: links on static BI pages (palli@opensource.is)
- added static BI view for iceland.adagios.org (palli@opensource.is)
- cleanup for static BI pages (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- incremental updates to BI (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- scripts->static_businessprocess.py - incremental updates
  (palli@opensource.is)
- status -> forms: pep8 cleanups (palli@opensource.is)
- Fix: BI add graphs typo (palli@opensource.is)
- Update status_error.html - Fix typo (mikecom32@gmail.com)
- scripts directory created (palli@opensource.is)
- status->services: Put a timed refresh on 30seconds (palli@opensource.is)
- selectable class added to status.html and status_detail.html
  (palli@opensource.is)
- selectable class added to status.html (palli@opensource.is)
- enhanchement: links on state_history view (palli@opensource.is)
- new status/rest function 'get' (palli@opensource.is)
- base status updates to javascript (palli@opensource.is)
- javascript updates to select2 objects query (palli@opensource.is)
- css: nomargin class added (palli@opensource.is)
- update servicelist checkboxes to new status standard (palli@opensource.is)
- checkboxes on perfdata metrics (palli@opensource.is)
- add subprocess and add graphs improvements (palli@opensource.is)
- CSS: links are bold again (for now) except on left_sidemenu
  (palli@opensource.is)
- Create servicegroups view (palli@opensource.is)
- fix typo in bpi forms (palli@opensource.is)
- error handler on businessprocess graphs (palli@opensource.is)
- Fix: business process add now redirects to edit after save
  (palli@opensource.is)
- PNP graphs now have last_value attribute (palli@opensource.is)
- Business Intelligence support last value of graph (palli@opensource.is)
- adagios.businessprocess - pep8 cleanup (palli@opensource.is)
- Business intelligence dashboard headers improved (palli@opensource.is)
- better graph support in business intelligence module (palli@opensource.is)
- PEP8 remove linebreak (palli@opensource.is)
- status.views pep8 cleanup (palli@opensource.is)
- Fix: rest/pynag delete_object was using obsolete pynag code
  (palli@opensource.is)
- New modules for custom pages (palli@opensource.is)

* Thu Jul 04 2013 Pall Sigurdsson <palli@opensource.is> 1.2.3-1
- Fix check_command editor when effective command line returns null
  (palli@opensource.is)

* Fri May 24 2013 Your Name <you@example.com> 1.2.1-2
- Remove remaining javascript alerts alert() (palli@opensource.is)
- Host aliases displayed in status detail (palli@opensource.is)
- clean up settings.py so unittests work again (palli@opensource.is)
- Fix select all functionality, using obsolete attr for clicked
  (tommi@tommi.org)
- objectbrowser->status view, assume return code 1 is DOWN
  (palli@opensource.is)
- DEPENDENCIES file deprecated by requirements.txt (palli@opensource.is)
- status/overview: top_alert_producers spinner refactored (palli@opensource.is)
- Remove direct access to /misc/edit_file (palli@opensource.is)
- Dashboard, fix incorrect counting of network parents (palli@opensource.is)
- nagios->Service better error handling (palli@opensource.is)
- Friendlier error message for pnp4nagios errors (palli@opensource.is)
- hostgroup_name changed from choicefield to textfield (palli@opensource.is)
- status/error cosmetic changes (palli@opensource.is)
- gitlog: run git.show internally instead of git.diff (palli@opensource.is)
- apache config: Change apache auth name (palli@opensource.is)
- Objectbrowser: Unused cancel button removed (palli@opensource.is)
- Fix objectbrowser/advanced errors being lost (palli@opensource.is)
- status/services: new querystring parameter: unhandled (palli@opensource.is)
- edit nagios.cfg: Fix cache not being invalidated (palli@opensource.is)
- okconfig->addtemplate Hide host templates from list of templates
  (palli@opensource.is)
- Fix typo in smart_str (palli@opensource.is)
- status/services -> include chat icon for comments (palli@opensource.is)
- status/error -> update name of check-mk-livestatus deb package
  (palli@opensource.is)
- status/detail - Reintroduce image preview on pnp4nagios graphs
  (palli@opensource.is)
- status/error - minor cosmetic patch (palli@opensource.is)
- nagios.cfg default location set to None (palli@opensource.is)
- status/error/ friendlier error messages if livestatus is not running
  (palli@opensource.is)
- /status/log/ mk-livestatus not needed in this view (palli@opensource.is)
- Fix javascript errors on pages that don't have searchbox
  (palli@opensource.is)
- okconfig install_agent error now has dynamic path to nsclient
  (palli@opensource.is)
- okconfig/install - Friendlier error messages (palli@opensource.is)
- update outdated rest function get_object() (palli@opensource.is)
- bugfix in status/detail. Custom variable editing fixed (palli@opensource.is)
- Changed version information on frontpage (palli@opensource.is)
- Revert "Removed editfile functionality, was not used anywhere."
  (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Fix bug where host commands where treated as service commands in
  status_detail (palli@opensource.is)
- Removed editfile functionality, was not used anywhere. (tommi@tommi.org)
- Fix unhandled exception in git eventhandler integration (palli@opensource.is)
- Make PNP path configurable (palli@opensource.is)
- New config option: enable_authorization (palli@opensource.is)
- Meta refresh removed from base_status (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- clean extra middleware (palli@opensource.is)
- Issue #119 - json based updating of variables after jquery update broken
  (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- send email.. properly check all checkboxes (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Issue #90 - Removed alert from a couple more places (tommi@tommi.org)
- Update README.md (palli-github@minor.is)
- Issue #90 - Removed alert from run check command (tommi@tommi.org)
- Updated descriptions (tommi@tommi.org)
- okconfig->addservice display service_description (palli@opensource.is)
- objectbrowser->edit host fix typos (palli@opensource.is)
- Updated links to project site and bug reports (palli@opensource.is)
- Temporarily disable access control (palli@opensource.is)
- README.md - drop link to github issue tracker (palli@opensource.is)
- status.utils.get_hosts() (palli@opensource.is)
- adding requirements.txt (palli@opensource.is)
- README.md - Fix typo (thanks lebean) (palli@opensource.is)
- send email -> message is now optional (palli@opensource.is)
- okconfig -> fix broken link in breadcrumbs (palli@opensource.is)
- Fix unhandled traceback when services_with_info does not exist in livestatus.
  (palli@opensource.is)
- /misc/mail/ add option to acknowledge problems when emails are sent out
  (palli@opensource.is)
- /rest/: switch to non-greedy regex to avoid trailing-slash errors
  (palli@opensource.is)
- Fix unicode error handling in object browser (palli@opensource.is)
- Javascript template update (palli@opensource.is)
- adagios/init: code cleanup (palli@opensource.is)
- rest/views: cleanup extra print statements (palli@opensource.is)
- REST: fix unhandled exception in host acknowledgements (palli@opensource.is)
- adagiostags - duration should say days when in plural (palli@opensource.is)

* Tue Apr 30 2013 Pall Sigurdsson <palli@opensource.is> 1.2.0-2
- Moved time selection in downtime to back (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Added datetimepicker to adagios.js and implmented downtime (tommi@tommi.org)
- Fix link to nagiosaurus web interface (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Fixes to layout for datetimepicker and disabled slider (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Status view: Fix traceback when okconfig is installed, but no config files
  present (palli@opensource.is)
- Merge branch 'gh-pages' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Updates demo website URL (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Create gh-pages branch via GitHub (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- Create gh-pages branch via GitHub (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- Create gh-pages branch via GitHub (palli-github@minor.is)
- Create README.md (palli-github@minor.is)
- /rest/pynag/add_object method created (palli@opensource.is)
- Allow columns=False parameter to livestatus. Workaround for livestatus bug
  (palli@opensource.is)
- google map, fix link to service checks (palli@opensource.is)
- Big screen problems renamed to dashboard (palli@opensource.is)
- CNAME: Removed www. from adagios.org (palli@opensource.is)
- adagios.org domains added to CNAME (palli@opensource.is)
- Create gh-pages branch via GitHub (palli-github@minor.is)
- Create gh-pages branch via GitHub (palli-github@minor.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Added slider for time selection (tommi@tommi.org)
- minor changes to send email feature (palli@opensource.is)
- updated layout for emails (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Google map, added polylines for network parents (palli@opensource.is)
- Update README.md (tommi@tommi.org)
- Bugfix in send_mail, add_myself_to_cc was not read (palli@opensource.is)
- Updated Send mail feature, add_myself_to_cc added (palli@opensource.is)
- http referer updated (palli@opensource.is)
- Updates to send mail feature (palli@opensource.is)
- Updated "send email" feature (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Updates to host lists and hostgroup lists (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Added bootstrap-datepicker for previous patch (tommi@tommi.org)
- Added datepicker to Status / Log (tommi@tommi.org)
- Update README.md (palli-github@minor.is)
- error handlers added on all status views (palli@opensource.is)
- Layout expirements for big screen view (palli@opensource.is)
- Layout expirements for big screen view (palli@opensource.is)
- Layout expirements for big screen view (palli@opensource.is)
- Performance tuning for overview and services (palli@opensource.is)
- contactgroup detail page and contact detail page updated
  (palli@opensource.is)
- problems view now uses default table (palli@opensource.is)
- Fix zero divisionerror in frontpage (palli@opensource.is)
- remove unneeded class=1 query parameter (palli@opensource.is)
- improvements to problems view (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Prevent run check command event firing when no id (tommi@tommi.org)
- Unhandled problems now excludes downtime in top header (palli@opensource.is)
- Send mail to field changed to select2 field (palli@opensource.is)
- Send email button added to base status (palli@opensource.is)
- Fix for csrf token code (tommi@tommi.org)
- Added cookie based csrf protection for posts (tommi@tommi.org)
- Fix hardcoded paths in /status/overview/ (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Closes #98 Clear error in run_plugin (tommi@tommi.org)
- Removed obsolete .live for .on (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Fixed a href selector for tab selection (tommi@tommi.org)
- remove extra print statements (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- More work on send email functionality (palli@opensource.is)
- Remove stale table.table modifications (palli@opensource.is)
- Remove spinner from unhandled problems (palli@opensource.is)
- Removed datepicker reference, not used. (tommi@tommi.org)
- Removed reference to old pnp/js code (tommi@tommi.org)
- Upgraded to jquery 1.9.1 (tommi@tommi.org)
- /status/ performance tuning (palli@opensource.is)
- Prototype of send email form (palli@opensource.is)
- Fix check_nagios_running() fail on first load (palli@opensource.is)
- Layout tweaks for rest module (palli@opensource.is)
- Performance tweaks for status view (palli@opensource.is)
- Disable plugin execution in demo environment. (palli@opensource.is)
- rest calls created for log fetching (palli@opensource.is)
- /rest/status/hosts and /rest/status/services (palli@opensource.is)
- search box works again for _status_combined (palli@opensource.is)
- Network parent tree in status_detail (palli@opensource.is)
- error handler minor bugfixes (palli@opensource.is)
- misc/service view migrated to base_status look (palli@opensource.is)
- fix google chrome btn group wrap bug (palli@opensource.is)
- Startup() code in adagios module moved to objectbrowser (palli@opensource.is)
- First installment of error_page decorator (palli@opensource.is)
- minor improvements to error page (palli@opensource.is)
- Copy service now supports changing service_description (palli@opensource.is)
- 90sec refresh set to all status pages. (palli@opensource.is)
- bugfix, keyerror when host has no services (palli@opensource.is)
- reapply search box feature (palli@opensource.is)
- sort order for hostgruops changed (palli@opensource.is)
- hostgroup updates (palli@opensource.is)
- New css class progress-bar-unknown (palli@opensource.is)
- pynag.Utils.grep now used for services and hostgroup views
  (palli@opensource.is)
- UTF-8 handling applied to all forms in objectbrowser and okconfig
  (palli@opensource.is)
- incremental updates (palli@opensource.is)
- Fix traceback in LogFiles() when nagios.cfg is not in a common place.
  (palli@opensource.is)
- Format fix, spaces in calculations (tommi@tommi.org)
- improve git log layout (palli@opensource.is)
- Show host custom variables in service detail (palli@opensource.is)
- Fix unhandled exception when invalid check_command is defined
  (palli@opensource.is)
- Colored coded diff in gitlog (palli@opensource.is)
- okconfig automatic git commit on add templates (needs latest okconfig)
  (palli@opensource.is)
- Objectbrowser.Forms now use Attributelist to split contact_groups style
  fields (palli@opensource.is)
- New view: /misc/images/ for the old nagios icon_images (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Experimental Perfdata view added (palli@opensource.is)
- More descriptive placeholder for timestamp fields (palli@opensource.is)
- More unittests added (palli@opensource.is)
- Objectbrowser -> Forms -> Default value for single choice fields is now a
  blank value (palli@opensource.is)
- font-size for host table now same as services and hostgroups
  (palli@opensource.is)
- changes to sidemenu (palli@opensource.is)
- Unit Tests added for troubleshooting purposes. (palli@opensource.is)
- Update README.md (palli-github@minor.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Update README.md (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- Single hostgroup view improvements (palli@opensource.is)
- status_contact comment feed now uses the new snippet (palli@opensource.is)
- updates to hostgroup view for a single hostgroup. status_contact updates
  (palli@opensource.is)
- Put a placeholder with inherited value (palli@opensource.is)
- Inherited attributes visible in objectbrowser (palli@opensource.is)
- Minor improvements to git log. Git log now available in the contact_detail
  view (palli@opensource.is)
- incremental updates. New Comments and Downtime views added
  (palli@opensource.is)
- Make sure status views honor nagios.cfg location set in adagios.conf file
  (palli@opensource.is)
- misc.helpers should always use the nagios.cfg specified in adagios.conf
  (palli@opensource.is)
- Objectbrowser custom variable and advanced tab improvements
  (palli@opensource.is)
- Some performance tweaks for large number of services if livestatus is
  enabled. (palli@opensource.is)
- viewing contact details, now shows the services they can see
  (palli@opensource.is)
- Incremental updates (palli@opensource.is)
- Fix broken links in okconfig/addcomplete (palli@opensource.is)
- incremental changes (palli@opensource.is)
- Improvements to comments and contacts views (palli@opensource.is)
- Comments added back to services view (palli@opensource.is)
- Don't try to display logs if there are no recent log entries.
  (palli@opensource.is)
- Resolved conflicts (palli@opensource.is)
- Resolved conflicts (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Status view now has contact information (palli@opensource.is)
- Status view now has contact information (palli@opensource.is)
- Log view moved from experimental. (palli@opensource.is)
- Autocomplete api in /rest/status/autocomplete (palli@opensource.is)
- top_alert_producers number now includes only log messages with state other
  than OK (palli@opensource.is)
- Incremental updates (palli@opensource.is)
- Host down not shown if host parent is also down (palli@opensource.is)
- url pattern changed for states detail to avoid double slash problem
  (palli@opensource.is)
- releasers updated (palli@opensource.is)
- status overview, top alert number now links to log (palli@opensource.is)
- Daily dosage of improvements * Fix google maps issues with bootstrap * Delete
  object now works with shortnames, delete object button works now in
  status_detail * status circles now spin if problem is unhandled *
  status_detail history now more accurate * status_log now very functional
  (palli@opensource.is)
- unneeded js cleanup (palli@opensource.is)
- add new marker now creates popup by default (palli@opensource.is)
- big update on status.. new map. Expirement with tiles instead of boxes
  (palli@opensource.is)
- improvements to state history (palli@opensource.is)
- rest/status/edit should save() (palli@opensource.is)
- changed css class block so that shadows are now minor (palli@opensource.is)
- remove keyerror (palli@opensource.is)
- general status module improvements (palli@opensource.is)
- hook for unhandled problems added (palli@opensource.is)
- extra print statements removed (palli@opensource.is)
- notification tray removed (palli@opensource.is)
- Better titles for boxes (palli@opensource.is)
- switched to white background (palli@opensource.is)
- Log view added. Default page changed to status_index (palli@opensource.is)
- New view: State History (palli@opensource.is)
- match hostnames correctly when service_description has multiple /
  (palli@opensource.is)
- layout tweaks for monitor01 (palli@opensource.is)
- status improvements, new base1.html (palli@opensource.is)
- layout updates ; new views in status (palli@opensource.is)
- Various improvements to reschedule and acknowledge in status view
  (palli@opensource.is)
- more work on acknowledge and schedule buttons (palli@opensource.is)
- path fixes for status rest interface (palli@opensource.is)
- status rest interface start. button functionality (palli@opensource.is)
- hostgroup view changed into proper hierarchy. Service List condensed
  (palli@opensource.is)
- Graph loading javascript made firefox compatible (palli@opensource.is)
- Comments for service checks now pretty (palli@opensource.is)
- multiselect selectbox added (palli@opensource.is)
- Titles fixed (palli@opensource.is)
- Tooltip added to progress bar (palli@opensource.is)
- Firefox support for progress bars (palli@opensource.is)
- switched to condensed tables (palli@opensource.is)
- more layout changes in status. Network Parents added (palli@opensource.is)
- hostgroup hosts hidden by default. hide empty hostgroups
  (palli@opensource.is)
- ajaxy graph loading (palli@opensource.is)
- show check_command for hosts (palli@opensource.is)
- needs_reload status is now changed directly after a reload
  (palli@opensource.is)
- layout changes in status module (palli@opensource.is)
- deprecation of base.html (palli@opensource.is)
- PNP moved to seperate module (palli@opensource.is)
- minor workarounds when no permission to run pnp, templatetags dded
  (palli@opensource.is)
- PNP Integration. Status Improvements (palli@opensource.is)
- more status and livestatus updates (needs pynag master) (palli@opensource.is)
- overall layout improvements in status module (palli@opensource.is)
- status views moved to a seperate module (palli@opensource.is)
- Event log and extra information added to host status (palli@opensource.is)
- localhost:8000/misc/status/ improvements (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Added jqplot (again... ) (tommi@tommi.org)
- Enable advanced and geek to save new objects (palli@opensource.is)
- Servicegroup view created and Service list fixed in sidebar
  (palli@opensource.is)
- PNP Integration made visible in misc menubar Closes #58 (palli@opensource.is)
- Objectbrowser search no longer imports oldinvalid javascripts. Closes #83
  (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- minor improvements to contactgroup hierarchy (palli@opensource.is)
- Test implementation of jqplot (tommi@tommi.org)
- Reworked view for editing hostgroup. Improved help texts for hosts and
  hostgroups (palli@opensource.is)
- Reworked view for editing contactgroup. Improved help texts for contacts and
  contactgroups (palli@opensource.is)
- test with contactgroup hierarchy (palli@opensource.is)
- bugfix: Always use generic name when available if copying a template. Closes
  #81 (palli@opensource.is)
- Bugfix: host_name field incorrectly clean in objectbrowser->copy->service.
  Closes #84. (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Fix sorting of keys in nagios.cfg (tommi@tommi.org)
- Added better looking objectbrowser/search (tommi@tommi.org)
- Added fataError javascript function (tommi@tommi.org)
- Merge remote-tracking branch 'origin/master' (tommi@tommi.org)
- Closes #82 - Remove alert if unable to fetch new version (tommi@tommi.org)
- objectbrowser->copy_object now handles templates better than before
  (palli@opensource.is)
- pnp view bugfixes (palli@opensource.is)
- improvements to pnp integration (palli@opensource.is)
- elif removed from nagios_service view since it is not compatible with django
  1.3.x (palli@opensource.is)
- checkbox to wide patch from tomas re-applied (palli@opensource.is)
- removed nagios_pid print statements (palli@opensource.is)
- minor layout tweaks for pnp (palli@opensource.is)
- merged (palli@opensource.is)
- PNP Integration prototype (palli@opensource.is)
- Textarea css for edit_file form (palli@opensource.is)
- nagios_cfg variable exposed to all templates. (palli@opensource.is)
- Closes #77 Unbind click handler before assigning new click handler
  (tommi@tommi.org)
- Closes #78 checkbox should not have width. (tommi@tommi.org)
- Fixes to status and reload buttons (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Closes #80 Fix bug where compared values were off (tommi@tommi.org)
- Update README.md (palli-github@minor.is)
- removed extra print statements (palli@opensource.is)
- Update README.md (palli-github@minor.is)
- First pages commit (tommi@tommi.org)

* Fri Oct 26 2012 Pall Sigurdsson <palli@opensource.is> 1.1.2-2
- fix block=smallheader boilerplates in misc module (palli@opensource.is)
- minor cosmetic fixes in status cgi (palli@opensource.is)
- Macro editing for hosts and services in objectbrowser (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Adding git reference to testing rpms (palli@opensource.is)
- Update README.md (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- size patch for select2 fields (palli@opensource.is)
- merged frontpage description with version check (palli@opensource.is)
- frontpage description updated (palli@opensource.is)
- Merge remote-tracking branch 'github/master' (tommi@tommi.org)
- Closes #56 - Implmented jsonp version checking (tommi@tommi.org)
- tomhom (palli@opensource.is)
- INSTALL removed in favour of README.md (palli@opensource.is)
- Nagios service reload button reintroduced (palli@opensource.is)
- pycharm inspection updates (palli@opensource.is)
- Nagios Service view now displays a notice if service needs to be reloaded
  (palli@opensource.is)
- Bugfix where sudo was removed from init script path if provided.
  (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Added select2 functionality (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- ensure_ascii set to False for simplejson (palli@opensource.is)
- Update README.md (palli-github@minor.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Improvements to objectbrowser/delete/ (palli@opensource.is)
- Fixes responsive design of ob->list->service shortname (tommi@tommi.org)
- Closes #75 - Removed hardcoded path for url resolver (tommi@tommi.org)
- Minor cosmetic patch (tommi@tommi.org)
- Merge remote-tracking branch 'github/master' (tommi@tommi.org)
- Closes #31 - Major rework of IDs to fix jump on location.hash change
  (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- status.html added (palli@opensource.is)
- exception handling broadened on objectbrowser views (palli@opensource.is)
- objectbrowser unicode strings converted to bytestrings before being passed to
  pynag (palli@opensource.is)
- Responsive - show service shortname on small devices (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Fixes to responsive ob list (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Various fixes related to get_effective_contactgroups and
  get_effective_hostgroups (palli@opensource.is)
- experimental status view added and settings bugfix (palli@opensource.is)
- Resize ob list working, implemented hiding column (tommi@tommi.org)
- Closes #61 - Implemented run_commands for okconfig/edithost (tommi@tommi.org)
- Typo in warning message regarding uncommitted changes (tommi@tommi.org)
- Fixed dismissal of notifications and failure handling (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Closes #72 - inconsistant labels on level="" (tommi@tommi.org)

* Fri Oct 26 2012 Pall Sigurdsson <palli@opensource.is>
- fix block=smallheader boilerplates in misc module (palli@opensource.is)
- minor cosmetic fixes in status cgi (palli@opensource.is)
- Macro editing for hosts and services in objectbrowser (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Adding git reference to testing rpms (palli@opensource.is)
- Update README.md (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- Update README.md (palli-github@minor.is)
- size patch for select2 fields (palli@opensource.is)
- merged frontpage description with version check (palli@opensource.is)
- frontpage description updated (palli@opensource.is)
- Merge remote-tracking branch 'github/master' (tommi@tommi.org)
- Closes #56 - Implmented jsonp version checking (tommi@tommi.org)
- tomhom (palli@opensource.is)
- INSTALL removed in favour of README.md (palli@opensource.is)
- Nagios service reload button reintroduced (palli@opensource.is)
- pycharm inspection updates (palli@opensource.is)
- Nagios Service view now displays a notice if service needs to be reloaded
  (palli@opensource.is)
- Bugfix where sudo was removed from init script path if provided.
  (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Added select2 functionality (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- ensure_ascii set to False for simplejson (palli@opensource.is)
- Update README.md (palli-github@minor.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Improvements to objectbrowser/delete/ (palli@opensource.is)
- Fixes responsive design of ob->list->service shortname (tommi@tommi.org)
- Closes #75 - Removed hardcoded path for url resolver (tommi@tommi.org)
- Minor cosmetic patch (tommi@tommi.org)
- Merge remote-tracking branch 'github/master' (tommi@tommi.org)
- Closes #31 - Major rework of IDs to fix jump on location.hash change
  (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- status.html added (palli@opensource.is)
- exception handling broadened on objectbrowser views (palli@opensource.is)
- objectbrowser unicode strings converted to bytestrings before being passed to
  pynag (palli@opensource.is)
- Responsive - show service shortname on small devices (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Fixes to responsive ob list (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Various fixes related to get_effective_contactgroups and
  get_effective_hostgroups (palli@opensource.is)
- experimental status view added and settings bugfix (palli@opensource.is)
- Resize ob list working, implemented hiding column (tommi@tommi.org)
- Closes #61 - Implemented run_commands for okconfig/edithost (tommi@tommi.org)
- Typo in warning message regarding uncommitted changes (tommi@tommi.org)
- Fixed dismissal of notifications and failure handling (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Closes #72 - inconsistant labels on level="" (tommi@tommi.org)

* Thu Sep 06 2012 Pall Sigurdsson <palli@opensource.is> 1.1.1-2
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- reload_nagios button implemented (palli@opensource.is)
- Fixed multiple replace of adagios and ownership of files (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- added missing okconfig.conf (palli@opensource.is)
- Modified file permissions on installed files in spec (tommi@tommi.org)
- path fix in spec file (palli@opensource.is)
- Removed line height for tables, sticking with defaults (tommi@tommi.org)
- edithost redesigned, should be fully functional (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- template cleanup (palli@opensource.is)
- Notify user if selinux is active (Closes #24) (palli@opensource.is)
- help text improved for install_agent form (palli@opensource.is)
- Rest module now raises exception if format is invalid. (palli@opensource.is)
- Submit button added on edit_contact notification tab (palli@opensource.is)
- Reorganized top navigation items (palli@opensource.is)
- reload_nagios button implemented (palli@opensource.is)
- New notification system for notification area on top-right
  (palli@opensource.is)
- ObjectBrowser Add/Edit/Delete always visible when something is selected
  (tommi@tommi.org)
- bulk copy feature implemented (palli@opensource.is)
- Made click action more specific (tommi@tommi.org)
- Moved actions to top of objectbrowser from sidebar and added copy
  (tommi@tommi.org)
- Some more objectbrowser filter optimizations (tommi@tommi.org)
- javascript converted to coffee and tuned objectbrowser and toolbar
  (tommi@tommi.org)
- Pynag radiobuttons are now all have the same style (palli@opensource.is)
- experimental new look for forms (palli@opensource.is)
- Fixes for numerous usability issues in ObjectBrowser (tommi@tommi.org)
- Fixed mass select and datatables problems in Objectbrowser (tommi@tommi.org)
- README updated to include features and link to project page
  (palli@opensource.is)

* Sat Aug 18 2012 Pall Sigurdsson <palli@opensource.is> 1.1.0-2
- removed weird reference to unmangled version (palli@opensource.is)

* Fri Aug 17 2012 Pall Sigurdsson <palli@opensource.is> 1.1.0-1
- Merge remote-tracking branch 'github/master' (tommi@tommi.org)
- Fixed okconfig/edit_host (tommi@tommi.org)
- Update README.md (palli-github@minor.is)
- Added white glyphicons (tommi@tommi.org)
- Closes #12 New filtering  and select all method for objectbrowser
  (tommi@tommi.org)
- README updated to include features and link to project page
  (palli@opensource.is)
- README updated to include features and link to project page
  (palli@opensource.is)
- Fix tag mismatch in apache config file (palli@opensource.is)
- pythonpath no longer hardcoded in apache config file (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Closes #6 WSGI sitelib fix and added auth (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- error handling improved if wrong hostname specified (palli@opensource.is)
- Added background image in gimp format. (tommi@tommi.org)
- Test mockup of okconfig_/edit_host (palli@opensource.is)
- Error handling moved into main content (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Error handling for get_effective_command_line to catch invalid check_command
  references. (Closes #21) (palli@opensource.is)
- avoid saving objects if only multichoicefield order has changed. (Closes #18)
  (palli@opensource.is)
- link for view diff renamed to 'diff' (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- Added gimp file for background (tommi@tommi.org)
- * Monitor from main navigation now loads "nagios_url" * Delete button now
  accessable from sidebar for a single object * Effective check_command now
  displayed in sidebar * install_agent is now passwordfield
  (palli@opensource.is)
- Changed display size of objectbrowser list (tommi@tommi.org)
- New background which doesn't tile ugly (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (tommi@tommi.org)
- Removed scrolling on objectbrowser list (tommi@tommi.org)
- form/form fixed (palli@opensource.is)
- improved error handling in okconfig add* forms. Closes issue #16
  (palli@opensource.is)
- Fixed inverted condition for Force (tommi@tommi.org)
- Fixes invalid variable names from commit 220698125ce (tommi@tommi.org)
- removed deprecated remove log (palli@opensource.is)
- spec file rename of README and useradd adagios removed (palli@opensource.is)
- sorrry (palli@opensource.is)
- sorrry (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- added empty service as default in addservicetohost (palli@opensource.is)
- glyph icons added to tabs in list_object_types (palli@opensource.is)
- Merge remote-tracking branch 'github/master' (tommi@tommi.org)
- Closes #15 - Implemented service macro javascript (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- addservicetoHost form now successfully accepts common macros
  (palli@opensource.is)
- Closes #5 - Changed wsgi user to nagios from adagios (tommi@tommi.org)
- #15 - Updates javascript code for service macros (tommi@tommi.org)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- multichoice select now have a default empty value. multichoice selects are
  now refreshed on every page lookup (palli@opensource.is)
- Closes Issue #10 - Implemented global chosen on all select nodes
  (tommi@tommi.org)
- Catching of IOErrors in views.py (palli@opensource.is)
- add_service moved from objectbrowser to okconfig (palli@opensource.is)
- Objectbrowser fields bootstrap standardized (palli@opensource.is)
- various readme updates (this should close issue #9) (palli@opensource.is)
- various readme updates (palli@opensource.is)
- syntax fix (palli@opensource.is)
- Readme updated to md format (palli@opensource.is)
- gitlog added to menu under new working name object history
  (palli@opensource.is)
- Bulk delete implemented. (palli@opensource.is)
- /rest/pynag/copy_object implemented. (palli@opensource.is)
- get_objects helper docstring clarified for issue #15 (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- inline_help_text attribute added to pynagmultichoicefield. fixes issue #14
  (palli@opensource.is)
- notification_options are now different for host and service. Fixes issue #3
  (palli@opensource.is)
- gitlog box removed (palli@opensource.is)
- ObjectDefinition.get_id() changed from md5sum (palli@opensource.is)
- filename argument removed in set_maincfg_attribute (palli@opensource.is)
- "contact us" link changed to an email address (palli@opensource.is)
- Merge remote-tracking branch 'github/master' (tommi@tommi.org)
- Re-arranged objectbrowser list tabs (tommi@tommi.org)
- radiobuttons, now use all of PynagRadioWidget (palli@opensource.is)
- Merge branch 'master' of github.com:opinkerfi/adagios (palli@opensource.is)
- PynagRadioWidget now has an initial state (fixes issue #4)
  (palli@opensource.is)
- Added nagios.cfg save functionality. (tommi@opensource.is)
- New objectbrowser/nagios.cfg (tommi@opensource.is)
- Progress bar green and andded span11 to inputs (tommi@tommi.org)
- Fixed form placement on tabs in OB (tommi@tommi.org)
- Tab overflow fix and Django 1.3 compatibility (tommi@opensource.is)
- Added servicestate to top bar in edit service (tommi@opensource.is)
- Added progressbar for longer checks (tommi@tommi.org)
- run_check_command jquery'ized. Fixed bug with refresh. (tommi@opensource.is)
- Badly formatted html quote fixed (tommi@opensource.is)
- Run Check Command, fix javascript and formatting (tommi@tommi.org)
- fixed typo (palli@opensource.is)
- sidebar only shows geek edit if there is an object (palli@opensource.is)
- refactoring and bugfixes related to advanced_form (palli@opensource.is)
- prototype for new gitlog view using dulwich python module
  (palli@opensource.is)
- templates for every hosttype added bugfixes in pynagform
  (palli@opensource.is)
- footer block added (palli@opensource.is)
- fixed tab-spacing issues (palli@opensource.is)
- Error notification code moved from base to header.html (palli@opensource.is)
- exception clause to broad (palli@opensource.is)
- cleanup and minor refactoring of templates (palli@opensource.is)
- Merge branch 'master' of http://opensource.ok.is/git/adagios
  (palli@opensource.is)
- Started working on edit_configfile for nagios.cfg (tommi@tommi.org)
- Merge branch 'master' of http://opensource.ok.is/git/adagios
  (palli@opensource.is)
- Removed bootstrap-modal, not used (tommi@tommi.org)
- Merge branch 'master' of http://opensource.ok.is/git/adagios
  (palli@opensource.is)
- minor cleanup in config_health (palli@opensource.is)
- Fixed no right margin (tommi@tommi.org)
- More fixes to layout after mega merge (tommi@tommi.org)
- Fixes to newly added html files with bad URLs (tommi@tommi.org)
- Merge branch 'master' of https://opensource.ok.is/git/adagios
  (tommi@tommi.org)
- Major cleanup of media/ and converted to bootstrap fluid layout
  (tommi@opensource.is)
- Fixes after an unsuccessful merge (palli@opensource.is)
- Merge branch 'master' of http://opensource.ok.is/git/adagios
  (palli@opensource.is)
- Changed layout of run check plugin and added support for stderr
  (tommi@opensource.is)
- nagios_url added to template view. effective_parents now visible on page
  (palli@opensource.is)
- effective command_line reintroduced (palli@opensource.is)
- menubar updates (palli@opensource.is)
- sidebar extended to display related objects (palli@opensource.is)
- Relative URLs for usage through WSGI and subdirs enabled (tommi@tommi.org)
- Merge branch 'master' of http://opensource.ok.is/git/adagios
  (palli@opensource.is)
- Minor cosmetic changes (palli@opensource.is)
- Settings page reworked. (palli@opensource.is)
- okconfig sidebar moved from snippet to block sidebar in base_okconfig.html
  (palli@opensource.is)
- objectbrowser sidebar moved from snippet to block sidebar in
  base_objectbrowser.html (palli@opensource.is)
- titles on all pages fixed (palli@opensource.is)
- timeperiod support improved (and more) (palli@opensource.is)
- objectbrowser snippified (palli@opensource.is)
- Install instructions for rhel6 (palli@opensource.is)
- list of templates and groups is now refreshed every time a form is loaded
  (palli@opensource.is)
- Removed contact_us and put up links to adagios website (tommi@tommi.org)
- cleanup of print statements (palli@opensource.is)
- template cleanups related to new base2.html (palli@opensource.is)
- various pep8 fixes. forms.py cleanups (palli@opensource.is)
- Missing templates/snippets/sidebar.html added (palli@opensource.is)
- django.core.context_processors.tz removed (palli@opensource.is)
- Changes template to new base2.html template (palli@opensource.is)
- template name added to addhost form (palli@opensource.is)
- fixed evil brokenness (palli@opensource.is)
- Checked update on select visible (tommi@tommi.org)
- Added "Select Visible" to objectbrowser (tommi@opensource.is)
- Various fixes to css and javascript, pycharm corrections (tommi@tommi.org)
- Bulk edit enabled and bulk delete as well (tommi@opensource.is)
- Edit many enabled from objectbrowser (tommi@tommi.org)
- Added datatable to edit_many, fixed delete_many url (tommi@opensource.is)
- Default to bootstrap headers for datatables (tommi@opensource.is)
- Removed static URLs for url addobject and bulk functions (tommi@tommi.org)
- On demand loading of OB and # anchor bookmarkable (tommi@tommi.org)
- Added missing file from previous commit (tommi@tommi.org)
- Implemented active navigation item (tommi@tommi.org)
- Removed /misc/ from urls.py (tommi@tommi.org)
- setuptools files ignored (tommi@tommi.org)
- Merge branch 'master' of https://opensource.ok.is/git/adagios
  (tommi@tommi.org)
- Added default objectbrowser list length, 48 rows (tommi@tommi.org)
- cleanup of old unused templates (palli@opensource.is)
- deprecated configurator module moved (palli@opensource.is)
- Code cleanup, pycharm inspection cleanup (palli@opensource.is)
- helpers.py moved from configurator module to misc module
  (palli@opensource.is)
- dnslookup() cleanup (palli@opensource.is)
- Revoke all the evil that was inflicted on us in
  9f460665f5b7e305ef4ce524e805df050c002b01 (palli@opensource.is)
- geek_edit complete erronously redirected you to add new object page
  (palli@opensource.is)
- Cleanup and removed "run any module" feature. (tommi@tommi.org)
- Minor code cleanup (tommi@tommi.org)
- dnslookup now returns error on failure (tommi@tommi.org)
- Removed erroneous filter (tommi@tommi.org)
- missing delete_object.html added (palli@opensource.is)
- Merge branch 'master' of http://opensource.ok.is/git/adagios
  (palli@opensource.is)
- delete object support added (palli@opensource.is)
- Datatable id fixed and column ordering and filter (tommi@tommi.org)
- use, register and name fields hardcoded into pynagform (palli@opensource.is)
- Link changed for delete object (palli@opensource.is)
- Merge branch 'master' of https://opensource.ok.is/git/adagios
  (tommi@tommi.org)
- Added lookup of services within a template. (tommi@tommi.org)
- Removed unused code. (tommi@tommi.org)
- .idea settings file put to .gitignore (palli@opensource.is)
- choosehost template added (palli@opensource.is)
- boostrap style forms now have bootstrap tooltip like objectbrowser
  implemented previously (palli@opensource.is)
- PynagRadioWidget created to handle 0/1 attributes (palli@opensource.is)
- edit host templates feature polished and added to menu (palli@opensource.is)
- edit_many bugfixed and streamlined (palli@opensource.is)
- Made some tests with layout of 'use' inheritance (tommi@tommi.org)
- Make "Run Check Plugin" not display for templates (tommi@tommi.org)
- Fix top spacing on navigation for narrow browsers (tommi@tommi.org)
- Removed debug print statements (tommi@tommi.org)
- DNS resolve host_name in addhost and chosen form (tommi@tommi.org)
- Moved rest URLs from urls.py and re-fitted dnslookups in rest
  (tommi@tommi.org)
- Added dependencies file (tommi@tommi.org)
- Merge branch 'master' of http://opensource.ok.is/git/adagios
  (palli@opensource.is)
- bulk edit prototype put in (palli@opensource.is)
- forms updated to use a new snipped bootstrap_fields (palli@opensource.is)
- url updated for bulk edit (palli@opensource.is)
- help_text set on form fields in okconfig (palli@opensource.is)
- Merge branch 'master' of https://opensource.ok.is/git/adagios
  (tommi@tommi.org)
- Frontpage made nicer. (tommi@tommi.org)
- removed peculiar print statement (palli@opensource.is)
- Problem badge added, removed OB debug box, styling (tommi@tommi.org)
- ObjectBrowser now loads services first (tommi@tommi.org)
- Cleanup of javascript code (tommi@tommi.org)
- Added preloading of objects on startup (tommi@tommi.org)
- Added preloading of pynag objects on startup (tommi@tommi.org)
- view_parents and view_nagioscfg were previously renamed to edit_. Fixed
  (palli@opensource.is)
- Renamed view_ functions to edit_ (palli@opensource.is)
- Made error messages visible again. TODO: Change location
  (palli@opensource.is)
- support for adding new object via web interface (palli@opensource.is)
- url updated for adding new object (palli@opensource.is)
- Merge branch 'master' of https://opensource.ok.is/git/adagios
  (tommi@tommi.org)
- Autoindent and moved actions to the right (tommi@opensource.is)
- releasers.conf updated to include source tarballs (palli@opensource.is)
- Merge branch 'master' of https://opensource.ok.is/git/adagios
  (palli@opensource.is)
- releasers.conf updated and is now split into production and testing
  (palli@opensource.is)
- Autoindent and moved actions to the right (tommi@tommi.org)
- Javascript cleanup and rename to ob_ (tommi@opensource.is)
- bugfix: multichoice fields treated as charfields (palli@opensource.is)
- add complete form updated to new formfields look (palli@opensource.is)
- removed hardcoded path to nagios.cfg (palli@opensource.is)
- Merge branch 'master' of https://opensource.ok.is/git/adagios
  (tommi@tommi.org)
- Syntax fixes and cleanups from pycharm suggestions (tommi@tommi.org)
- test with new template boilerplates (palli@opensource.is)
- geek and advanced edit are now seperate functions in views.py. Template fixed
  for view_host and view_object. PynagForm now accepts parameter simple to turn
  every field into charfield (palli@opensource.is)
- Suggestion for new generic page boilerplate. Tommi please review
  (palli@opensource.is)
- Merge branch 'master' of http://opensource.ok.is/git/adagios
  (palli@opensource.is)
- url to advanced forms and geek edit forms updated (palli@opensource.is)
- Added bulk functionaility to object list. (tommi@tommi.org)
- Added initial Add HTML to the objectbrowser (tommi@tommi.org)
- Fixed tooltip bug when paging in datatables Various cleanups, duplicate
  definititions (tommi@tommi.org)
- Break up html and javascript for services (tommi@tommi.org)
- Styled Nagios iframe to fit a little better (tommi@tommi.org)
- Merge branch 'formfields' (tommi@tommi.org)
- Added pretty radio buttons on [0/1/undef] fields (tommi@tommi.org)
- Merge branch 'formfields' of https://opensource.ok.is/git/adagios into
  formfields (tommi@tommi.org)
- Newline formatting Unknown object ID error shown Run Check Plugin refresh now
  working (tommi@tommi.org)
- templates polished, fields updated (palli@opensource.is)
- menubar updated, nagios link added (palli@opensource.is)
- New Feature: Add single service to host (palli@opensource.is)
- Newly added features stuffed in the menubar (palli@opensource.is)
- fixed python spacing (palli@opensource.is)
- rpm package now requires Django (palli@opensource.is)
- Added refresh button to run plugin modal (tommi@tommi.org)
- Added first design of run check plugin (tommi@tommi.org)
- make sure cache is reloaded if manual edit has been made
  (palli@opensource.is)
- Parsers.config.errors now appears on the confighealth page
  (palli@opensource.is)
- .settings added to .gitignore (palli@opensource.is)
- Merge (palli@opensource.is)
- Merge (palli@opensource.is)
- service_description fixed in edittemplate.html (palli@opensource.is)
- Merge (palli@opensource.is)
- Merged plugin execution (palli@opensource.is)
- Revert "make sure cache is reloaded if manual edit has been made"
  (tommi@tommi.org)
- Revert "Parsers.config.errors now appears on the confighealth page"
  (tommi@tommi.org)
- Revert "form support for installing agent remotely" (tommi@tommi.org)
- Revert "Fixed broken merge" (tommi@tommi.org)
- Revert ".settings added to .gitignore" (tommi@tommi.org)
- Revert "Feature: run_check_command() feature added to pynag helpers"
  (tommi@tommi.org)
- Revert "kreb" (tommi@tommi.org)
- kreb (tommi@tommi.org)
- Feature: run_check_command() feature added to pynag helpers
  (palli@opensource.is)
- .settings added to .gitignore (palli@opensource.is)
- Fixed broken merge (tommi@tommi.org)
- form support for installing agent remotely (palli@opensource.is)
- Parsers.config.errors now appears on the confighealth page
  (palli@opensource.is)
- make sure cache is reloaded if manual edit has been made
  (palli@opensource.is)
- Manual edit to geekedit and finish service editor (tommi@tommi.org)
- make sure cache is reloaded if manual edit has been made
  (palli@opensource.is)
- form support for installing agent remotely (palli@opensource.is)
- TBS (tommi@tommi.org)
- Fixed bug where git comment included colon. (tommi@tommi.org)
- Parsers.config.errors now appears on the confighealth page
  (palli@opensource.is)
- .settings added to .gitignore (palli@opensource.is)
- Feature: run_check_command() feature added to pynag helpers
  (palli@opensource.is)
- BS (tommi@tommi.org)
- Revert "REST: added no client side caching" (tommi@tommi.org)
- BS shizzle (tommi@tommi.org)
- TB hostdetail (tommi@tommi.org)
- REST: added no client side caching (tommi@tommi.org)
- delete_object() helper method created (palli@opensource.is)
- TB changes (tommi@tommi.org)
- service_description fixed in edittemplate.html (palli@opensource.is)
- Feature: Edit of okconfig templates (palli@opensource.is)
- TB service form and chosen. Cleanups of unneeded code. (tommi@tommi.org)
- Breadcrumbs and object browser service view in TB (tommi@tommi.org)
- Enabled pagination in tables, performance increase (tommi@tommi.org)
- More DataTables optimizations (tommi@tommi.org)
- Fixed column width and sizing issues. Performance optimizations for
  datatables. (tommi@tommi.org)
- twitter bootstrap migration - object browser (tommi@tommi.org)
- More bulk changes to twitter bootstrap (tommi@tommi.org)
- Added contacts tab (tommi@tommi.org)
- ObjectBrowser ajaxified, multiple changes (tommi@tommi.org)
- Styling changes and added tabs (tommi@tommi.org)
- Merge branch 'formfields' of https://opensource.ok.is/git/adagios into
  formfields (tommi@tommi.org)
- CSS Style Changes (git log) view and added header to overview
  (tommi@tommi.org)
- delete_object() helper method created (palli@opensource.is)
- Reset djangopath to discovery (tommi@tommi.org)
- Better guessing for git directory (tommi@tommi.org)
- Added git log capability and changes to objectbrowser (tommi@tommi.org)
- Implementing twitter bootstrap framework (tommi@tommi.org)
- Removed old style.css (tommi@tommi.org)
- re-enabled okconfig/urls (palli@opensource.is)
- Changed href links to use template url tags for navigation (tommi@tommi.org)
- Moved from WSGI embedded to daemon with apache (tommi@tommi.org)

* Tue Mar 13 2012 Pall Sigurdsson <palli@opensource.is> 1.0.0-1
- tito releasers added (palli@opensource.is)
- copied wsgi configuration from fpaste.wsgi (palli@opensource.is)
- conf/ renamed to apache/ (palli@opensource.is)
- apache wsgi configuration added (palli@opensource.is)
- setup.py modified to take recursive copy of source directory
  (palli@opensource.is)
- manage.py no longer executable in site-lib (palli@opensource.is)

* Tue Mar 13 2012 Pall Sigurdsson <palli@opensource.is>
- tito releasers added (palli@opensource.is)
- copied wsgi configuration from fpaste.wsgi (palli@opensource.is)
- conf/ renamed to apache/ (palli@opensource.is)
- apache wsgi configuration added (palli@opensource.is)
- setup.py modified to take recursive copy of source directory
  (palli@opensource.is)
- manage.py no longer executable in site-lib (palli@opensource.is)

* Tue Mar 13 2012 Pall Sigurdsson <palli@opensource.is>
- copied wsgi configuration from fpaste.wsgi (palli@opensource.is)
- conf/ renamed to apache/ (palli@opensource.is)
- apache wsgi configuration added (palli@opensource.is)
- setup.py modified to take recursive copy of source directory
  (palli@opensource.is)
- manage.py no longer executable in site-lib (palli@opensource.is)

* Tue Mar 13 2012 Pall Sigurdsson <palli@opensource.is>
- copied wsgi configuration from fpaste.wsgi (palli@opensource.is)
- conf/ renamed to apache/ (palli@opensource.is)
- apache wsgi configuration added (palli@opensource.is)
- setup.py modified to take recursive copy of source directory
  (palli@opensource.is)
- manage.py no longer executable in site-lib (palli@opensource.is)

* Tue Mar 13 2012 Pall Sigurdsson <palli@opensource.is>
- copied wsgi configuration from fpaste.wsgi (palli@opensource.is)
- conf/ renamed to apache/ (palli@opensource.is)
- apache wsgi configuration added (palli@opensource.is)
- setup.py modified to take recursive copy of source directory
  (palli@opensource.is)
- manage.py no longer executable in site-lib (palli@opensource.is)

* Tue Mar 13 2012 Pall Sigurdsson <palli@opensource.is> 1.0-1
- new package built with tito

