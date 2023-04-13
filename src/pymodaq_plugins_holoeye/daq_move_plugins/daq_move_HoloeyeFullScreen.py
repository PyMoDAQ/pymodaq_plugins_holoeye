from typing import List
import os
import sys
from easydict import EasyDict as edict
from enum import IntEnum
import tables
import numpy as np
from pathlib import Path

import pymodaq_plugins_holoeye  # mandatory if not imported from somewhere else to load holeye module from local install
from holoeye import slmdisplaysdk

from pymodaq.utils.gui_utils import select_file
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.utils.h5modules.browsing import browse_data
from pymodaq.utils.enums import BaseEnum
from pymodaq_plugins_holoeye import Config as HoloConfig
from pymodaq.utils.logger import set_logger, get_module_name
from pymodaq_plugins_holoeye.resources.daq_move_HoloeyeBase import DAQ_Move_HoloeyeBase


logger = set_logger(get_module_name(__file__))
config = HoloConfig()


class DAQ_Move_HoloeyeFullScreen(DAQ_Move_HoloeyeBase):

    shaping_type: str = 'FullScreen'
    shaping_settings: List = []
    is_multiaxes = False
    axes_names = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings.child('bounds', 'is_bounds').setValue(True)
        self.settings.child('bounds', 'max_bound').setValue(255)
        self.controller_units = 'greyscale'

    def move(self, value):
        self.controller.showBlankscreen(grayValue=int(value))


if __name__ == '__main__':
    main(__file__, init=True)