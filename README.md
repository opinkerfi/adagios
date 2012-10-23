About
=====
Adagios is a web based Nagios configuration interface build to be simple and intuitive in design, exposing less of the clutter under the hood of nagios.

Design principals
==================
  - No database backend (work with current configuration files and extremely gentle when modifying them)
  - Make common tasks as simple as possible (monitoring a new windows or oracle host should be as easy as 1,2,3)
  - Be a value-add for both novices and nagios experts
  - Assist Nagios admins in keeping configuration files clean and simple

Features
========
  - Full view/edit of hosts,services, etc
  - Tons of pre-bundled plugins and configuration templates
  - Network scan
  - Remote installation of linux/windows agents
  - Full audit of any changes made

Components
==========
  - OKconfig - A robust plugin collection with preconfigured nagios template configuration files
  - Pynag - Nagios Configuration Parser
  - Django - Python web framework
  - Bootstrap - For user interface

Live Demo
=========
http://adagios.opensource.is/

Project website
=========
http://opensource.is/adagios

Source Code
===========

	git clone http://github.com/opinkerfi/adagios.git

Install Instructions
====================
These installation instructions apply for rhel6. If running Fedora, please modify yum repos as needed.

For RHEL6/CentOS6 you must install epel yum repository (fedora users skip this step):

	rpm -Uvh http://download.fedoraproject.org/pub/epel/6/$HOSTTYPE/epel-release-6-7.noarch.rpm

Next step is to install OK yum repository:

	rpm -Uhv http://opensource.is/repo/ok-release-10-1.el6.noarch.rpm

Install needed packages:

	yum --enablerepo=ok-testing install -y nagios okconfig git adagios

Adagios will not work unless you turn off selinux:

	sed -i "s/SELINUX=enforcing/SELINUX=permissive/" /etc/sysconfig/selinux
	setenforce 0

If you plan to access adagios through apache, make sure it is started:

	service httpd restart
	chkconfig httpd on


Same goes for nagios, start it if it is ready

	service nagios restart
	chkconfig nagios on
	
It is strongly recommended that you create a git repository in /etc/nagios/ and additionally give ownership of
everything in /etc/nagios to the nagios user.

	cd /etc/nagios/
	git init
	git add .
	git commit -a -m "Initial commit"
	chown -R nagios /etc/nagios/* /etc/nagios/.git

Congratulations! You are now ready to browse through adagios through http://$servername/adagios/. By default it
will use same authentication mechanism as nagios. (on rhel default is nagiosadmin/nagiosadmin and can be 
changed in /etc/nagios/passwd)

Communicate with us
===================

Mailing list: http://groups.google.com/group/adagios

IRC: #adagios on irc.freenode.net
