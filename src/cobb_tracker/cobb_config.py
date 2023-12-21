import configparser
import sys
import os
from pathlib import Path

class CobbConfig():
    def __init__(
            self,
            config_dir = Path.home().joinpath(".config","cobb_tracker"),
            data_dir = Path.home().joinpath(".local","share")
            ):
        self.DEFAULT_CONFIG_DIR = Path(config_dir)
        self.DEFAULT_DATA_DIR = Path(data_dir)
        self.DEFAULT_CONFIG_FILE = Path(f"{self.DEFAULT_CONFIG_DIR}").joinpath("config.ini")
        self.DEFAULT_DATABASE_DIR = Path(self.DEFAULT_DATA_DIR).joinpath('db')
        self.DEFAULT_MINUTES_DIR = Path(self.DEFAULT_DATA_DIR).joinpath('minutes')

        self.config = configparser.ConfigParser()

        self.DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if not self.DEFAULT_CONFIG_FILE.exists():
            self.config['directories'] = {
                'database_dir': f"{self.DEFAULT_DATABASE_DIR}",
                'minutes_dir': f"{self.DEFAULT_MINUTES_DIR}"
                }

            if not Path(self.config['directories']['database_dir']).exists():
                Path.mkdir(self.config['directories']['database_dir'])

            with open(Path(self.DEFAULT_CONFIG_DIR).joinpath("config.ini"), 'w') as config_file:
                self.config.write(config_file)

        elif self.DEFAULT_CONFIG_FILE.exists():
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
