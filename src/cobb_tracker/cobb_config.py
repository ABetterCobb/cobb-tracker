import configparser
import sys
import os
from pathlib import Path

class cobb_config():
    def __init__(
            self,
            config_dir = os.path.join(Path(os.path.expanduser('~')),
                                      ".config",
                                      "cobb_tracker"),
            data_dir = os.path.join(Path(os.path.expanduser('~')),
                                      ".local",
                                      "share")
            ):
        self.DEFAULT_CONFIG_DIR=config_dir
        self.DEFAULT_DATA_DIR=data_dir
        self.DEFAULT_CONFIG_FILE = os.path.join(f"{self.DEFAULT_CONFIG_DIR}","config.ini")
        self.config = configparser.ConfigParser()

        if not os.path.exists(self.DEFAULT_CONFIG_DIR):
            os.mkdir(self.DEFAULT_CONFIG_DIR)

        if not os.path.exists(self.DEFAULT_CONFIG_FILE):
            self.config['directories'] = {
                'database_dir': f"{os.path.join(self.DEFAULT_DATA_DIR, 'db')}",
                'minutes_dir': f"{os.path.join(self.DEFAULT_DATA_DIR, 'minutes')}"
                }

            if not os.path.exists(self.config['directories']['database_dir']):
                os.mkdir(self.config['directories']['database_dir'])

            with open(os.path.join(self.DEFAULT_CONFIG_DIR, "config.ini"), 'w') as config_file:
                self.config.write(config_file)

        elif os.path.exists(self.DEFAULT_CONFIG_FILE):
            self.config.read(self.DEFAULT_CONFIG_FILE) 
            if len(self.config.sections()) == 0:
                print("Error: Configuration file incorrect")
                sys.exit()
            elif len(self.config.sections()) > 0:
                try:
                    self.config.get('directories','database_dir')
                    self.config.get('directories','minutes_dir')
                except Exception as e:
                    print(f"Error: {e}, is your configuration correctly formatted?")
                    sys.exit()
            
    def get_config(self, section: str, key: str) -> str:
        return self.config[section][key]
