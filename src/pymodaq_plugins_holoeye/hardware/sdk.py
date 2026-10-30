"""Selection of the Holoeye SLM Display SDK to use: version 3 (``holoeye.slmdisplaysdk``) or version 4 (``HEDS``).

Both SDKs can be installed at the same time (each has its own environment variable, see ``pymodaq_plugins_holoeye``).
They are only imported when requested, and both expose the same minimal interface to the plugins, the one of the
``SLMInstance`` of the SDK 3: ``open``, ``close``, ``errorString``, ``width_px``, ``height_px``, ``showData``,
``showPhasevalues`` and ``utilsSLMPreviewShow``.
"""
import importlib.util
import sys
from typing import List

import pymodaq_plugins_holoeye  # adds the SDK folders to the python path

SDK_CHOICES = ['auto', '3', '4']
NO_ERROR = 0


def _is_available(module_name: str) -> bool:
    if module_name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def installed_sdks() -> List[str]:
    """The versions of the SDK that can be imported, the most recent first"""
    sdks = []
    if _is_available('HEDS') and _is_available('hedslib'):
        sdks.append('4')
    if _is_available('holoeye.slmdisplaysdk'):
        sdks.append('3')
    return sdks


def select_sdk(version: str = 'auto') -> str:
    """Return '3' or '4'. With 'auto' the SDK 4 is used when installed (more recent), else the SDK 3"""
    version = str(version)
    if version not in SDK_CHOICES:
        raise ValueError(f'Unknown SDK version {version}, should be one of {SDK_CHOICES}')
    sdks = installed_sdks()
    if version == 'auto':
        if not sdks:
            raise ImportError('No Holoeye SLM Display SDK found: install the SDK 3 or 4 and set its environment '
                              'variable (HEDS_*_PYTHON_MODULES for the SDK 3, HEDS_<major>_<minor>_PYTHON for the SDK 4 and newer)')
        return sdks[0]
    if version not in sdks:
        raise ImportError(f'The Holoeye SLM Display SDK {version} cannot be imported, '
                          f'installed SDKs: {sdks if sdks else "none"}')
    return version


def get_slm_class(version: str = 'auto'):
    """Return the class driving the SLM with the requested SDK"""
    if select_sdk(version) == '3':
        from holoeye.slmdisplaysdk import SLMInstance
        return SLMInstance
    from pymodaq_plugins_holoeye.hardware.sdk4 import SLMInstance4
    return SLMInstance4
