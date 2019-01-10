import logging

from .client import BlueIrisClient
from .const import PTZCommand, Signal, LOG_SEVERITY
from aiohttp import ClientSession

UNKNOWN_DICT = {'-1': ''}
UNKNOWN_LIST = [{'-1': ''}]
UNKNOWN_STRING = "noname"

_LOGGER = logging.getLogger(__name__)


class BlueIris:

    def __init__(self, aiosession: ClientSession, user, password, protocol, host, port="", debug=False, logger=_LOGGER):
        """Initialize a client which is prepared to talk with a Blue Iris server"""
        self._attributes = dict()
        self.logger = logger
        self.debug = debug
        self.am_logged_in = False

        if port != "":
            host = "{}:{}".format(host, port)
        self.url = "{}://{}/json".format(protocol, host)

        self.username = user
        self.password = password

        self.client = BlueIrisClient(aiosession, self.url, debug=self.debug, logger=self.logger)

    @property
    def attributes(self):
        return self._attributes

    async def async_setup_session(self):
        """Initialize the session with the Blue Iris server"""
        session_info = await self.client.login(self.username, self.password)
        self._attributes["name"] = session_info.get('system name', UNKNOWN_STRING)
        self._attributes["profiles"] = session_info.get('profiles', UNKNOWN_LIST)
        self._attributes["iam_admin"] = session_info.get('admin', False)
        self._attributes["ptz_allowed"] = session_info.get('ptz', False)
        self._attributes["clips_allowed"] = session_info.get('clips', False)
        self._attributes["schedules"] = session_info.get('schedules', UNKNOWN_LIST)
        self._attributes["version"] = session_info.get('version', UNKNOWN_STRING)
        self.am_logged_in = True
        if self.debug:
            self.logger.debug("Session info: {}".format(session_info))
            self.logger.debug(
                "Parsed following session values: name={}, profiles={}, iam_admin={}, ptz_allowed={},"
                " clips_allowed={}, schedules={}, version={}".format(
                    self._attributes["name"], self._attributes["profiles"], self._attributes["iam_admin"],
                    self._attributes["ptz_allowed"],
                    self._attributes["clips_allowed"], self._attributes["schedules"], self._attributes["version"]))

    async def async_update_status(self):
        if not self.am_logged_in:
            await self.async_setup_session()

        status = await self.client.cmd("status")
        if self.debug:
            self.logger.debug("Returned signal: {}".format(status["signal"]))
        self._attributes["signal"] = Signal(int(status["signal"]))
        if status["profile"] == -1:
            self._attributes["profile"] = "Undefined"
        else:
            self._attributes["profile"] = self._attributes["profiles"][status["profile"]]

    async def async_update_camlist(self):
        if not self.am_logged_in:
            await self.async_setup_session()

        camlist = await self.client.cmd("camlist")
        self.attributes["cameras"] = dict()
        for cam in camlist:
            self.attributes["cameras"][cam.get('optionValue')] = cam.get('optionDisplay')

