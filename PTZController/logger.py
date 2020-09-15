
from logging import handlers

import logging
import os
import sys
import threading
import traceback


# These settings are for file logging only
FILENAME = "PTZController.log"
MAX_SIZE = 5000000  # 5 MB
MAX_FILES = 5


# Main logger
FORMAT = '%(asctime)s - %(levelname)-7s :: %(threadName)-23s : %(message)s'
FORMAT_DATE = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(format=FORMAT, datefmt=FORMAT_DATE)
logger = logging.getLogger('PTZController')



def initLogger(console=False, log_dir=False, verbose=False):
    """
    Setup logging. Three log handlers are added:

    * RotatingFileHandler: for the file main log
    * LogListHandler: for Web UI
    * StreamHandler: for console (if console)

    Console logging is only enabled if console is set to True. This method can
    be invoked multiple times, during different stages.
    """

    # Close and remove old handlers. This is required to reinit the loggers
    # at runtime
    for handler in logger.handlers[:]:
        # Just make sure it is cleaned up.
        if isinstance(handler, handlers.RotatingFileHandler):
            handler.close()
        elif isinstance(handler, logging.StreamHandler):
            handler.flush()

        logger.removeHandler(handler)

    # Configure the logger to accept all messages
    logger.propagate = False
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Setup file logger
    if log_dir:
        file_formatter = logging.Formatter(FORMAT, FORMAT_DATE)

        # Main Tautulli logger
        filename = os.path.join(log_dir, FILENAME)
        file_handler = handlers.RotatingFileHandler(filename, maxBytes=MAX_SIZE, backupCount=MAX_FILES)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        logger.addHandler(file_handler)

    # Setup console logger
    if console:
        console_formatter = logging.Formatter(FORMAT, FORMAT_DATE)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)

        logger.addHandler(console_handler)


    # Install exception hooks
    initHooks()


def initHooks(global_exceptions=True, thread_exceptions=True, pass_original=True):
    """
    This method installs exception catching mechanisms. Any exception caught
    will pass through the exception hook, and will be logged to the logger as
    an error. Additionally, a traceback is provided.

    This is very useful for crashing threads and any other bugs, that may not
    be exposed when running as daemon.

    The default exception hook is still considered, if pass_original is True.
    """

    def excepthook(*exception_info):
        # We should always catch this to prevent loops!
        try:
            message = "".join(traceback.format_exception(*exception_info))
            logger.error("Uncaught exception: %s", message)
        except:
            pass

        # Original excepthook
        if pass_original:
            sys.__excepthook__(*exception_info)

    # Global exception hook
    if global_exceptions:
        sys.excepthook = excepthook

    # Thread exception hook
    if thread_exceptions:
        old_init = threading.Thread.__init__

        def new_init(self, *args, **kwargs):
            old_init(self, *args, **kwargs)
            old_run = self.run

            def new_run(*args, **kwargs):
                try:
                    old_run(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    excepthook(*sys.exc_info())
            self.run = new_run

        # Monkey patch the run() by monkey patching the __init__ method
        threading.Thread.__init__ = new_init


def shutdown():
    logging.shutdown()


# Expose logger methods
# Main Tautulli logger
info = logger.info
warn = logger.warn
error = logger.error
debug = logger.debug
warning = logger.warning
exception = logger.exception
