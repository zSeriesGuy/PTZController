#!/bin/sh
''''which python    >/dev/null 2>&1 && exec python    "$0" "$@" # '''
''''which python3   >/dev/null 2>&1 && exec python3   "$0" "$@" # '''
''''exec echo "Error: Python not found!" # '''

# -*- coding: utf-8 -*-


import os
import sys
import locale
import tzlocal
import pytz
import datetime
import argparse
import signal
import time

# Ensure lib added to path, before any other imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

import PTZController
from PTZController import PTZController, logger


def main():
    """
    PTZController application entry point.
    Parses arguments, setups encoding and initializes the application.
    """

    if hasattr(sys, 'frozen'):
        PTZController.FULL_PATH = os.path.abspath(sys.executable)
    else:
        PTZController.FULL_PATH = os.path.abspath(__file__)

    PTZController.PROG_DIR = os.path.dirname(PTZController.FULL_PATH)

    try:
        locale.setlocale(locale.LC_ALL, "")
        PTZController.SYS_LANGUAGE, PTZController.SYS_ENCODING = locale.getlocale()
    except (locale.Error, IOError):
        pass

    if not PTZController.SYS_ENCODING or PTZController.SYS_ENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        PTZController.SYS_ENCODING = 'UTF-8'

    try:
        PTZController.SYS_TIMEZONE = str(tzlocal.get_localzone())
        PTZController.SYS_UTC_OFFSET = datetime.datetime.now(pytz.timezone(PTZController.SYS_TIMEZONE)).strftime('%z')
    except (pytz.UnknownTimeZoneError, LookupError, ValueError) as e:
        print("Could not determine system timezone: %s" % e)
        PTZController.SYS_TIMEZONE = 'Unknown'
        PTZController.SYS_UTC_OFFSET = '+0000'

    # Set up and gather command line arguments
    parser = argparse.ArgumentParser(
        description='A Python-based controller for PTZ cameras.')

    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Increase console logging verbosity')
    parser.add_argument(
        '-q', '--quiet', action='store_true', help='Turn off console logging')
    parser.add_argument(
        '-d', '--daemon', action='store_true', help='Run as a daemon')
    parser.add_argument(
        '-p', '--port', type=int, help='Force PTZController to run on a specified port')
    parser.add_argument(
        '--config', help='Specify a config file to use')
    parser.add_argument(
        '--nolaunch', action='store_true', help='Prevent browser from launching on startup')
    parser.add_argument(
        '--pidfile', help='Create a pid file (only relevant when running as a daemon)')
    parser.add_argument(
        '--nofork', action='store_true', help='Start PTZController as a service, do not fork when restarting')

    args = parser.parse_args()

    if not args.verbose:
        args.verbose = True
    if not args.quiet:
        args.quiet = False

    # Do an intial setup of the logger.
    logger.initLogger(console=not args.quiet, log_dir=False, verbose=args.verbose)

    ptzController = PTZController(args)

    # Register signals, such as CTRL + C
    def sig_handler(signum=None, frame=None):
        if signum is not None:
            print("Signal %i caught, saving and exiting..." % signum)
            if ptzController:
                ptzController.SIGNAL = 'shutdown'

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    # Wait endlessy for a signal to happen
    while True:
        if not ptzController.SIGNAL:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                ptzController.SIGNAL = 'shutdown'
        else:
            print('Received signal: %s' % ptzController.SIGNAL)

            if ptzController.SIGNAL == 'shutdown':
                ptzController.shutdown()
                os._exit(0)
            elif ptzController.SIGNAL == 'restart':
                ptzController.shutdown(restart=True)
            elif ptzController.SIGNAL == 'checkout':
                ptzController.shutdown(restart=True, checkout=True)
            else:
                ptzController.shutdown(restart=True, update=True)

            ptzController.SIGNAL = None


# Call main()
if __name__ == "__main__":
    main()
