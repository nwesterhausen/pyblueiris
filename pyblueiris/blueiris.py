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

# This was going to be used to auto-update attributes when calling the property
STALE_THRESHOLD = 5
LAST_UPDATE_KEY = "lastupdate"  # Used in a dict to store the last update time

# Creates a default logger if none is provided during instantiation
_LOGGER = logging.getLogger(__name__)


class BlueIris:
    """Class which represents a Blue Iris server.

    This class uses a provided aiohttp.ClientSession with an internal 
    helper client to talk with a Blue Iris server. Optionally you can 
    provide a logging.Logger for it to use for logs. If none is 
    provided, it will use one under its own namespace.

    Parameters:
        aiosession (aiohttp.ClientSession): Async Session for handling
            requests to the Blue Iris server.
        user (str): Username used to authenticate to the server.
        password (str): Password used to authenticate to the server.
        protocol (str): Protocol used to communicate with the server. 
            This should be either `http` or `https`.
        host (str): The IP address or FQDN of the Blue Iris server.
        port (str): The port of the Blue Iris server. This defauls to 
            match `protocol` -- 80 for `http` and 443 for `https`.
        debug (boot): Should we print extra debug messages? True if yes,
            False if no; defaults to False.
        logger (logging.Logger): The Logger to log messages to. Specify 
            your own if you want to control where the log messages go. 
            By default, uses the namespace `__name__` for logging.
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
        """Initialize object for interaction with the Blue Iris server."""
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
        """
        Return a dict of the Blue Iris server properties.

        The attributes dictionary has the following structure:

        - name: The name of the Blue Iris server.
        - profiles: A list of profiles on the server.
        - iam_admin: True if our account is an admin.
        - ptz_allowed: True if we are allowed to send PTZ commands.
        - clips_allowed: True if we are allowed to access clips.
        - schedules: A list of schedules on the server.
        - version: The version of Blue Iris on the server.
        - audio_allowed: True if audio is available.
        - dio_available: True if dio is available.
        - stream_timelimit: The streaming timelimit.
        - license: The license used on the server.
        - support: The date support ends.
        - user: The username the server knows us by.
        - longitude: The server's self-reported longitude.
        - latitude: The server's self-reported latitude
        - tzone: The timezone offset.
        - streams: Available streams.
        - sounds: List of sounds that can be used.
        - www_sounds: List of sounds that can be used.
        """
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
        """
        Return the configured base url, including protocol and port.

        Examples:
            - https://192.168.1.15:8081/
            - http://blueiris.local/
            - https://blueiris.example.com:30125/
        """
        return self._base_url

    async def setup_session(self):
        """
        Log into the Blue Iris server and record basic server info.

        Set up the session with the Blue Iris server by sending a login
        command using Client. When the reply is received, we
        check for an object of data about the server. We know if the
        data dictionary is not in the reply that the login failed.

        Returns:
            False if the session did not get created successfully. True
            on success.
        """
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
        Send command to the Blue Iris server and handle the response. 

        Arguments:
            command: Command to send to the server. See the JSON API 
                reference for valid values

        Other Parameters:
            params (dict):  Parameters for the command. (Default: None)

        Returns:
            A dict of data or True on success and False on failure (if 
            no data returned from server).
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
        """
        Return list of cameras on Blue Iris.

        Returns:
            A (list) of camera shortcodes on the server.
        """
        cameras_as_list = list()
        for key in self._cameras:
            cameras_as_list.append(self._cameras[key])
        return cameras_as_list

    async def update_camlist(self):
        """
        Update the camera config and camera list in attributes.

        This function sends the 'camlist' command to the server and
        parses the result. It stores the full result in 
        self.attributes.camconfig and creates a dictionary of the camera
        shortcode and display names in self.attributes.cameras.

        This makes it easier to go through what cameras are available
        and how to reference them without cycling through a large dict.
        """
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
        Update the list of clips in attributes for specified camera. 

        If no camera is specified, this will includes all cameras.

        Arguments:
            camera (str): The shortname-code for the camera to update 
                the list for. By default, it will send "Index" to update
                the list for all cameras.
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
        Update the list of alerts in attributes for specified camera. 

        If no camera is specified, this includes all cameras.

        Arguments:
            camera (str): The shortname-code for the camera to update 
                the list for. By default, it will send "Index" to update
                the list for all cameras.
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
        Return if cam_shortcode is a valid camera known to Blue Iris.

        Arguments:
            cam_shortcode (str): The shortname-code for the camera to
                check for validity.

        Returns:
            True if cam_shortcode is a valid camera shortcode, otherwise
            False.
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

        Arguments:
            camera (str): The shortname-code for the camera to reset.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "reset": "true"
            })

    async def enable_camera(self, camera, enabled=True):
        """Send camconfig command to enable camera.

        Arguments:
            camera (str): The shortname-code for the camera to enable or
                disable.
        
        Other Parameters:
            enabled (bool): True to enable camera, False to disable.
                (Default: True)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "enable": enabled
            })

    async def unpause_camera(self, camera):
        """Send camconfig command to pause camera.
        
        Arguments:
            camera (str): The shortname-code for the camera to unpause
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_CANCEL.value
            })

    async def pause_camera_indefinitely(self, camera):
        """Send camconfig command to pause camera.
        
        Arguments:
            camera (str): The shortname-code for the camera to pause
                until it is sent an unpause command.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_INDEFINITELY.value
            })

    async def pause_camera_add30seconds(self, camera):
        """Send camconfig command to pause camera.

        
        Arguments:
            camera (str): The shortname-code for the camera to pause for
                an additional 30 seconds.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_ADD_30_SEC.value
            })

    async def pause_camera_add1minute(self, camera):
        """Send camconfig command to pause camera.

        
        Arguments:
            camera (str): The shortname-code for the camera to pause for
                an additional minute.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_ADD_1_MIN.value
            })

    async def pause_camera_add1hour(self, camera):
        """Send camconfig command to pause camera.

        Arguments:
            camera (str): The shortname-code for the camera to pause for
                an additional hour.
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "pause": CAMConfig.PAUSE_ADD_1_HOUR.value
            })

    async def pause_camera(self, camera, seconds):
        """
        Send camconfig command to pause camera for seconds (rounded down to nearest 30 seconds).
        
        Arguments:
            camera (str): The shortname-code for the camera to pause.
            seconds (int): The number of seconds to pause the camera. 
                (Note: this will get rounded down to nearest 30 seconds).
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

        
        Arguments:
            camera (str): The shortname-code for the camera to enable or
                disable motion-detection on.
        
        Other Parameters:
            motion_enabled (bool): True to enable motion detection, 
                False to disable. (Default: True)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "motion": motion_enabled
            })

    async def set_camera_schedule(self, camera, camera_schedule_enabled=True):
        """
        Send camconfig command to enable or disable the caerma's custom schedule.

        
        Arguments:
            camera (str): The shortname-code for the camera to update 
            the list for. By default, it will send "Index" to update the
            list for all cameras.
        
        Other Parameters:
            camera_schedule_enabled (bool): True to enable, False to 
                disable. (Default: True)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "schedule": camera_schedule_enabled
            })

    async def set_camera_ptzcycle(self, camera, preset_cycle_enabled=True):
        """
        Send camconfig command to enable or disable the preset cycle feature.

        
        Arguments:
            camera (str): The shortname-code for the camera to update 
            the list for. By default, it will send "Index" to update the
            list for all cameras.
        
        Other Parameters:
            preset_cycle_enabled (bool): True to enable, False to 
                disable. (Default: True)
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

        
        Arguments:
            camera (str): The shortname-code for the camera to update 
                the list for. By default, it will send "Index" to update 
                the list for all cameras.
        
        Other Parameters:
            ptz_event_schedule_enabled (bool): True to enable, False to 
                disable. (Default: True)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("camconfig", {
                "camera": camera,
                "ptzevents": ptz_event_schedule_enabled
            })

    async def send_ptz_command(self, camera, command: PTZCommand):
        """
        Operate a camera's PTZ functionality.

        
        Arguments:
            camera (str): The shortname-code for the camera to update 
                the list for. By default, it will send "Index" to update
                the list for all cameras.
            command: A valid PTZCommand. (Use the 
                pyblueiris.const.PTZCommand Enum)
        """
        if await self.is_valid_camera(camera):
            await self.send_command("ptz", {
                "camera": camera,
                "button": command.value,
                "updown": 1
            })

    async def set_status_signal(self, signal: Signal):
        """
        Set the signal on the Blue Iris.

        Arguments:
            signal: The signal to set on Blue Iris server. (Use the
                pyblueiris.const.Signal Enum.)
        """
        await self.send_command("status", {"signal": signal.value})

    async def set_status_profile(self, profile_index: int):
        """
        Set the current profile using the index of the profile.

        Arguments:
            profile_index: Index of the profile to set.
        """
        await self.send_command("status", {"profile": profile_index})

    async def set_status_profile_by_name(self, profile_name: str):
        """
        Set the current profile using the name of the profile.

        Arguments:
            profile_name: Name of the profile to set active on the server.
        """
        profile_ind = self._attributes["profiles"].index(profile_name)
        await self.set_status_profile(profile_ind)

    async def set_sysconfig_archive(self, archive_enabled: bool):
        """
        Enable or disable web archiving.

        Arguments:
            archive_enabled: True to enable web archiving, False to 
                disable
        """
        if self._attributes["iam_admin"]:
            await self.send_command("sysconfig", {"archive": archive_enabled})

    async def set_sysconfig_schedule(self, global_schedule_enabled: bool):
        """
        Enable or disable the global schedule.

        Arguments:
            global_schedule_enabled: True to enable the global schedule, 
                False to disable
        """
        if self._attributes["iam_admin"]:
            await self.send_command("sysconfig",
                                    {"schedule": global_schedule_enabled})

    async def trigger_camera_motion(self, camera):
        """
        Send trigger command to specific camera.

        Arguments:
            camera (str): The shortname-code for the camera to trigger.
        """
        if not self._attributes["iam_admin"]:
            self.logger.error(
                "Unable to trigger cameras without admin permissions")
            return False
        if await self.is_valid_camera(camera):
            await self.send_command("trigger", {"camera": camera})

    async def get_camera_details(self, camera):
        """
        Return the camera details for requested camera. 
        
        If last update was UPDATE_THRESHOLD seconds ago, it will request
        updated information for that camera from the Blue Iris server.
        
        Arguments:
            camera (str): The shortname-code for the camera to update 
            details for. 
        """
        if time.time(
        ) - self._camera_details[LAST_UPDATE_KEY] > STALE_THRESHOLD:
            await self.update_camlist()
        return self._camera_details[camera]
