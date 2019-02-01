from enum import Enum


def has_value(enum: Enum, value):
    """:bool: Return True if `value` is a valid member of `enum`.

    You can check either the string (GREEN, RED..) or the value (0, 1..).

    Parameters:
        enum: The enumeration to check for `value` in.
        value: The enum string key or its int value.

    Returns: 
        True if the value is within this enum, False if it isn't.
    """
    if isinstance(value, str):
        # We were provided a string, let's check it
        return value in enum.__members__
    else:
        # Assume we were given an int corresponding to the value assigned in this class
        # noinspection PyTypeChecker
        return any(value == item.value for item in enum)


class Signal(Enum):
    """Enumaration of the possible values of the stoplight signal property."""

    RED = 0
    """Red stoplight signal."""
    YELLOW = 2
    """Yellow stoplight signal."""
    GREEN = 1
    """Green stoplight signal."""


class PTZCommand(Enum):
    """Enumaration of the possible values for sending PTZ commands."""

    PAN_LEFT = 0
    PAN_RIGHT = 1
    TILT_UP = 2
    TILT_DOWN = 3
    CENTER = HOME = 4
    ZOOM_IN = 5
    ZOOM_OUT = 6
    POWER_50 = 8
    POWER_60 = 9
    POWER_OUTDOOR = 10
    BRIGHTNESS_0 = 11
    BRIGHTNESS_1 = 12
    BRIGHTNESS_2 = 13
    BRIGHTNESS_3 = 14
    BRIGHTNESS_4 = 15
    BRIGHTNESS_5 = 16
    BRIGHTNESS_6 = 17
    BRIGHTNESS_7 = 18
    BRIGHTNESS_8 = 19
    BRIGHTNESS_9 = 20
    BRIGHTNESS_10 = 21
    BRIGHTNESS_11 = 22
    BRIGHTNESS_12 = 23
    BRIGHTNESS_13 = 24
    BRIGHTNESS_14 = 25
    BRIGHTNESS_15 = 26
    CONTRAST_0 = 27
    CONTRAST_1 = 28
    CONTRAST_2 = 29
    CONTRAST_3 = 30
    CONTRAST_4 = 31
    CONTRAST_5 = 32
    CONTRAST_6 = 33
    IR_ON = 34
    IR_OFF = 35
    PRESET_1 = 101
    PRESET_2 = 102
    PRESET_3 = 103
    PRESET_4 = 104
    PRESET_5 = 105
    PRESET_6 = 106
    PRESET_7 = 107
    PRESET_8 = 108
    PRESET_9 = 109
    PRESET_10 = 110
    PRESET_11 = 111
    PRESET_12 = 112
    PRESET_13 = 113
    PRESET_14 = 114
    PRESET_15 = 115
    PRESET_16 = 116
    PRESET_17 = 117
    PRESET_18 = 118
    PRESET_19 = 119
    PRESET_20 = 120


class CAMConfig(Enum):
    """Enumaration of the possible values used when changing CAMConfig."""

    PAUSE_INDEFINITELY = -1
    PAUSE_CANCEL = 0
    PAUSE_ADD_30_SEC = 1
    PAUSE_ADD_1_MIN = 2
    PAUSE_ADD_1_HOUR = 3


LOG_SEVERITY = {0: "INFO", 1: "WARNING", 2: "ERROR"}
