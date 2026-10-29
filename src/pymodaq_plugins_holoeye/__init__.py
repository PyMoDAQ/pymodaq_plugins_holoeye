# call the Holoeye python library for the correct path

import os
import re
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

# SDK 4 and newer: root folder given by HEDS_<major>_<minor>_PYTHON (the name changes with the version of the SDK),
# the python libraries are in api/python and examples. The most recent version is used.
_sdk_versions = {}
for env in os.environ:
    match = re.fullmatch(r'HEDS_(\d+)_(\d+)_PYTHON', env)
    if match and int(match.group(1)) >= 4:
        _sdk_versions[(int(match.group(1)), int(match.group(2)))] = env
if _sdk_versions:
    _sdk_root = os.getenv(_sdk_versions[max(_sdk_versions)], '')
    _add_to_path(os.path.join(_sdk_root, 'api', 'python'))
    _add_to_path(os.path.join(_sdk_root, 'examples'))
