import numbers
from typing import List, Union
import os
import sys
from easydict import EasyDict as edict
from enum import IntEnum
import tables
import numpy as np
from pathlib import Path

import pymodaq_plugins_holoeye  # mandatory if not imported from somewhere else to load holeye module from local install
from holoeye import slmdisplaysdk

from pymodaq_gui.utils import select_file
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main
from pymodaq_utils.utils import ThreadCommand, getLineInfo
from pymodaq_gui.h5modules.browsing import browse_data
from pymodaqutils.enums import BaseEnum
from pymodaq.utils.data import DataActuator
from pymodaq_plugins_holoeye import Config as HoloConfig
from pymodaq_utils.logger import set_logger, get_module_name
from pymodaq_plugins_holoeye.resources.daq_move_HoloeyeBase import DAQ_Move_HoloeyeBase
from pymodaq.control_modules.move_utility_classes import DataActuatorType

logger = set_logger(get_module_name(__file__))
config = HoloConfig()


class DAQ_Move_Holoeye(DAQ_Move_HoloeyeBase):

    shaping_type: str = 'Phase Value'
    shaping_settings = []
    is_multiaxes = False
    axes_name = []
    data_actuator_type = DataActuatorType['DataActuator']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings.child('bounds', 'is_bounds').setValue(True)
        self.settings.child('bounds', 'max_bound').setValue(100)
        self.controller_units = ''

    def move(self, value: Union[numbers.Number, np.ndarray, DataActuator]):

        if isinstance(value, numbers.Number):
            self.controller.showBlankscreen(grayValue=int(value))
        elif isinstance(value, np.ndarray):
            self.controller.showData(value.astype(np.uint8))
        elif isinstance(value, DataActuator):
            self.controller.showData(value.data[0].astype(np.uint8))

    def commit_settings(self, param):
        super().commit_settings(param)


if __name__ == '__main__':
    main(__file__, init=True)
