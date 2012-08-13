ABOUT
=====
Adagios is a web based Nagios configuration interface build to be simple and intuitive in design, exposing less of the clutter under the hood of nagios.

Design principals:
==================
  - No database backend (work with current configuration files and extremely gentle when modifying them)
  - Make common tasks as simple as possible (monitoring a new windows or oracle host should be as easy as 1,2,3)
  - Be a value-add for both novices and nagios experts
  - Assist Nagios admins in keeping configuration files clean and simple

Live Demo
=========
http://adagios.opensource.is/

INSTALL INSTRUCTIONS
====================
These installation instructions apply for rhel6. If running Fedora, please modify yum repos as needed.

For RHEL6 you must install epel yum repository (fedora users skip this step):

	rpm -Uvh http://download.fedoraproject.org/pub/epel/6/$HOSTTYPE/epel-release-6-7.noarch.rpm

Next step is to install OK yum repository:

	rpm -Uhv http://opensource.is/repo/ok-release-10-1.el6.noarch.rpm

Install needed packages:

	yum install -y nagios okconfig git adagios

Adagios will not work unless you turn off selinux:

	setenforce 0

If you plan to access adagios through apache, make sure it is started:

	service httpd restart

Now you should be able to access adagios through http://<host_name>/adagios/
