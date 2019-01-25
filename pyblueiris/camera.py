"""Represent a Camera on a Blue Iris sever."""
import time


# Define lookup values for Camlist Data
CONF_DISPLAY_NAME = 'optionDisplay'
CONF_SHORT_NAME = 'optionValue'
CONF_FPS = 'FPS'
CONF_HEX_COLOR = 'color'
CONF_NUM_CLIPS = 'clipsCreated'
CONF_IS_ALERTING = 'isAlerting'
CONF_IS_ENABLED = 'isEnabled'
CONF_IS_ONLINE = 'isOnline'
CONF_IS_MOTION = 'isMotion'
CONF_IS_NOSIGNAL = 'isNoSignal'
CONF_IS_PAUSED = 'isPaused'
CONF_IS_TRIGGERED = 'isTriggered'
CONF_IS_RECORDING = 'isRecording'
CONF_IS_YELLOW = 'isYellow'
CONF_PROFILE = 'profile'
CONF_PTZ_SUPPORTED = 'ptz'
CONF_AUDIO_SUPPORTED = 'audio'
CONF_WIDTH = 'width'
CONF_HEIGHT = 'height'
CONF_NUM_TRIGGERS = 'nTriggers'
CONF_NUM_NOSIGNAL = 'nNoSignal'
CONF_NUM_NORECORDING = 'nClips'

# Define Default Values for Config
DEFAULT_DISPLAY_NAME = 'Camera'
DEFAULT_FPS = 0
DEFAULT_HEX_COLOR = 16777215  # (255, 255, 255)
DEFAULT_NUM_CLIPS = 0
DEFAULT_IS_ALERTING = False
DEFAULT_IS_ENABLED = False
DEFAULT_IS_ONLINE = False
DEFAULT_IS_MOTION = False
DEFAULT_IS_NOSIGNAL = False
DEFAULT_IS_PAUSED = False
DEFAULT_IS_TRIGGERED = False
DEFAULT_IS_RECORDING = False
DEFAULT_IS_YELLOW = False
DEFAULT_PROFILE = -1
DEFAULT_PTZ_SUPPORTED = False
DEFAULT_AUDIO_SUPPORTED = False
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_NUM_TRIGGERS = 0
DEFAULT_NUM_NOSIGNAL = 0
DEFAULT_NUM_NORECORDING = 0


