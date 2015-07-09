Ellis - Development Guide
=========================

This document describes how to build and test Ellis.

Dependencies
============

To build Ellis, you need to install a number of packages. On Ubuntu,
the following commands install them all - similar commands should
work on other systems.

1. Update the package list.

    ```
    sudo apt-get update
    ```

2. Install the packages you need.

    ```
    sudo apt-get install ntp build-essential autoconf scons pkg-config libtool libcloog-ppl0 dpkg-dev devscripts dh-make python-setuptools python-virtualenv python-dev libcurl4-openssl-dev libmysqlclient-dev libgmp10 libgmp-dev libc-ares-dev ncurses-dev libxml2-dev libxslt1-dev libzmq3-dev
    ```

The build has been tested on Ubuntu 14.04, with Python 2.7.3. Other
environments should work but have not been tested.

Code
====

The code consists of the `ellis` repository and its submodules as
defined in `.gitmodules`:

* `python-common`, which appears at `common/`, contains Python utility
  code shared between the Python components of Clearwater.
* `clearwater-build-infra`, which appears at `build-infra/`, contains
  support for building Debian packages which is shared between all
  components of Clearwater.

If you are using git, you can check out the Ellis codebase with

    git clone --recursive git@github.com:Metaswitch/ellis.git

This accesses the repository over SSH on Github, and will not work unless you have a Github account and registered SSH key. If you do not have both of these, you will need to configure Git to read over HTTPS instead:

    git config --global url."https://github.com/".insteadOf git@github.com:
    git clone --recursive git@github.com:Metaswitch/ellis.git 

Building
========

The build requires GNU Make. It uses virtualenv and buildout to create
a virtual Python environment in `_env/` containing only the required
dependencies, at the expected versions.

As part of the environment, a special python executable is generated in the
`bin/` subdirectory.  That executable is preconfigured to use the correct
`PYTHONPATH` to pick up the dependencies in the `_env/` directory.

To build the code, you will need to make the environment, then run the
set up scripts. This is done by the following commands (run from the top level
Ellis directory):

    make env
    _env/bin/easy_install --allow-hosts=None -f eggs/ eggs/*.egg
    _env/bin/python setup.py install
    cd common
    ../_env/bin/python setup.py install

To build the Debian package, type `make deb` (or `make deb-only` if
you have already built the code). This creates a Debian package in
`${HOME}/www/repo/binary/` which you can install with `dpkg -i`.

Setting up the database
=======================

The database is configured automatically if you are using the Debian
package install.

Ellis expects access to a MySQL database. The credentials can be
configured in `local_settings.py` (see comments in `settings.py` for
details). The database is initialised by invoking

    mysql < src/metaswitch/ellis/data/schema.sql
    mysql < src/metaswitch/ellis/data/apply_db_updates.sql

It is safe to apply these to an existing database. In fact, this is
how we upgrade the database.

The database is called `ellis`, so you can examine it as follows:

    sudo mysql
    use ellis;
    SELECT * FROM users WHERE email = 'alice@example.org';
    SELECT * FROM numbers WHERE number = 'sip:6505550001@example.org';

Configuring
===========

Ellis reads its configuration on startup from
`src/metaswitch/ellis/local_settings.py` and
`src/metaswitch/ellis/settings.py`. Per-host or per-deployment changes
should be made to `local_settings.py`, because these override the
global settings in `settings.py`.

The Debian package installation reads the Clearwater configuration
file at `/etc/clearwater/config` and transcribes the necessary
information into the Ellis local settings file.

Available numbers configuration
-------------------------------

The available numbers (from which new telephone numbers are assigned)
are stored in the database. The range of available numbers can be
initialized or updated using the [`create_numbers.py`
tool](create-numbers.md).


If you are installing manually or via Debian package you must invoke
this tool yourself. The Chef installation invokes this automatically
as part of the `ellis` recipe. It configures 100 local and 10 PSTN
numbers.

Email configuration
-------------------

If you want Ellis to be able to send emails to users who have
forgotten their password, you need to set up email.  To do this, Ellis
needs access to an [SMTP
smarthost](http://en.wikipedia.org/wiki/Smart_host). To avoid being
blacklisted, Ellis limits the rate of emails it sends, throttling any
excess. Replies and bounces are directed to a configured email
address.

Ellis has been tested with [Amazon SES](http://aws.amazon.com/ses/) -
see [instructions](smtp-aws.md) - but it should work with any SMTP
service, such as the SMTP server provided by your ISP or hosting
provider. The necessary settings are described in `settings.py` under
`SMTP_*` and `EMAIL_RECOVERY_*`. These include the name of the SMTP
server, the username and password to use with it, and whether or not
to use TLS. These should be configured in `local_settings.py`.

Running
=======

If you are using the Debian package, installing it will install the
usual init.d script at `/etc/init.d/ellis`, along with a Monit script
which starts it on installation and boot and restarts it if it stops.

Ellis is installed to `/usr/share/clearwater/ellis/`.

Startup logs (from Monit) are written to `/var/log/monit.log` and
`/var/log/syslog`.

Ellis logs are written to `/var/log/ellis/`. The logging level is set
to INFO by default. To also view DEBUG logs add the following to 
`local_settings.py`

    LOG_LEVEL = logging.DEBUG
    
To run the server as part of development use:

    make run

Testing
=======

This project has unit tests and code coverage. Unit tests are in
`src/metaswitch/ellis/test/`, parallel to the packages being tested,
e.g., the tests for `src/metaswitch/ellis/api/` are in
`src/metaswitch/ellis/test/api/`.

To run the unit tests, do:

    make test

To run coverage, do:

    make coverage

You should aim for 100% coverage on newly-written code. At the very
least, you shouldn't reduce the coverage level when adding new code.

Files
=====

* `src/` contains the source code for the Ellis application.
* `web-content/` contains the HTML, Javascript, CSS, etc files for the
  Ellis web GUI.
* `build-infra/` and `common/` are submodules, described above.
* `scripts/` contains scripts intended for manual or cron use.
* `docs/` contains this documentation.
* `backup/` contains the Ellis backup system.
* `debian/` and `root/`, as well as the repository root, contain files
  used for building the install package.
* The remaining directories are mostly related to Python packaging.

