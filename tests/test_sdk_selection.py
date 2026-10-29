"""Tests of the selection between the Holoeye SDK 3 and 4, with fake SDK modules (no hardware)"""
import sys
import types

import numpy as np
import pytest

from pymodaq.utils.plugin_testing import make_actuator, move_abs_and_wait
from pymodaq.utils.data import DataActuator

from pymodaq_plugins_holoeye.hardware import sdk
from pymodaq_plugins_holoeye.hardware.sdk4 import SLMInstance4
from pymodaq_plugins_holoeye.daq_move_plugins.daq_move_Holoeye import DAQ_Move_Holoeye
from pymodaq_plugins_holoeye.daq_move_plugins.daq_move_HoloeyeMock import DAQ_Move_HoloeyeMock


class FakeSlm4:
    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.shown = []
        self.closed = False
        self.preview_state = []

    def errorCode(self):
        return 0

    def width_px(self):
        return 8

    def height_px(self):
        return 6

    def pixelsize_um(self):
        return 8.

    def showImageData(self, data, flags=None):
        self.shown.append((np.asarray(data), None))
        return 0

    def showPhaseData(self, data, phase_unit=256):
        self.shown.append((np.asarray(data), phase_unit))
        return 0

    def window(self):
        slm = self
        return types.SimpleNamespace(close=lambda: setattr(slm, 'closed', True) or 0)

    def preview(self):
        return types.SimpleNamespace(open=lambda: self.preview_state.append(True) or 0,
                                     close=lambda: self.preview_state.append(False) or 0)


@pytest.fixture
def fake_sdk4(monkeypatch):
    slms = []

    def init_with_option(preselect='', openPreview=True, previewScale=1.0):
        slms.append(FakeSlm4(preselect=preselect, openPreview=openPreview))
        return slms[-1]

    heds = types.ModuleType('HEDS')
    heds.SDK = types.SimpleNamespace(Init=lambda major, minor: 0, ErrorString=lambda error: f'error {error}')
    heds.SLM = types.SimpleNamespace(Init=init_with_option)
    hedslib = types.ModuleType('hedslib')
    heds_types = types.ModuleType('hedslib.heds_types')
    heds_types.HEDSERR_NoError = 0
    hedslib.heds_types = heds_types
    monkeypatch.setitem(sys.modules, 'HEDS', heds)
    monkeypatch.setitem(sys.modules, 'hedslib', hedslib)
    monkeypatch.setitem(sys.modules, 'hedslib.heds_types', heds_types)
    heds.slms = slms
    return heds


class TestSelection:
    def test_unknown_version(self):
        with pytest.raises(ValueError):
            sdk.select_sdk('5')

    @pytest.mark.parametrize('installed, requested, expected', [
        (['4', '3'], 'auto', '4'), (['4'], 'auto', '4'), (['3'], 'auto', '3'),
        (['3', '4'], '4', '4'), (['3', '4'], '3', '3')])
    def test_choice(self, monkeypatch, installed, requested, expected):
        monkeypatch.setattr(sdk, 'installed_sdks', lambda: installed)
        assert sdk.select_sdk(requested) == expected

    @pytest.mark.parametrize('installed, requested', [([], 'auto'), (['3'], '4'), (['4'], '3')])
    def test_not_installed(self, monkeypatch, installed, requested):
        monkeypatch.setattr(sdk, 'installed_sdks', lambda: installed)
        with pytest.raises(ImportError):
            sdk.select_sdk(requested)

    def test_sdk4_detected_and_class(self, fake_sdk4):
        assert '4' in sdk.installed_sdks()
        assert sdk.get_slm_class('4') is SLMInstance4


class TestSdk4Adapter:
    def test_open_without_preview_by_default(self, fake_sdk4):
        slm = SLMInstance4()
        assert slm.open() == 0
        assert fake_sdk4.slms[-1].init_kwargs['openPreview'] is False
        assert (slm.width_px, slm.height_px) == (8, 6)

    def test_grey_levels_and_phase(self, fake_sdk4):
        slm = SLMInstance4()
        slm.open()
        slm.showData(np.full((6, 8), 300.4))
        slm.showPhasevalues(np.full((6, 8), 2 * np.pi + 1))
        (grey, grey_unit), (phase, phase_unit) = fake_sdk4.slms[-1].shown
        assert grey.dtype == np.uint8 and np.all(grey == 255) and grey_unit is None
        assert np.allclose(phase, 1, atol=1e-5) and phase_unit == pytest.approx(2 * np.pi)

    def test_preview_and_close(self, fake_sdk4):
        slm = SLMInstance4()
        slm.open()
        slm.utilsSLMPreviewShow(True)
        slm.utilsSLMPreviewShow(False)
        fake = fake_sdk4.slms[-1]
        assert fake.preview_state == [True, False]
        slm.close()
        assert fake.closed

    def test_error_string(self, fake_sdk4):
        assert SLMInstance4().errorString(3) == 'error 3'


def test_plugin_with_sdk4(qapp, fake_sdk4):
    plugin = make_actuator(DAQ_Move_Holoeye, sdk='4')
    assert plugin.initialized
    assert plugin.settings['info', 'width'] == 8
    move_abs_and_wait(plugin, DataActuator(data=[np.zeros((6, 8))]))
    assert len(fake_sdk4.slms[-1].shown) == 1
    plugin.close()
    assert fake_sdk4.slms[-1].closed


def test_plugin_without_any_sdk(qapp, monkeypatch):
    monkeypatch.setattr(sdk, 'installed_sdks', lambda: [])
    with pytest.raises(ImportError):
        make_actuator(DAQ_Move_Holoeye)


def test_mock_plugin_still_works(qapp):
    plugin = make_actuator(DAQ_Move_HoloeyeMock)
    assert plugin.initialized
    move_abs_and_wait(plugin, 0.5)
    plugin.close()
