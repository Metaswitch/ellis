Ellis Provisioning Server
=========================

This project contains the Clearwater provisioning server, named Ellis
after Ellis Island.  It provides a web GUI and underlying HTTP API for
user and line creation, number allocation, and configuration of iFCs
and call services.

Project Clearwater is an open-source IMS core, developed by [Metaswitch Networks](http://www.metaswitch.com) and released under the [GNU GPLv3](http://www.projectclearwater.org/download/license/). You can find more information about it on [our website](http://www.projectclearwater.org/) or [our wiki](https://github.com/Metaswitch/clearwater-docs/wiki).

Details
=======

Ellis contains the user database and the pool of numbers that can be
allocated. It does not contain per-line configuration - it stores all
this directly in Homestead and Homer, accessing them over their
defined HTTP APIs.

Ellis is mainly written in Python. It uses Tornado for HTTP and MySQL
as the underlying database. virtualenv is used to manage
dependencies. The build system creates a Debian package, but the code
can also be run directly.

Further info
------------

* [Install guide](http://@@@remote/installation)
* [Design guide](docs/design.md)
* [API guide](docs/api.md)
* [Development guide](docs/development.md)
* [Feature guide](docs/features.md)
* [Changelog](CHANGELOG.md)