class BlueIrisCamera:
    """Class which represents a Camera on a Blue Iris server.

    :param BlueIris bi: The Blue Iris server this camera belongs to.
    :param str camera_shortname: The shortname for this camera.
    """

    def __init__(self, bi, camera_shortname: str):
        """Initialize an object to represent a camera."""
        self._short_name = camera_shortname
        self.bi = bi
        self._mjpeg_url = "{}/mjpg/@Index".format(bi.base_url)
        self._display_name = DEFAULT_DISPLAY_NAME
        self._fps = DEFAULT_FPS
        self._color = DEFAULT_HEX_COLOR
        self._num_clips = DEFAULT_NUM_CLIPS
        self._is_alerting = DEFAULT_IS_ALERTING
        self._is_enabled = DEFAULT_IS_ENABLED
        self._is_online = DEFAULT_IS_ONLINE
        self._is_motion = DEFAULT_IS_MOTION
        self._is_nosignal = DEFAULT_IS_NOSIGNAL
        self._is_paused = DEFAULT_IS_PAUSED
        self._is_triggered = DEFAULT_IS_TRIGGERED
        self._is_recording = DEFAULT_IS_RECORDING
        self._is_yellow = DEFAULT_IS_YELLOW
        self._profile = DEFAULT_PROFILE
        self._ptz_supported = DEFAULT_PTZ_SUPPORTED
        self._audio_supported = DEFAULT_AUDIO_SUPPORTED
        self._width = DEFAULT_WIDTH
        self._height = DEFAULT_HEIGHT
        self._num_triggers = DEFAULT_NUM_TRIGGERS
        self._num_nosignal = DEFAULT_NUM_NOSIGNAL
        self._num_norecording = DEFAULT_NUM_NORECORDING
        self._last_update_time = 0

    @property
    def display_name(self):
        """:return str: Return the camera's name."""
        return self._display_name

    @property
    def short_name(self):
        """:return str: Return the camera shortcode for the camera."""
        return self._short_name

    @property
    def fps(self):
        """:return int: Return the FPS of the camera."""
        return self._fps

    @property
    def color(self):
        """:return: Return color of camera."""
        return self._color

    @property
    def num_clips(self):
        """:return int: Return the number of clips the camera has recorded."""
        return self._num_clips

    @property
    def is_alerting(self):
        """:return bool: Return True if the camera is alerting."""
        return self._is_alerting

    @property
    def is_enabled(self):
        """:return bool: Return True if the camera is enabled in Blue Iris."""
        return self._is_enabled

    @property
    def is_online(self):
        """:return bool: Return True if the camera is online."""
        return self._is_online

    @property
    def is_motion(self):
        """:return bool: Return True if the camera detects motion."""
        return self._is_motion

    @property
    def is_nosignal(self):
        """:return bool: Return True if the camera is in 'no signal' state."""
        return self._is_nosignal

    @property
    def is_paused(self):
        """:return bool: Return True if the camera is paused."""
        return self._is_paused

    @property
    def is_triggered(self):
        """:return bool: Return True if the camera is triggered."""
        return self._is_triggered

    @property
    def is_recording(self):
        """:return bool: Return True if the camera is recording."""
        return self._is_recording

    @property
    def is_yellow(self):
        """:return bool: Return True if the camera is yellow in Blue Iris."""
        return self._is_yellow

    @property
    def profile(self):
        """:return int: Return the index of the profile active on the camera."""
        return self._profile

    @property
    def ptz_supported(self):
        """:return bool: Return True if the camera has PTZ support."""
        return self._ptz_supported

    @property
    def audio_supported(self):
        """:return bool: Return True if the camera has audio support."""
        return self._audio_supported

    @property
    def width(self):
        """:return int: Return the width of the camera image."""
        return self._width

    @property
    def height(self):
        """:return int: Return the height of the camera image."""
        return self._height

    @property
    def num_triggers(self):
        """:return int: Return the number of 'trigger' events."""
        return self._num_triggers

    @property
    def num_nosignal(self):
        """:return int: Return the number of 'no signal' events."""
        return self._num_nosignal

    @property
    def num_norecording(self):
        """:return int: Return the number of 'no recording' events."""
        return self._num_norecording

    @property
    def mjpeg_url(self):
        """:return str: Return the URL to the mjpeg stream for this camera."""
        return self._mjpeg_url

    @property
    def last_update_time(self):
        """:return long: Return the EPOCH of when this object last updated its camera information."""
        return self._last_update_time

    async def update_camconfig(self):
        """Update this object's details on the camera it represents."""
        updated_data = await self.bi.get_camera_details(self._short_name)
        self.update_properties(updated_data)

    async def enable(self):
        """Enable this camera."""
        await self.bi.enable_camera(self._short_name, True)

    async def disable(self):
        """Disable this camera."""
        await self.bi.enable_camera(self._short_name, False)

    async def detect_motion(self, enabled=True):
        """Set this camera to detect motion or not.

        :param bool enabled: True to enable motion detection, False to disable. Defaults to True.
        """
        await self.bi.set_camera_motion(self._short_name, enabled)

    def update_properties(self, camlist_data: {}):
        """Update this objects properties based on a dictionary of camera data.

        The camera data dictionary should come from the `camlist` command sent to the Blue Iris server.

        :param dict() camlist_data: Dictionary of property values for this camera.
        """
        self._last_update_time = time.time()
        self._display_name = camlist_data.get(CONF_DISPLAY_NAME, DEFAULT_DISPLAY_NAME)
        self._mjpeg_url = "{}/mjpg/{}".format(self.bi.base_url, self._short_name)
        self._fps = camlist_data.get(CONF_FPS, DEFAULT_FPS)
        self._color = camlist_data.get(CONF_HEX_COLOR, DEFAULT_HEX_COLOR)
        self._num_clips = camlist_data.get(CONF_NUM_CLIPS, DEFAULT_NUM_CLIPS)
        self._is_alerting = camlist_data.get(CONF_IS_ALERTING, DEFAULT_IS_ALERTING)
        self._is_enabled = camlist_data.get(CONF_IS_ENABLED, DEFAULT_IS_ENABLED)
        self._is_online = camlist_data.get(CONF_IS_ONLINE, DEFAULT_IS_ONLINE)
        self._is_motion = camlist_data.get(CONF_IS_MOTION, DEFAULT_IS_MOTION)
        self._is_nosignal = camlist_data.get(CONF_IS_NOSIGNAL, DEFAULT_IS_NOSIGNAL)
        self._is_paused = camlist_data.get(CONF_IS_PAUSED, DEFAULT_IS_PAUSED)
        self._is_triggered = camlist_data.get(CONF_IS_TRIGGERED, DEFAULT_IS_TRIGGERED)
        self._is_recording = camlist_data.get(CONF_IS_RECORDING, DEFAULT_IS_RECORDING)
        self._is_yellow = camlist_data.get(CONF_IS_YELLOW, DEFAULT_IS_YELLOW)
        self._profile = camlist_data.get(CONF_PROFILE, DEFAULT_PROFILE)
        self._ptz_supported = camlist_data.get(CONF_PTZ_SUPPORTED, DEFAULT_PTZ_SUPPORTED)
        self._audio_supported = camlist_data.get(CONF_AUDIO_SUPPORTED, DEFAULT_AUDIO_SUPPORTED)
        self._width = camlist_data.get(CONF_WIDTH, DEFAULT_WIDTH)
        self._height = camlist_data.get(CONF_HEIGHT, DEFAULT_HEIGHT)
        self._num_triggers = camlist_data.get(CONF_NUM_TRIGGERS, DEFAULT_NUM_TRIGGERS)
        self._num_nosignal = camlist_data.get(CONF_NUM_NOSIGNAL, DEFAULT_NUM_NOSIGNAL)
        self._num_norecording = camlist_data.get(CONF_NUM_NORECORDING, DEFAULT_NUM_NORECORDING)
