%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%define name adagios
%define release 2

Name: adagios
Version: 1.1.0
Release: %{release}%{?dist}
Summary: Adagios web-configuration front-end to nagios 
Group: Applications/Internet
License: GPLv2+
URL: https://adagios.opensource.is/
Source0: https://adagios.opensource.is/releases/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Prefix: %{_prefix}

BuildRequires: python2-devel
BuildRequires: python-setuptools

Requires: pynag >= 0.4.5
Requires: httpd
Requires: mod_wsgi
Requires: Django
Requires: sudo

%description
Adagios is a web based Nagios configuration interface build to be simple and intuitive in design, exposing less of the clutter under the hood of nagios. 

%prep
%setup -qn %{name}-%{version} -n %{name}-%{version}
sed -i "s/__version__=.*/__version__='%{version}'/" adagios/__init__.py

%build
python setup.py build
sed "s/python2.7/python%{python_version}/" -i adagios/apache/adagios.conf

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
#chmod a+x %{buildroot}%{python_sitelib}/adagios/manage.py
sed -i 's|/usr/lib/python2.7/site-packages|%{python_sitelib}|g' %{buildroot}%{python_sitelib}/adagios/apache/adagios.conf
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d/
install -m644 %{buildroot}%{python_sitelib}/adagios/apache/adagios.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/adagios.conf

mkdir -p %{buildroot}%{_sysconfdir}/adagios/conf.d/
install -o nagios -m644 %{buildroot}%{python_sitelib}/adagios/etc/adagios/adagios.conf %{buildroot}%{_sysconfdir}/adagios/
install -o nagios -m644 %{buildroot}%{python_sitelib}/adagios/etc/adagios/conf.d/okconfig.conf %{buildroot}%{_sysconfdir}/adagios/conf.d/

mkdir -p %{buildroot}%{_sysconfdir}/sudoers.d/
install -m0440 %{buildroot}%{python_sitelib}/adagios/etc/sudoers.d/adagios %{buildroot}%{_sysconfdir}/sudoers.d/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc README.md 
%{python_sitelib}/*
%config(noreplace) %{_sysconfdir}/httpd/conf.d/adagios.conf
%config(noreplace) %{_sysconfdir}/adagios/adagios.conf
%config(noreplace) %{_sysconfdir}/sudoers.d/adagios

%changelog
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


* Mon Aug 10 2011 Clint Savage <herlo@fedoraproject.org> 0.2-1
- Cleaned up pathing and config files

* Mon Apr 11 2011 Clint Savage <herlo@fedoraproject.org> 0.1-3
- Added dist macro to release line.

* Mon Mar 07 2011 Clint Savage <herlo@fedoraproject.org> 0.1-2
- Fixed rpmlint errors and warnings.

* Tue Feb 08 2011 Clint Savage <herlo@fedoraproject.org> 0.1-1
- Initial package build

