# call the Holoeye python library for the correct path

import os
from pathlib import Path
import sys

from pymodaq.utils.config import BaseConfig


environs = []
for env in os.environ.keys():
    if 'HEDS' in env and 'MODULES' in env:
        environs.append(env)

sorted(environs)
sys.path.append(os.getenv(environs[0], ''))


class Config(BaseConfig):
    """Main class to deal with configuration values for PyMoDAQ"""
    config_template_path = Path(__file__).parent.joinpath('resources/config_template.toml')
    config_name = 'config_holoeye'
