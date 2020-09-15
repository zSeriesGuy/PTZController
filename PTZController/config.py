import re
import logging
from configparser import ConfigParser


FILENAME = "PTZController.conf"


class Config(ConfigParser):
    """ Wraps access to particular values in a config file """

    def __init__(self, config_file):
        """ Initialize the config with values from a file """
        super().__init__()
        self._config_file = config_file
        self.read(self._config_file)
