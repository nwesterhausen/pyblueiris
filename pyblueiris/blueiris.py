"""Module for communicating with a Blue Iris server."""

import logging
import time
from math import floor

from .client import BlueIrisClient
from .camera import BlueIrisCamera
from .const import PTZCommand, Signal, CAMConfig
from aiohttp import ClientSession

# The following constants are used when understanding the data returned by
# the login command. We get a lot of information about the server. These
# constants help make any future changes to the API easier and make the
# code down below a little less 'magic'
SESSION_NAME = 'system name'
SESSION_PROFILES = 'profiles'
SESSION_IAM_ADMIN = 'admin'
SESSION_PTZ_ALLOWED = 'ptz'
SESSION_DIO_AVAILABLE = 'dio'
SESSION_CLIPS_ALLOWED = 'clips'
SESSION_SCHEDULES = 'schedules'
SESSION_VERSION = 'version'
SESSION_AUDIO_ALLOWED = 'audio'
SESSION_STREAM_TIMELIMIT = 'streamtimelimit'
SESSION_LICENSE = 'license'
SESSION_SUPPORT = 'support'
SESSION_USER = 'user'
SESSION_LATITUDE = 'latitude'
SESSION_LONGITUDE = 'longitude'
SESSION_TZONE = 'tzone'
SESSION_STREAMS = 'streams'
SESSION_SOUNDS = 'sounds'
SESSION_WWW_SOUNDS = 'www_sounds'

# These values are used to initialize values which are unknown at the time.
UNKNOWN_DICT = {'-1': ''}
UNKNOWN_LIST = [{'-1': ''}]
UNKNOWN_STRING = "noname"

STALE_THRESHOLD = 5  # This was going to be used to auto-update attributes when calling the property
LAST_UPDATE_KEY = "lastupdate"  # Used in a dict to store the last update time

# Creates a default logger if none is provided during instantiation
_LOGGER = logging.getLogger(__name__)


