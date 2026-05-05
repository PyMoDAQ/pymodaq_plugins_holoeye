from typing import List, Union, Tuple


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
    comon_shaping_params = [
        {'title': 'SLM Infos:', 'name': 'info', 'type': 'group', 'visible': True, 'children': [
            {'title': 'Width:', 'name': 'width', 'type': 'int', 'value': 0, 'readonly': True},
            {'title': 'Height:', 'name': 'height', 'type': 'int', 'value': 0, 'readonly': True},
        ]},
        {'title': 'Show Preview?:', 'name': 'show_preview', 'type': 'bool', 'value': False},
        {'title': 'Shaping type:', 'name': 'shaping_type', 'type': 'str', 'value': ''},
        {'title': 'shaping options:', 'name': 'options', 'type': 'group', 'visible': True,
         'children': []},
        {'title': 'Input as grey:', 'name': 'input_as_grey_levels', 'type': 'bool', 'value': False},
    ]
    params = comon_shaping_params + comon_parameters_fun(is_multiaxes, _axis_names, epsilon=_epsilon)

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
        if self.is_master:
            self.controller = self.controller_class()
        else:
            self.controller = controller


        if self.is_master:
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

    @property
    def shape(self) -> Tuple[int, int]:
        return (self.settings['info', 'height'],
                self.settings['info', 'width'])

    def apply_data(self, value: DataActuator):
        value_array = value[0]

        if self.settings['input_as_grey_levels'] or ('as_grey_levels' in value.extra_attributes and value.as_grey_levels):
            self.controller.showData(value_array)
        else:
            self.controller.showPhasevalues(value_array)

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