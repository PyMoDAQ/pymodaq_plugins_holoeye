from abc import abstractproperty
from typing import List, Union, Tuple
import numbers

import numpy as np
from pathlib import Path

import pymodaq_plugins_holoeye  # mandatory if not imported from somewhere else to load holeye module from local install


from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType
from pymodaq_utils.utils import ThreadCommand, getLineInfo
from pymodaq_gui.h5modules.browsing import browse_data
from pymodaq_gui.parameter.utils import iter_children

from pymodaq.utils.data import DataActuator, DataWithAxes
from pymodaq_plugins_holoeye import Config as HoloConfig
from pymodaq_utils.logger import set_logger, get_module_name
from pymodaq_utils.math_utils import wrap

from holoeye.slmdisplaysdk import SLMInstance, ErrorCode

logger = set_logger(get_module_name(__file__))
config = HoloConfig()


class DAQ_Move_HoloeyeBase(DAQ_Move_base):

    controller_class = SLMInstance
    shaping_type: str = None
    shaping_settings: List = []

    is_multiaxes = False
    _axis_names = ['']
    data_actuator_type = DataActuatorType.DataActuator
    _epsilon = 0.00001
    _controller_units = ''
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
        {'title': 'Linear phase:', 'name': 'linear_phase', 'type': 'group', 'children': [
            {'title': 'Linear X:', 'name': 'linear_x', 'type': 'float',
             'value': 0},
            {'title': 'Linear Y:', 'name': 'linear_y', 'type': 'float',
             'value': 0}]},
        {'title': 'Quad. phase:', 'name': 'quad_phase', 'type': 'group', 'children': [
            {'title': 'Quad. X:', 'name': 'quad_x', 'type': 'float',
             'value': 0, },
            {'title': 'Quad. Y:', 'name': 'quad_y', 'type': 'float',
             'value': 0},
            {'title': 'Both:', 'name': 'quad_both', 'type': 'float',
             'value': 0},
        ]},
        {'title': 'Mask shift:', 'name': 'mask_shift', 'type': 'group', 'children': [
            {'title': 'Shift X (px):', 'name': 'shift_x', 'type': 'int',
             'value': 0},
            {'title': 'Shit Y (px):', 'name': 'shift_y', 'type': 'int',
             'value': 0}]},
             ] + comon_parameters_fun(is_multiaxes, _axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.settings.child('scaling').hide()

        self.calibration = None
        self._applied_value: np.ndarray = None

        self.controller = None
        self.settings.child('shaping_type').setValue(self.shaping_type)
        self.settings.child('options').addChildren(self.shaping_settings)

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
                                              new_controller=self.controller_class())

        if self.settings['multiaxes', 'multi_status'] == "Master":
            error = self.controller.open()
            if error != ErrorCode.NoError:
                raise IOError(f'SLM Error: {self.controller.errorString(error)}')

        data_width = self.controller.width_px
        data_height = self.controller.height_px

        self.settings.child('info', 'width').setValue(data_width)
        self.settings.child('info', 'height').setValue(data_height)

        self.current_position = DataActuator(data=[np.zeros(self.shape)])

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
        elif param.name() in iter_children(self.settings.child('linear_phase'), []) or \
                param.name() in iter_children(self.settings.child('quad_phase'), []) or \
                param.name() in iter_children(self.settings.child('mask_shift'), []):

            if param.name() == 'quad_both':
                self.settings.child('quad_phase', 'quad_x').setValue(param.value())
                self.settings.child('quad_phase', 'quad_y').setValue(param.value())

            self.move_abs(self._applied_value)
            self.emit_value(self.target_value)

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

    @property
    def shape(self) -> Tuple[int, int]:
        return (self.settings['info', 'height'],
                self.settings['info', 'width'])

    def apply_data(self, value: DataActuator):
        value_array = value[0]

        if self.settings['calibration', 'calib_apply'] and self.calibration is not None:
            value_array = np.reshape(
                np.interp(value_array.reshape(np.prod(value_array.shape)),
                          self.calibration,
                          np.linspace(0, 255, 256)).astype('uint8'),
                value_array.shape)
            self.controller.showData(value_array)
        else:
            self.controller.showPhasevalues(value_array)

    def compute_linear_phase(self) -> np.ndarray:
        xlin = self.settings['linear_phase', 'linear_x']
        ylin = self.settings['linear_phase', 'linear_y']

        ylin *= np.linspace(-self.shape[0] / 2, self.shape[0] / 2, self.shape[0], endpoint=True)
        xlin *= np.linspace(-self.shape[1] / 2, self.shape[1] / 2, self.shape[1], endpoint=True)

        yy, xx = np.meshgrid(ylin, xlin, indexing='ij')

        return yy + xx

    def set_linear_phase(self, xlin: float, ylin: float):
        """ Programmatically set the X and Y linear phase terms"""
        self.settings.child('linear_phase', 'linear_x').setValue(xlin)
        self.settings.child('linear_phase', 'linear_y').setValue(ylin)
        self.move_abs(self._applied_value)
        self.emit_value(self.target_value)

    def compute_quad_phase(self):
        xquad = self.settings['quad_phase', 'quad_x']
        yquad = self.settings['quad_phase', 'quad_y']

        yquad *= (np.linspace(-self.shape[0] / 2, self.shape[0] / 2, self.shape[0], endpoint=True)) ** 2
        xquad *= (np.linspace(-self.shape[1] / 2, self.shape[1] / 2, self.shape[1], endpoint=True)) ** 2

        yy, xx = np.meshgrid(yquad, xquad, indexing='ij')

        return yy + xx

    def set_quad_phase(self, xquad: float = None, yquad: float = None, both=None):
        """ Programmatically set the X and Y quadratic phase terms"""
        if both is None:
            if xquad is not None:
                self.settings.child('quad_phase', 'quad_x').setValue(xquad)
            if yquad is not None:
                self.settings.child('quad_phase', 'quad_y').setValue(yquad)
        else:
            self.settings.child('quad_phase', 'quad_both').setValue(both)
            self.settings.child('quad_phase', 'quad_x').setValue(both)
            self.settings.child('quad_phase', 'quad_y').setValue(both)
        self.move_abs(self._applied_value)
        self.emit_value(self.target_value)

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

        pos = self.target_value
        return pos

    def user_condition_to_reach_target(self) -> bool:
        return True

    def move(self, value):
        raise NotImplementedError

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (DataActuator) value of the absolute target positioning
        """
        if value.shape == (1,):
            value.data = [np.ones(self.shape) * value.data[0]]

        self._applied_value = value.deepcopy()

        value = value + self.compute_linear_phase() + self.compute_quad_phase()

        value = wrap(value)

        value = np.roll(value, shift=(self.settings['mask_shift', 'shift_y'],
                                      self.settings['mask_shift', 'shift_x']),
                        axis=(0,1))

        value = self.check_bound(value)  # if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one

        self.apply_data(value)


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
        if value.shape == (1,):
            value.data = [np.ones(self.shape) * value.data[0]]
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