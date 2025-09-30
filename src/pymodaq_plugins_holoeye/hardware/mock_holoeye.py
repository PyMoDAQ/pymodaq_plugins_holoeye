from pymodaq_utils.enums import BaseEnum


class ErrorCode(BaseEnum):
    NoError = 0


class SLMInstance:

    def __init__(self):
        pass

    def open(self):
        return ErrorCode.NoError.value

    def errorString(self, error_code: ErrorCode):
        return error_code.name

    @property
    def width_px(self) -> int:
        return 1024

    @property
    def height_px(self) -> int:
        return 768

    def utilsSLMPreviewShow(self, *args, **kwargs):
        pass

    def showData(self, value):
        pass

    def showPhasevalues(self, value):
        pass
