from abc import abstractproperty
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

logger = set_logger(get_module_name(__file__))
config = HoloConfig()


class DAQ_Move_HoloeyeBase(DAQ_Move_base):

    shaping_type: str = abstractproperty()
    shaping_settings: List = abstractproperty()
    is_multiaxes = False
    axes_name = []

    _epsilon = 1
    _controller_units = 'greyscale'  # dependent on the shaping_type so to be updated accordingly using self.controller_units = new_unit

    params = [
        {'title': 'SLM Infos:', 'name': 'info', 'type': 'group', 'visible': True, 'children': [
            {'title': 'Width:', 'name': 'width', 'type': 'int', 'value': 0, 'readonly': True},
            {'title': 'Height:', 'name': 'height', 'type': 'int', 'value': 0, 'readonly': True},
        ]},
        {'title': 'Show Preview?:', 'name': 'show_preview', 'type': 'bool', 'value': False},
        {'title': 'Shaping type:', 'name': 'shaping_type', 'type': 'str', 'value': ''},
        {'title': 'shaping options:', 'name': 'options', 'type': 'group', 'visible': True,
         'children': []},
        {'title': 'Calibration:', 'name': 'calibration', 'type': 'group', 'children': [
            {'title': 'File name:', 'name': 'calib_file', 'type': 'browsepath',
             'value': config('calibration', 'path'),
             'filetype': True},
            {'title': 'Apply calib?:', 'name': 'calib_apply', 'type': 'bool', 'value': False},
              ]},
             ] + comon_parameters_fun(is_multiaxes, axes_name, epsilon=_epsilon)

    def ini_attributes(self):
        self.settings.child('scaling').hide()
        self.calibration = None
        self.controller: slmdisplaysdk.SLMInstance = None
        self.settings.child('shaping_type').setValue(self.shaping_type)
        self.settings.child('options').addChildren(self.shaping_settings)

        self.settings.child('multiaxes', 'ismultiaxes').setValue(self.is_multiaxes)
        self.settings.child('multiaxes').show(self.is_multiaxes)

        self.settings.child('multiaxes', 'axis').setOpts(limits=self.axes_name)

    def ini_stage(self, controller=None):
        """
            Initialize the controller and stages (axes) with given parameters.

            ============== ================================================ ==========================================================================================
            **Parameters**  **Type**                                         **Description**

            *controller*    instance of the specific controller object       If defined this hardware will use it and will not initialize its own controller instance
            ============== ================================================ ==========================================================================================

            Returns
            -------
            Easydict
                dictionnary containing keys:
                 * *info* : string displaying various info
                 * *controller*: instance of the controller object in order to control other axes without the need to init the same controller twice
                 * *stage*: instance of the stage (axis or whatever) object
                 * *initialized*: boolean indicating if initialization has been done corretly

            See Also
            --------
             daq_utils.ThreadCommand
        """

        self.controller = self.ini_stage_init(old_controller=controller,
                                              new_controller=slmdisplaysdk.SLMInstance())

        if self.settings['multiaxes', 'multi_status'] == "Master":
            error = self.controller.open()
            assert error == slmdisplaysdk.ErrorCode.NoError, self.controller.errorString(error)

        data_width = self.controller.width_px
        data_height = self.controller.height_px

        self.settings.child('info', 'width').setValue(data_width)
        self.settings.child('info', 'height').setValue(data_height)

        info = "Holoeye"
        initialized = True
        return info, initialized

    def commit_settings(self, param):
        """Apply settings modification to the SLM

        To be implemented in real implementations
        """
        if param.name() == 'show_preview':
            self.controller.utilsSLMPreviewShow(param.value())
        elif param.name() == 'calib_file' or param.name() == 'calib_apply':
            fname = self.settings['calibration', 'calib_file']
            self.load_calibration(fname)

        self.commit_options(param)

    def load_calibration(self, fname: str):

        path = Path()
        ext = path.suffix[1:]

        if not path.is_file():
            self.calibration = None
            self.emit_status(ThreadCommand('Update_Status',['No calibration has been loaded','log']))

        if 'h5' in ext:
            self.calibration = browse_data(fname) #phase values corresponding to grey levels (256 elements in array)
        elif 'txt' in ext or 'dat' in ext:
            self.calibration = np.loadtxt(fname)[:, 1]  # to update in order to select what data in file
        else: 
            self.calibration = None
            logger.warning('No calibration has been loaded')

        if self.calibration is not None:
            if self.calibration.shape != (self.settings['info', 'height'],
                                          self.settings['info', 'width']):
                logger.warning(f"Data with shape {self.calibration.shape} cannot be loaded into the SLM of shape"
                               f" {(self.settings['info', 'height'], self.settings['info', 'width'])}")
                self.calibration = None

    def apply_data(self, data: np.ndarray = None):
        if data.shape != (self.settings['info', 'height'],
                          self.settings['info', 'width']):
            raise ValueError(f"Data with shape {data.shape} cannot be loaded into the SLM of shape"
                             f" {(self.settings['info', 'height'],  self.settings['info', 'width'])}")

        if self.settings['calibration', 'calib_apply'] and self.calibration is not None:
            data = np.reshape(np.interp(data.reshape(np.prod(data.shape)),
                                        self.calibration,
                                        np.linspace(0, 255, 256)).astype('uint8'),
                              data.shape)

        self.controller.showData(data.astype(np.uint8))

    def close(self):
        """

        """
        self.controller.close()

    def stop_motion(self):
        self.move_done()

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        pos = self.current_position
        return pos

    def move(self, value):
        raise NotImplementedError

    def move_abs(self, value):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  # if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
        self.move(value)

        self.current_position = value

    def move_rel(self, value):
        """
            Make the relative move from the given position after thread command signal was received in DAQ_Move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            hardware.set_position_with_scaling, DAQ_Move_base.poll_moving

        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position

        self.move_abs(self.target_value)

    def move_home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """
        pass


if __name__ == '__main__':
    main(__file__, init=True)