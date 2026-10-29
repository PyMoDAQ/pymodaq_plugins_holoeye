# call the Holoeye python library for the correct path

import os
from pathlib import Path
import sys
from pathlib import Path
from pymodaq_utils.logger import set_logger  # to be imported by other modules.

from pymodaq_utils.utils import get_version
from pymodaq_plugins_holoeye.utils import Config

__version__ = get_version(__package__)
config = Config()




def _add_to_path(folder: str):
    if folder and os.path.isdir(folder) and folder not in sys.path:
        sys.path.append(folder)


# SDK 3: python modules folder given by the HEDS_*_PYTHON_MODULES environment variable
environs = sorted(env for env in os.environ if 'HEDS' in env and 'MODULES' in env)
if 'HEDS_PYTHON_MODULES' in environs:  # old stuff without the sdk version
    environs.remove('HEDS_PYTHON_MODULES')
if environs:
    _add_to_path(os.getenv(environs[-1], ''))

# SDK 4: root folder given by HEDS_4_0_PYTHON, the python libraries are in api/python and examples
_sdk4_root = os.getenv('HEDS_4_0_PYTHON', '')
if _sdk4_root:
    _add_to_path(os.path.join(_sdk4_root, 'api', 'python'))
    _add_to_path(os.path.join(_sdk4_root, 'examples'))
