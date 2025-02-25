
import numpy as np

from pymodaq.utils.data import DataActuator


from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main

from pymodaq_plugins_holoeye import Config as HoloConfig
from pymodaq_utils.logger import set_logger, get_module_name
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

    def move_abs(self, value=0.):
        data = np.loadtxt(self.settings['options', 'file'])
        super().move_abs(DataActuator(data=data))

    def commit_options(self, param):
        if param.name() == 'apply':
            self.move()


if __name__ == '__main__':
    main(__file__, init=True)
