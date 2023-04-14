# call the Holoeye python library for the correct path

import os
from pathlib import Path
import sys

from pymodaq.utils.config import BaseConfig


environs = []
for env in os.environ.keys():
    if 'HEDS' in env and 'MODULES' in env:
        environs.append(env)

environs = sorted(environs)
if 'HEDS_PYTHON_MODULES' in environs:
    environs.remove('HEDS_PYTHON_MODULES', )
sys.path.append(os.getenv(environs[-1], ''))


class Config(BaseConfig):
    """Main class to deal with configuration values for PyMoDAQ"""
    config_template_path = Path(__file__).parent.joinpath('resources/config_template.toml')
    config_name = 'config_holoeye'
