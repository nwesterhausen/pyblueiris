import logging
from math import floor

from .client import BlueIrisClient
from .const import PTZCommand, Signal, LOG_SEVERITY, CAMConfig
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

    async def setup_session(self):
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

    async def update_status(self):
        """Updates Blue Iris status"""
        if not self.am_logged_in:
            await self.setup_session()

        status = await self.client.cmd("status")
        if self.debug:
            self.logger.debug("Returned signal: {}".format(status["signal"]))
        self._attributes["signal"] = Signal(int(status["signal"]))
        if status["profile"] == -1:
            self._attributes["profile"] = "Undefined"
        else:
            self._attributes["profile"] = self._attributes["profiles"][status["profile"]]

    async def update_camlist(self):
        """Updates known cameras on Blue Iris"""
        if not self.am_logged_in:
            await self.setup_session()

        camlist = await self.client.cmd("camlist")
        self._attributes["cameras"] = dict()
        self._attributes["camconfig"] = camlist
        if camlist is None:
            camlist = dict()
        for cam in camlist:
            self._attributes["cameras"][cam.get('optionValue')] = cam.get('optionDisplay')

    async def update_cliplist(self, camera="Index"):
        """Updates list of available clips. Provide a camera name to update an individual camera"""
        if not await self.is_valid_camera(camera):
            camera = "Index"

        if "cliplist" not in self._attributes:
            self._attributes["cliplist"] = dict()
            for cam_shortname in self._attributes["cameras"].keys():
                if cam_shortname not in ['@Index', 'Index']:
                    self._attributes["cliplist"][cam_shortname] = []

        cliplist = await self.client.cmd("cliplist", {"camera": camera})

        if cliplist is None:
            cliplist = dict()
        for clip in cliplist:
            self._attributes["cliplist"][clip["camera"]].append(clip)

    async def update_alertlist(self, camera="Index"):
        """Updates list of alerts. Provide a camera name to update an individual camera"""
        if not await self.is_valid_camera(camera):
            camera = "Index"

        if "alertlist" not in self._attributes:
            self._attributes["alertlist"] = dict()
            for cam_shortname in self._attributes["cameras"].keys():
                if cam_shortname not in ['@Index', 'Index']:
                    self._attributes["alertlist"][cam_shortname] = []

        alertlist = await self.client.cmd("alertlist", {"camera": camera, "reset": "false"})
        if alertlist is not dict:
            alertlist = dict()
        for alert in alertlist:
            self._attributes["alertlist"][alert["camera"]].append(alert)

    async def update_log(self):
        """Updates the log from Blue Iris"""
        if not self.am_logged_in:
            await self.setup_session()

        log = await self.client.cmd("log")
        self._attributes["log"] = log

    async def update_sysconfig(self):
        """Updates the system configuration status from Blue Iris"""
        if not self.am_logged_in:
            await self.setup_session()

        if not self._attributes["iam_admin"]:
            self.logger.error("The sysconfig command requires admin access. Current user is NOT admin")
        else:
            sysconfig = await self.client.cmd("sysconfig")
            self._attributes["sysconfig"] = sysconfig

    async def update_all_information(self):
        """Update all the information we can get from the Blue Iris server"""
        if not self.am_logged_in:
            await self.setup_session()

        await self.update_status()
        await self.update_camlist()
        await self.update_cliplist()
        await self.update_alertlist()
        await self.update_log()
        await self.update_sysconfig()

    async def is_valid_camera(self, cam_shortcode):
        """Checks if camera shortcode is a valid option"""
        if not self.am_logged_in:
            await self.setup_session()
        if not self._attributes["cameras"]:
            await self.update_camlist()
        if cam_shortcode not in self._attributes["cameras"]:
            self.logger.error(
                "{}: invalid camera provided. Choose one of {}".format(cam_shortcode, self._attributes["cameras"].keys()))
            return False
        return True

    async def send_camera_reset(self, camera):
        """Send camconfig command to reset camera"""
        if await self.is_valid_camera(camera):
            resp = await self.client.cmd("camconfig", {"camera": camera, "reset": "true"})
            return resp["result"]

    async def send_camera_enable(self, camera):
        """Send camconfig command to enable camera"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "enable": "true"})

    async def send_camera_disable(self, camera):
        """Send camconfig command to enable camera"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "enable": "false"})

    async def unpause_camera(self, camera):
        """Send camconfig command to pause camera"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "pause": CAMConfig.PAUSE_CANCEL.value})

    async def pause_camera_indefinitely(self, camera):
        """Send camconfig command to pause camera"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "pause": CAMConfig.PAUSE_INDEFINITELY.value})

    async def pause_camera_add30seconds(self, camera):
        """Send camconfig command to pause camera"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "pause": CAMConfig.PAUSE_ADD_30_SEC.value})

    async def pause_camera_add1minute(self, camera):
        """Send camconfig command to pause camera"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "pause": CAMConfig.PAUSE_ADD_1_MIN.value})

    async def pause_camera_add1hour(self, camera):
        """Send camconfig command to pause camera"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "pause": CAMConfig.PAUSE_ADD_1_HOUR.value})

    async def pause_camera(self, camera, seconds):
        """Send camconfig command to pause camera for seconds (rounded down to nearest 30 seconds"""
        if seconds < 30:
            seconds = 30
        num_1hour_pauses = floor(seconds / 3600)
        num_1minute_pauses = floor(seconds / 60) - (60 * num_1hour_pauses)
        num_30second_pauses = floor(seconds / 30) - (2 * num_1minute_pauses) - (120 * num_1hour_pauses)
        if await self.is_valid_camera(camera):
            for x in range(num_1hour_pauses):
                await self.client.cmd("camconfig", {"camera": camera, "pause": CAMConfig.PAUSE_ADD_1_HOUR.value})
            for x in range(num_1minute_pauses):
                await self.client.cmd("camconfig", {"camera": camera, "pause": CAMConfig.PAUSE_ADD_1_MIN.value})
            for x in range(num_30second_pauses):
                await self.client.cmd("camconfig", {"camera": camera, "pause": CAMConfig.PAUSE_ADD_30_SEC.value})

    async def set_camera_motion(self, camera, motion_enabled=True):
        """Send camconfig command to pause camera"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "motion": motion_enabled})

    async def set_camera_schedule(self, camera, camera_schedule_enabled=True):
        """Send camconfig command to enable or disable the caerma's custom schedule"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "schedule": camera_schedule_enabled})

    async def set_camera_ptzcycle(self, camera, preset_cycle_enabled=True):
        """Send camconfig command to enable or disable the preset cycle feature"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "ptzcycle": preset_cycle_enabled})

    async def set_camera_ptzevent_schedule(self, camera, ptz_event_schedule_enabled=True):
        """Send camconfig command to enable or disable the PTZ event schedule"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("camconfig", {"camera": camera, "ptzevents": ptz_event_schedule_enabled})

    async def send_ptz_command(self, camera, command: PTZCommand):
        """Operate a camera's PTZ functionality"""
        if await self.is_valid_camera(camera):
            await self.client.cmd("ptz", {"camera":camera, "button": command.value, "updown": 1})

    async def set_status_signal(self, signal: Signal):
        """Send camconfig command to pause camera"""
        await self.client.cmd("status", {"signal": signal.value})

    async def set_status_profile(self, profile_index: int):
        """Send camconfig command to pause camera"""
        await self.client.cmd("status", {"profile": profile_index})

    async def set_status_profile_by_name(self, profile_name: str):
        """Send camconfig command to pause camera"""
        profile_ind = self._attributes["profiles"].index(profile_name)
        await self.set_status_profile(profile_ind)

    async def set_sysconfig_archive(self, archive_enabled: bool):
        """Enable or disable web archival"""
        if self._attributes["iam_admin"]:
            await self.client.cmd("sysconfig",{"archive": archive_enabled})

    async def set_sysconfig_schedule(self, global_schedule_enabled: bool):
        """Enable or disable web archival"""
        if self._attributes["iam_admin"]:
            await self.client.cmd("sysconfig",{"schedule": global_schedule_enabled})
