import configparser
import os
from pathlib import Path

class cobb_config():
    def __init__(
            self,
            config_dir = os.path.join(Path(os.path.expanduser('~')),
                                      ".config",
                                      "cobb_tracker")
            ):

        self.DEFAULT_CONFIG_DIR=config_dir
        self.DEFAULT_CONFIG_FILE = os.path.join(f"{self.DEFAULT_CONFIG_DIR}","config.ini")
        if not os.path.exists(self.DEFAULT_CONFIG_DIR):
            os.mkdir(self.DEFAULT_CONFIG_DIR)

        self.config = configparser.ConfigParser()
        self.config['directories'] = {
                'database_dir': f"{os.path.join(self.DEFAULT_CONFIG_DIR, 'db')}",
                'minutes_dir': f"{os.path.join(self.DEFAULT_CONFIG_DIR, 'minutes')}"
                }

        if not os.path.exists(self.config['directories']['database_dir']):
            os.mkdir(self.config['directories']['database_dir'])

        if not os.path.exists(self.DEFAULT_CONFIG_FILE):
            with open(os.path.join(self.DEFAULT_CONFIG_DIR, "config.ini"), 'w') as config_file:
                config.write(config_file)

    def get_config(self, section: str, key: str) -> str:
        return self.config[section][key]
