#!/bin/sh

# @file ellis.init.d
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

### BEGIN INIT INFO
# Provides:          ellis
# Required-Start:    $network $local_fs
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: ellis
# Description:       ellis, the user/number management interface
### END INIT INFO

# PATH should only include /usr/* if it runs after the mountnfs.sh script
PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC=ellis       # Introduce a short description here
NAME=ellis       # Introduce the short server's name here
USER=ellis       # Username to run as
DAEMON=/usr/share/clearwater/ellis/env/bin/python # Introduce the server's location here
DAEMON_ARGS="-m metaswitch.ellis.main" # Arguments to run the daemon with
DAEMON_DIR=/usr/share/clearwater/ellis/
PIDFILE=/var/run/$NAME/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME

# Exit if the package is not installed
[ -x $DAEMON ] || exit 0

# Read configuration variable file if it is present
[ -r /etc/default/$NAME ] && . /etc/default/$NAME

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.0-6) to ensure that this file is present.
. /lib/lsb/init-functions

#
# Determine runtime settings
#
get_settings()
{
  log_level=2

  . /etc/clearwater/config
}

#
# Function to get the arguments to pass to the process
#
get_daemon_args()
{
  # Get the settings
  get_settings

  DAEMON_ARGS="$DAEMON_ARGS --log-level $log_level"
}
#
# Function that starts the daemon/service
#
do_start()
{
  # Return
  #   0 if daemon has been started
  #   1 if daemon was already running
  #   2 if daemon could not be started

  install -m 755 -o $USER -g root -d /var/run/$NAME && chown -R $NAME /var/run/$NAME

  start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON --test > /dev/null \
    || return 1
  get_daemon_args
  start-stop-daemon --start --quiet --chdir $DAEMON_DIR --chuid $USER --pidfile $PIDFILE --exec $DAEMON -- \
    $DAEMON_ARGS --background \
    || return 2
}

#
# Function that stops the daemon/service
#
do_stop()
{
  # Return
  #   0 if daemon has been stopped
  #   1 if daemon was already stopped
  #   2 if daemon could not be stopped
  #   other if a failure occurred

  # Kill the parent Python process by specifying a pidfile. We use prctl's SET_PSIGNAL feature to
  # make that automatically send SIGTERM to the children.
  start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 --pidfile $PIDFILE --user $USER --exec $DAEMON
  RETVAL="$?"
  [ "$RETVAL" = 2 ] && return 2
  return "$RETVAL"
}

#
# Function that runs the daemon/service in the foreground
#
do_run()
{
  install -m 755 -o $USER -g root -d /var/run/$NAME && chown -R $NAME /var/run/$NAME
  start-stop-daemon --start --quiet --chdir $DAEMON_DIR --chuid $USER --exec $DAEMON -- $DAEMON_ARGS \
    || return 2
}

#
# Function that aborts the daemon/service
#
# This is very similar to do_stop except it sends SIGUSR1 to dump a stack.
#
do_abort()
{
  # Return
  #   0 if daemon has been stopped
  #   1 if daemon was already stopped
  #   2 if daemon could not be stopped
  #   other if a failure occurred
  start-stop-daemon --stop --quiet --retry=USR1/5/TERM/30/KILL/5 --pidfile $PIDFILE --user $USER --exec $DAEMON
  RETVAL="$?"
  # If the abort failed, it may be because the PID in PIDFILE doesn't match the right process
  # In this window condition, we may not recover, so remove the PIDFILE to get it running
  if [ $RETVAL != 0 ]; then
    rm -f $PIDFILE
  fi
  return "$RETVAL"
}

# There should only be at most one ellis process, and it should be the one in /var/run/ellis.pid.
# Sanity check this, and kill and log any leaked ones.
if [ -f $PIDFILE ] ; then
  leaked_pids=$(pgrep -f "^$DAEMON" | grep -v $(cat $PIDFILE))
else
  leaked_pids=$(pgrep -f "^$DAEMON")
fi
if [ -n "$leaked_pids" ] ; then
  for pid in $leaked_pids ; do
    logger -p daemon.error -t $NAME Found leaked ellis $pid \(correct is $(cat $PIDFILE)\) - killing $pid
    kill -9 $pid
  done
fi

case "$1" in
  start)
    [ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC " "$NAME"
    do_start
    case "$?" in
      0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
      2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
    esac
    ;;
  stop)
    [ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME"
    do_stop
    case "$?" in
      0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
      2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
    esac
    ;;
  run)
    [ "$VERBOSE" != no ] && log_daemon_msg "Running $DESC" "$NAME"
    do_run
    case "$?" in
      0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
    2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
    esac
    ;;
  status)
    status_of_proc "$DAEMON" "$NAME" && exit 0 || exit $?
    ;;
  #reload|force-reload)
    #
    # If do_reload() is not implemented then leave this commented out
    # and leave 'force-reload' as an alias for 'restart'.
    #
    #log_daemon_msg "Reloading $DESC" "$NAME"
    #do_reload
    #log_end_msg $?
    #;;
  restart|force-reload)
    #
    # If the "reload" option is implemented then remove the
    # 'force-reload' alias
    #
    log_daemon_msg "Restarting $DESC" "$NAME"
    do_stop
    case "$?" in
      0|1)
        do_start
        case "$?" in
          0) log_end_msg 0 ;;
          1) log_end_msg 1 ;; # Old process is still running
          *) log_end_msg 1 ;; # Failed to start
        esac
        ;;
      *)
        # Failed to stop
        log_end_msg 1
      ;;
    esac
    ;;
  abort)
    log_daemon_msg "Aborting $DESC" "$NAME"
    do_abort
    ;;
  abort-restart)
    log_daemon_msg "Abort-Restarting $DESC" "$NAME"
    do_abort
    case "$?" in
      0|1)
        do_start
        case "$?" in
          0) log_end_msg 0 ;;
          1) log_end_msg 1 ;; # Old process is still running
          *) log_end_msg 1 ;; # Failed to start
        esac
        ;;
      *)
      # Failed to stop
      log_end_msg 1
      ;;
    esac
    ;;
  *)
    echo "Usage: $SCRIPTNAME {start|stop|run|status|restart|force-reload|abort|abort-restart}" >&2
    exit 3
    ;;
esac

:
