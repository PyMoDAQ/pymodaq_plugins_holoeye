# call the Holoeye python library for the correct path

import os
from pathlib import Path
import sys
from pathlib import Path
from pymodaq.utils.logger import set_logger  # to be imported by other modules.

from .utils import Config
config = Config()

with open(str(Path(__file__).parent.joinpath('resources/VERSION')), 'r') as fvers:
    __version__ = fvers.read().strip()

environs = []
for env in os.environ.keys():
    if 'HEDS' in env and 'MODULES' in env:
        environs.append(env)

environs = sorted(environs)
if 'HEDS_PYTHON_MODULES' in environs:
    environs.remove('HEDS_PYTHON_MODULES', )
sys.path.append(os.getenv(environs[-1], ''))

