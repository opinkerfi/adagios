About
=====
Adagios is a web based Nagios configuration interface built to be simple and intuitive in design, exposing less of the clutter under the hood of nagios. Additionally adagios has a rest interface for both status and configuration data as well a feature complete status interface that can be used as an alternative to nagios web interface.

Project website is at http://adagios.org

Live Demo
=========
http://demo.adagios.org/

Features
========
  - Full view/edit of hosts,services, etc
  - Tons of pre-bundled plugins and configuration templates
  - Network scan
  - Remote installation of linux/windows agents
  - Modern Status view as an alternative to default nagios web interface
  - Rest interface for status of hosts/services
  - Rest interface for viewing and modifying configuration
  - Full audit of any changes made

Design principles
==================
  - Useful for both novices and nagios experts
  - No database backend
  - Make common operational tasks as easy as possible
  - Assist Nagios admins in keeping configuration files clean and simple

Components
==========
  - Pynag - Nagios Configuration Parser
  - OKconfig - A robust plugin collection with preconfigured nagios template configuration files
  - PNP4Nagios - For Graphing Performance data
  - MK Livestatus - Broker module for nagios for high performance status information


Install Instructions
====================

Adagios has packages for most recent versions of redhat/fedora and debian/ubuntu.

Install takes about 5 minutes following our [Install Guide](https://github.com/opinkerfi/adagios/wiki/Install-guide)


Translations
============

  - handled by gettext, and stored in adagios/locale/
  - .po files are editable with standart text editors or po-specific ones
  - to add a language, run 'mkdir adagios/locale/<language-code>',
    e.g. mkdir adagios/locale/de for German
  - to create/update/compile .po files, run 'make trad'


Support us
===================

So you think the project is helping you or your company and you want to help us back?

Great! There are many ways you can support the project by contributing your time, talent and money.

See http://adagios.org/support.html for more information.


Contact us
===================
If you need any help with getting adagios to work, feel free to open up an issue on github issue tracker. If you want to chat you can contact us on:

  - Bug reports, feature requests: https://github.com/opinkerfi/adagios/issues
  - Mailing list: http://groups.google.com/group/adagios
  - IRC: #adagios on irc.freenode.net


License
=======
GNU AFFERO GENERAL PUBLIC LICENSE Version 3

The GNU Affero General Public License is a free, copyleft license for
software and other kinds of works, specifically designed to ensure
cooperation with the community in the case of network server software.


