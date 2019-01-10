
UNKNOWN_DICT = {'-1': ''}
UNKNOWN_LIST = [{'-1': ''}]
UNKNOWN_STRING = "noname"


class BlueIris:

    def __init__(self):
        self._status = UNKNOWN_DICT
        self._camlist = UNKNOWN_LIST
        self._camcodes = []
        self._camnames = []
        self._alertlist = UNKNOWN_LIST
        self._cliplist = UNKNOWN_LIST
        self._profiles = UNKNOWN_LIST
        self._log = UNKNOWN_LIST

