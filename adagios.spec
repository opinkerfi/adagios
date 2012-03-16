%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%define name adagios
%define version 1.0.0
%define unmangled_version 1.0.0
%define release 1

Name: %{name}
Version: %{version}
Release: %{release}%{?dist}
Summary: Adagios web-configuration front-end to nagios 
Group: Applications/Internet
License: GPLv2+
URL: https://adagios.opensource.is/
Source0: https://adagios.opensource.is/releases/%{name}-%{unmangled_version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Prefix: %{_prefix}

BuildRequires: python2-devel
BuildRequires: python-setuptools

Requires: pynag >= 0.4.0
Requires: httpd mod_wsgi Django

%description
Adagios is a web based Nagios configuration interface build to be simple and intuitive in design, exposing less of the clutter under the hood of nagios. 

%prep
%setup -qn %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
chmod a+x %{buildroot}%{python_sitelib}/adagios/manage.py
sed -i 's|#python_path#|%{python_sitelib}|g' %{buildroot}%{python_sitelib}/adagios/apache/adagios.conf
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d/
mv %{buildroot}%{python_sitelib}/adagios/apache/adagios.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/adagios.conf

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc README 
%{python_sitelib}/*
%config(noreplace) %{_sysconfdir}/httpd/conf.d/adagios.conf

%changelog

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

