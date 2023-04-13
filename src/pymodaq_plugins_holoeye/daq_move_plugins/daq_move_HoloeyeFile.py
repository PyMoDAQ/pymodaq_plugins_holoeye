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


class DAQ_Move_HoloeyeFile(DAQ_Move_HoloeyeBase):

    shaping_type: str = 'File'
    shaping_settings = [
        {'title': 'File name:', 'name': 'file', 'type': 'browsepath', 'value': '', 'filetype': True},
        {'title': 'Apply:', 'name': 'apply', 'type': 'bool_push', 'value': False},
    ]
    is_multiaxes = False
    axes_name = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings.child('bounds', 'is_bounds').setValue(False)
        self.controller_units = 'file'

    def move(self, value=0.):
        data = np.loadtxt(self.settings['options', 'file'])

        if data.shape != (self.settings['info', 'height'],
                          self.settings['info', 'width']):
            raise ValueError(f"Data with shape {data.shape} cannot be loaded into the SLM of shape"
                             f" {(self.settings['info', 'height'],  self.settings['info', 'width'])}")

        if self.settings['calibration', 'calib_apply'] and self.calibration is not None:
            data = np.reshape(np.interp(data.reshape(np.prod(data.shape)),
                                        self.calibration,
                                        np.linspace(0, 255, 256)).astype('uint8'),
                              data.shape)

        if data is None:
            raise Exception('No data has been selected')
        else:
            self.controller.showData(data.astype(np.uint8))

    def commit_options(self, param):
        if param.name() == 'apply':
            self.move()


if __name__ == '__main__':
    main(__file__, init=True)
