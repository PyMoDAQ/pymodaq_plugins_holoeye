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


class DAQ_Move_HoloeyeSplitScreen(DAQ_Move_HoloeyeBase):

    shaping_type: str = 'SplitScreen'
    shaping_settings = [
        {'title': 'Splitting (%):', 'name': 'split_value', 'type': 'int', 'value': 50, 'min': 0, 'max': 100},
        {'title': 'Grey A value:', 'name': 'greyA_value', 'type': 'int', 'value': 0, 'min': 0, 'max': 255},
        {'title': 'Grey B value:', 'name': 'greyB_value', 'type': 'int', 'value': 255, 'min': 0, 'max': 255},
        {'title': 'Splitting direction:', 'name': 'split_dir', 'type': 'list',
         'limits': ['Horizontal', 'Vertical']},
        {'title': 'Flipped?:', 'name': 'split_flip', 'type': 'bool', 'value': False},]
    is_multiaxes = True
    axes_name = ['Screen spliting', 'GreyA', 'GreyB']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings.child('bounds', 'is_bounds').setValue(True)
        self.settings.child('bounds', 'max_bound').setValue(100)
        self.controller_units = 'percent'

    def move(self, value):
        if self.settings['multiaxes', 'axis'] == 'Screen spliting':  # ,'GreyA','GreyB']
            screenDivider = value
            self.settings.child('options', 'split_value').setValue(value)
        else:
            screenDivider = self.settings['options', 'split_value']

        if self.settings['multiaxes', 'axis'] == 'GreyA':
            a_gray_value = int(value)
            self.settings.child('options', 'greyA_value').setValue(a_gray_value)
        else:
            a_gray_value = self.settings['options', 'greyA_value']
        if self.settings['multiaxes', 'axis'] == 'GreyB':
            b_gray_value = int(value)
            self.settings.child('options', 'greyB_value').setValue(b_gray_value)
        else:
            b_gray_value = self.settings['options', 'greyB_value']

        flipped = self.settings['options', 'split_flip']

        if self.settings['options', 'split_dir'] == 'Vertical':
            self.controller.showDividedScreenVertical(a_gray_value, b_gray_value, screenDivider / 100, flipped)
        else:
            self.controller.showDividedScreenHorizontal(a_gray_value, b_gray_value, screenDivider / 100, flipped)

    def commit_options(self, param):
        if self.settings['multiaxes', 'axis'] == 'Screen spliting':
            self.settings.child('bounds', 'max_bound').setValue(100)
            self.controller_units = 'Percent'
        else:
            self.settings.child('bounds', 'max_bound').setValue(255)
            self.controller_units = 'Greyscale'


if __name__ == '__main__':
    DAQ_Move_HoloeyeSplitScreen.axes_name
    main(__file__, init=True)