class BlueIris:
    """Class which represents a Blue Iris server.

    :param ClientSession aiosession: AIOHTTP Client Session to run the commands through (required)
    :param str user: Username used to authenticate to the Blue Iris server.
    :param str password: Password used to authenticate to the Blue Iris server.
    :param str protocol: Protocol used to communicate with the Blue Iris server. This should be either `http` or
        `https`.
    :param str host: The IP address or FQDN used to communicate with the Blue Iris server.
    :param int port: The port used to communicate with the Blue Iris server. This defauls to match `protocol` --
        80 for `http` and 443 for `https`.
    :param bool debug: Should we print extra debug messages? True if yes, False if no; defaults to False.
    :param Logger logger: The Logger to log messages to. Specify your own if you want to control where the
        log messages go. By default, uses the namespace `__name__` for logging.
    """

    def __init__(self,
                 aiosession: ClientSession,
                 user,
                 password,
                 protocol,
                 host,
                 port="",
                 debug=False,
                 logger=_LOGGER):
        """Initialize a representation of a Blue Iris server which can be interacted with."""
        self._attributes = dict()
        self._cameras = dict()
        self._camera_details = dict()
        self._camera_details[LAST_UPDATE_KEY] = 0
        self.logger = logger
        self.debug = debug
        self.am_logged_in = False

        if port != "":
            host = "{}:{}".format(host, port)
        if protocol not in ['http', 'https']:
            self.logger.warning(
                "Invalid protocol passed {}. (Expected 'http' or 'https'. Using 'http')"
                .format(protocol))
            protocol = 'http'
        self._base_url = "{}://{}".format(protocol, host)
        self.url = "{}/json".format(self._base_url)
        self.username = user
        self.password = password
        if self.debug:
            self.logger.info("Attempting connection to {}".format(self.url))

        self.client = BlueIrisClient(
            aiosession, self.url, debug=self.debug, logger=self.logger)

    @property
    def attributes(self):
        """Return a dict of the Blue Iris server properties."""
        return self._attributes

    @property
    def admin(self):
        """Return True if we are authenticated as admin."""
        return self._attributes["iam_admin"]

    @property
    def name(self):
        """Return the name of the Blue Iris server."""
        return self.attributes["name"]

    @property
    def version(self):
        """Return the version of Blue Iris running on the server."""
        return self.attributes["version"]

    @property
    def base_url(self):
        """Return the configured base url, including protocol and port."""
        return self._base_url

    async def setup_session(self):
        """Log into the Blue Iris server and sets attributes values with server information."""
        full_reply = await self.client.login(self.username, self.password)
        if "data" not in full_reply:
            self.logger.error(
                "Did not get a good result from login command. Failing login.")
            self.logger.debug(full_reply)
            return False
        # Extract the server information from the login reply
        session_info = full_reply["data"]
        self._attributes["name"] = session_info.get(SESSION_NAME,
                                                    UNKNOWN_STRING)
        self._attributes["profiles"] = session_info.get(
            SESSION_PROFILES, UNKNOWN_LIST)
        self._attributes["iam_admin"] = session_info.get(
            SESSION_IAM_ADMIN, False)
        self._attributes["ptz_allowed"] = session_info.get(
            SESSION_PTZ_ALLOWED, False)
        self._attributes["clips_allowed"] = session_info.get(
            SESSION_CLIPS_ALLOWED, False)
        self._attributes["schedules"] = session_info.get(
            SESSION_SCHEDULES, UNKNOWN_LIST)
        self._attributes["version"] = session_info.get(SESSION_VERSION,
                                                       UNKNOWN_STRING)
        self._attributes["audio_allowed"] = session_info.get(
            SESSION_AUDIO_ALLOWED, False)
        self._attributes["dio_available"] = session_info.get(
            SESSION_DIO_AVAILABLE, False)
        self._attributes["stream_timelimit"] = session_info.get(
            SESSION_STREAM_TIMELIMIT, False)
        self._attributes["license"] = session_info.get(SESSION_LICENSE,
                                                       UNKNOWN_STRING)
        self._attributes["support"] = session_info.get(SESSION_SUPPORT)
        self._attributes["user"] = session_info.get(SESSION_USER,
                                                    UNKNOWN_STRING)
        self._attributes["longitude"] = session_info.get(
            SESSION_LONGITUDE, UNKNOWN_STRING)
        self._attributes["latitude"] = session_info.get(
            SESSION_LATITUDE, UNKNOWN_STRING)
        self._attributes["tzone"] = session_info.get(SESSION_TZONE,
                                                     UNKNOWN_STRING)
        self._attributes["streams"] = session_info.get(SESSION_STREAMS,
                                                       UNKNOWN_LIST)
        self._attributes["sounds"] = session_info.get(SESSION_SOUNDS,
                                                      UNKNOWN_LIST)
        self._attributes["www_sounds"] = session_info.get(
            SESSION_WWW_SOUNDS, UNKNOWN_LIST)
        # Now we are logged in, let's make sure we know it
        self.am_logged_in = True
        if self.debug:
            self.logger.debug("Session info: {}".format(session_info))
        return True

    async def send_command(self, command: str, params=None):
        """
        Send command to the Blue Iris server. Return a dict of data or True on success. Return False on failure.
        
        :param str command: Command to send to the server. See the JSON API reference for valid values
        :param dict() params: Dictionary of extra parameters for the command. By default no extra parameters are sent.
        """
        if not self.am_logged_in:
            # If we aren't logged in for some reason, let's log in again
            if not await self.setup_session():
                self.logger.error(
                    "Unable to login, not sending {}".format(command))
                return False
        # Send the command to the server
        result = await self.client.cmd(command, params)
        # Sometimes when a command is sent to Blue Iris, it doesn't return a data attribute but is still successful.
        if "data" in result:
            return result["data"]
        if result["result"] == "success":
            return True
        self.logger.error("Got a fail result without data from {}({})".format(
            command, params))
        return False

    async def update_status(self):
        """Update the status record in attributes."""
        status = await self.send_command("status")
        if self.debug:
            self.logger.debug("Returned signal: {}".format(status["signal"]))
        self._attributes["signal"] = Signal(int(status["signal"]))
        if status["profile"] == -1:
            self._attributes["profile"] = "Undefined"
        else:
            self._attributes["profile"] = self._attributes["profiles"][
                status["profile"]]

    @property
    def cameras(self):
        """Return list of cameras on Blue Iris."""
        cameras_as_list = list()
        for key in self._cameras:
            cameras_as_list.append(self._cameras[key])
        return cameras_as_list

    async def update_camlist(self):
        """Update the camera config and camera list in attributes."""
        camlist = await self.send_command("camlist")
        self._attributes["cameras"] = dict()
        self._attributes[
            "camconfig"] = camlist  # Stores the full result in this key
        if camlist is None:
            camlist = dict()
        # For the 'cameras' value in attributes, we create a short dict that uses the
        # shortname for the key and the display name for the value. { CAM1: Camera 1 }
        for camconfig in camlist:
            shortcode = camconfig.get('optionValue')
            self._attributes["cameras"][shortcode] = camconfig.get(
                'optionDisplay')
            self._camera_details[shortcode] = camconfig
            if shortcode not in self._cameras and 'group' not in camconfig:
                self._cameras[shortcode] = BlueIrisCamera(self, shortcode)
                self.logger.info(
                    "Created BlueIrisCamera for {}".format(shortcode))
            self._camera_details[LAST_UPDATE_KEY] = time.time()

    async def update_cliplist(self, camera="Index"):
        """
        Update the list of clips in attributes for specified camera. If no camera is specified, includes all cameras.
        
        :param str camera: The shortname-code for the camera to update the list for. By default, it will send
            "index" to update the list for all cameras.
        """
        if not await self.is_valid_camera(camera):
            # If you gave us an invalid camera shortname, we're going to use index.
            camera = "Index"

        if "cliplist" not in self._attributes:
            # Create the cliplist attribute
            self._attributes["cliplist"] = dict()
            for cam_shortname in self._attributes["cameras"].keys():
                if cam_shortname not in ['@Index', 'Index']:
                    self._attributes["cliplist"][cam_shortname] = []

        cliplist = await self.send_command("cliplist", {"camera": camera})

        if cliplist is None:
            # We have to have a dict() for the next step
            cliplist = dict()
        for clip in cliplist:
            # Append the clips to the cliplist attribute
            self._attributes["cliplist"][clip["camera"]].append(clip)

    async def update_alertlist(self, camera="Index"):
        """
        Update the list of alerts in attributes for specified camera. If no camera is specified, includes all cameras.
        
        :param str camera: The shortname-code for the camera to update the list for. By default, it will send
            "index" to update the list for all cameras.
        """
        if not await self.is_valid_camera(camera):
            camera = "Index"

        if "alertlist" not in self._attributes:
            self._attributes["alertlist"] = dict()
            for cam_shortname in self._attributes["cameras"].keys():
                if cam_shortname not in ['@Index', 'Index']:
                    self._attributes["alertlist"][cam_shortname] = []

        alertlist = await self.send_command("alertlist", {
            "camera": camera,
            "reset": "false"
        })
        if alertlist is not dict:
            # We have to have a dict() for the next step
            alertlist = dict()
        for alert in alertlist:
            self._attributes["alertlist"][alert["camera"]].append(alert)

    async def update_log(self):
        """Update the log attribute from the Blue Iris server."""
        log = await self.send_command("log")
        self._attributes["log"] = log

    async def update_sysconfig(self):
        """Update the system configuration status from Blue Iris."""
        if not self._attributes["iam_admin"]:
            self.logger.error(
                "The sysconfig command requires admin access. Current user is NOT admin"
            )
        else:
            sysconfig = await self.send_command("sysconfig")
            self._attributes["sysconfig"] = sysconfig

    async def update_all_information(self):
        """Refresh all the information we can get from the Blue Iris server."""
        await self.update_status()
        await self.update_camlist()
        await self.update_cliplist()
        await self.update_alertlist()
        await self.update_log()
        await self.update_sysconfig()

    async def is_valid_camera(self, cam_shortcode):
        """
        Return True if cam_shortcode is a valid camera known to Blue Iris.
        
        :param str cam_shortcode: Camera shortcode to check for validity.
        """
        if not self._attributes["cameras"]:
            # Update our list of cameras if it doesn't exist.
            await self.update_camlist()
        if cam_shortcode not in self._attributes["cameras"]:
            self.logger.error(
                "{}: invalid camera provided. Choose one of {}".format(
                    cam_shortcode, self._attributes["cameras"].keys()))
            return False
        return True

    async def reset_camera(self, camera):
        """Send camconfig command to reset camera.

        :param str camera: The camera shortcode for the camera to send this command to.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "reset": "true"
            })

    async def enable_camera(self, camera, enabled=True):
        """Send camconfig command to enable camera.

        :param bool enabled: True to enable the camera, False to disable. Defaults to True.
        :param str camera: The camera shortcode for the camera to send this command to.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "enable": enabled
            })

    async def unpause_camera(self, camera):
        """Send camconfig command to pause camera.

        :param str camera: The camera shortcode for the camera to send this command to.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_CANCEL.value
            })

    async def pause_camera_indefinitely(self, camera):
        """Send camconfig command to pause camera.

        :param str camera: The camera shortcode for the camera to send this command to.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_INDEFINITELY.value
            })

    async def pause_camera_add30seconds(self, camera):
        """Send camconfig command to pause camera.

        :param str camera: The camera shortcode for the camera to send this command to.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_ADD_30_SEC.value
            })

    async def pause_camera_add1minute(self, camera):
        """Send camconfig command to pause camera.

        :param str camera: The camera shortcode for the camera to send this command to.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_ADD_1_MIN.value
            })

    async def pause_camera_add1hour(self, camera):
        """Send camconfig command to pause camera.

        :param str camera: The camera shortcode for the camera to send this command to.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_ADD_1_HOUR.value
            })

    async def pause_camera(self, camera, seconds):
        """
        Send camconfig command to pause camera for seconds (rounded down to nearest 30 seconds).
        
        :param str camera: The camera shortcode for the camera to send this command to.
        :param int seconds: The number of seconds to pause the camera (will get rounded down to nearest 30 seconds).
        """
        if seconds < 30:
            seconds = 30
        num_1hour_pauses = floor(seconds / 3600)
        num_1minute_pauses = floor(seconds / 60) - (60 * num_1hour_pauses)
        num_30second_pauses = floor(
            seconds / 30) - (2 * num_1minute_pauses) - (120 * num_1hour_pauses)
        if await self.is_valid_camera(camera):
            for x in range(num_1hour_pauses):
                await self.send_command(
                    "camconfig", {
                        "camera": camera,
                        "pause": CAMConfig.PAUSE_ADD_1_HOUR.value
                    })
            for x in range(num_1minute_pauses):
                await self.send_command(
                    "camconfig", {
                        "camera": camera,
                        "pause": CAMConfig.PAUSE_ADD_1_MIN.value
                    })
            for x in range(num_30second_pauses):
                await self.send_command(
                    "camconfig", {
                        "camera": camera,
                        "pause": CAMConfig.PAUSE_ADD_30_SEC.value
                    })

    async def set_camera_motion(self, camera, motion_enabled=True):
        """
        Send camconfig command to pause camera.

        :param str camera: The camera shortcode for the camera to send this command to.
        :param bool motion_enabled: This is True to enable motion detection, False to disable. If neither is specified,
            this will enable motion detection.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "motion": motion_enabled
            })

    async def set_camera_schedule(self, camera, camera_schedule_enabled=True):
        """
        Send camconfig command to enable or disable the caerma's custom schedule.
        
        camera - shortcode for the camera to send the command to
        camera_schedule_enabled - True to enable, False to disable (default True)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "schedule": camera_schedule_enabled
            })

    async def set_camera_ptzcycle(self, camera, preset_cycle_enabled=True):
        """
        Send camconfig command to enable or disable the preset cycle feature.
        
        :param str camera: The camera shortcode for the camera to send this command to.
        :param bool preset_cycle_enabled: True to enable, False to disable (default True)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "ptzcycle": preset_cycle_enabled
            })

    async def set_camera_ptzevent_schedule(self,
                                           camera,
                                           ptz_event_schedule_enabled=True):
        """
        Send camconfig command to enable or disable the PTZ event schedule.
        
        :param str camera: The camera shortcode for the camera to send this command to.
        :param bool ptz_event_schedule_enabled: True to enable, False to disable (default True)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "ptzevents": ptz_event_schedule_enabled
            })

    async def send_ptz_command(self, camera, command: PTZCommand):
        """
        Operate a camera's PTZ functionality.
        
        :param str camera: The camera shortcode for the camera to send this command to.
        :param PTZCommand command: a valid PTZCommand (use the enum)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("ptz", {
                "camera": camera,
                "button": command.value,
                "updown": 1
            })

    async def set_status_signal(self, signal: Signal):
        """
        Send command to set the Blue Iris server signal.
        
        :param Signal signal: The signal to set on Blue Iris server (use the enum)
        """
        await self.send_command("status", {"signal": signal.value})

    async def set_status_profile(self, profile_index: int):
        """
        Send command to set the current profile using the index of the profile.
        
        :param int profile_index: index of the profile to set.
        """
        await self.send_command("status", {"profile": profile_index})

    async def set_status_profile_by_name(self, profile_name: str):
        """
        Send command to set the current profile using the name of the profile.
        
        :param str profile_name: name of the profile you want to set
        """
        profile_ind = self._attributes["profiles"].index(profile_name)
        await self.set_status_profile(profile_ind)

    async def set_sysconfig_archive(self, archive_enabled: bool):
        """
        Send command to enable or disable web archiving.
        
        :param bool archive_enabled: True to enable web archiving, False to disable
        """
        if self._attributes["iam_admin"]:
            await self.send_command("sysconfig", {"archive": archive_enabled})

    async def set_sysconfig_schedule(self, global_schedule_enabled: bool):
        """
        Send command to enable or disable the global schedule.
        
        :param bool global_schedule_enabled: True to enable the global schedule, False to disable
        """
        if self._attributes["iam_admin"]:
            await self.send_command("sysconfig",
                                    {"schedule": global_schedule_enabled})

    async def trigger_camera_motion(self, camera):
        """
        Send trigger command to specific camera.
        
        :param str camera: The camera shortcode for the camera to send this command to.
        """
        if not self._attributes["iam_admin"]:
            self.logger.error(
                "Unable to trigger cameras without admin permissions")
            return False
        if await self.is_valid_camera(camera):
            await self.send_command("trigger", {"camera": camera})

    async def get_camera_details(self, camera_shortname):
        """
        Return the camera details for requested camera. If last update was UPDATE_THRESHOLD seconds ago, refresh.

        :param str camera_shortname: The camera shortcode for the camera to send this command to.
        """
        if time.time(
        ) - self._camera_details[LAST_UPDATE_KEY] > STALE_THRESHOLD:
            await self.update_camlist()
        return self._camera_details[camera_shortname]
