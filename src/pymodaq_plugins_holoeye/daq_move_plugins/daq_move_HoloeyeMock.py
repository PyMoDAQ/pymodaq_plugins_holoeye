import numbers
from typing import List, Union, Dict

import numpy as np

from pymodaq.control_modules.move_utility_classes import main

from pymodaq.utils.data import DataActuator, DataWithAxes
from pymodaq_plugins_holoeye import Config as HoloConfig
from pymodaq_utils.logger import set_logger, get_module_name
from pymodaq_plugins_holoeye.resources.daq_move_HoloeyeBase import DAQ_Move_HoloeyeBase
from pymodaq.control_modules.move_utility_classes import DataActuatorType

from pymodaq_plugins_holoeye.hardware.mock_holoeye import SLMInstance, ErrorCode

logger = set_logger(get_module_name(__file__))
config = HoloConfig()


class DAQ_Move_HoloeyeMock(DAQ_Move_HoloeyeBase):

    controller_class = SLMInstance



if __name__ == '__main__':
    main(__file__, init=True)
