"""Adapter of the Holoeye SLM Display SDK 4 (module ``HEDS``) to the interface of the ``SLMInstance`` of the SDK 3"""
import numpy as np

NO_ERROR = 0


class SLMInstance4:
    """Same methods as the ``SLMInstance`` of the SDK 3, used by the plugins, but based on the SDK 4"""

    def __init__(self):
        import HEDS
        from hedslib import heds_types
        self._heds = HEDS
        self._types = heds_types
        self._slm = None
        self.width_px = 0
        self.height_px = 0
        self.pixelsize_um = 0.

    def open(self, preview: bool = False):
        """Open the SLM window. The preview window is not opened by default (it may require authorizations)"""
        error = self._heds.SDK.Init(4, 0)
        if error != self._types.HEDSERR_NoError:
            return error
        self._slm = self._heds.SLM.Init(preselect='', openPreview=preview)
        error = self._slm.errorCode()
        if error != self._types.HEDSERR_NoError:
            return error
        self.width_px = self._slm.width_px()
        self.height_px = self._slm.height_px()
        self.pixelsize_um = self._slm.pixelsize_um()
        return NO_ERROR

    def errorString(self, error):
        return self._heds.SDK.ErrorString(error)

    def close(self):
        if self._slm is not None:
            self._slm.window().close()
            self._slm = None

    def showData(self, data):
        """Show 8 bits grey levels"""
        grey = np.ascontiguousarray(np.clip(np.rint(np.asarray(data, dtype=float)), 0, 255).astype(np.uint8))
        return self._slm.showImageData(grey)

    def showPhasevalues(self, data):
        """Show phase values in radians, wrapped in [0, 2pi["""
        phase = np.ascontiguousarray(np.mod(np.asarray(data, dtype=np.float32), 2 * np.pi))
        return self._slm.showPhaseData(phase, phase_unit=2 * np.pi)

    def utilsSLMPreviewShow(self, show=True):
        preview = self._slm.preview()
        return preview.open() if show else preview.close()
