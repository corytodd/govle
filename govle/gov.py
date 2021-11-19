"""
@file gov.py
@brief Implements Govee BLE packet protocol
"""

import datetime

PROTOCOL_MAP = {
    "indicator": 0x33,
    "arg_start": 0x01,
    "limits" : {
        "gradient" : { "min": 0x14, "max": 0xFE},
        "color" : { "min": 0x00, "max": 0xFF},
        "segment" : { "min": 0x00, "max": 0xFF},
    },
    "constants" : {True: 0x01, False: 0x00},
    "commands" : {"power": 0x01, "brightness": 0x04, "gradient": 0x14, "color": 0x05},
    "args": {
        "color": {"manual": 0x02, "segment": 0x0b}
    }
}

def clamp(value, limits):
    """Clamps value to range [minimum, maximum]"""
    return min(limits["max"], max(limits["min"], value))

class Gov(object):
    """Govee packet builder"""

    def __init__(self) -> None:
        super().__init__()
        self.timestamp = datetime.datetime.now()
        self.pm = PROTOCOL_MAP
        self.__payload = [
            self.pm["indicator"],
            0x00, # Command
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, # XOR
        ]
        assert len(self.__payload) == 20, "Incorrect payload size"

    def set_power(self, on: bool):
        """Set power state
            :param on: bool True for on
            :return self
        """
        command = [self.pm["commands"]["power"], self.pm["constants"][on]]
        return self.__set_command(command)

    def set_brightness(self, level: int):
        """Set brightness
            This seems to be either 0x14-0xFE or 0-0xFF depending on the source
            so we'll allow the wider range.
            :param level: 0 to 255
            :return self
        """
        level = clamp(level, self.pm["limits"]["brightness"])
        command = [self.pm["commands"]["brightness"], level]
        return self.__set_command(command)

    def set_gradient(self, on: bool):
        """Set gradient enable state
            :param on: bool True for on
            :return self
        """
        command = [self.pm["commands"]["gradient"], self.pm["constants"][on]]
        return self.__set_command(command)

    def set_manual_color(self, rgb: tuple):
        """Set entire LED strip to one color"""
        red, green, blue = rgb
        red = clamp(red, self.pm["limits"]["color"])
        green = clamp(green, self.pm["limits"]["color"])
        blue = clamp(blue, self.pm["limits"]["color"])
        command = [self.pm["commands"]["color"], self.pm["args"]["color"]["manual"], red, green, blue,
            # 0x00, 0xFF, 0xAE, 0x54 # TODO Warm/Cold seems to be required sometimes
        ]
        return self.__set_command(command)

    def set_segment_color(self, rgb: tuple, seg: tuple):
        """Set segment of LED strip to one color"""
        red, green, blue = rgb
        left, right = seg
        red = clamp(red, self.pm["limits"]["color"])
        green = clamp(green, self.pm["limits"]["color"])
        blue = clamp(blue, self.pm["limits"]["color"])
        left = clamp(left, self.pm["limits"]["segment"])
        right = clamp(right, self.pm["limits"]["segment"])
        command = [self.pm["commands"]["color"], self.pm["args"]["color"]["segment"], red, green, blue,
            left, right
        ]
        return self.__set_command(command)

    def keep_alive(self):
        """Keep alive packet"""
        self.__payload = [0xAA, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xAB]
        return self

    def get_payload(self) -> bytearray:
        """Returns CRC'd payload as a bytearray"""
        self.__crc()
        return bytearray(self.__payload)

    def __set_command(self, command):
        """Write command bytes to paylaod
            :param command: list
        """
        self.__payload[self.pm["arg_start"]:self.pm["arg_start"]+len(command)] = command
        return self.__crc()

    def __crc(self):
        """Calculate and set XOR checksum byte"""
        self.__payload[-1] = 0
        for b in self.__payload[:-1]:
            self.__payload[-1] ^= b
        return self

    def __str__(self) -> str:
        return ",".join([f"{b:02X}" for b in self.__payload])

    def __repr__(self) -> str:
        return str(self)

    def __lt__(self, other):
        """Stupid requirement for PQ"""
        return self.timestamp < other.timestamp

    def __gt__(self, other):
        """Stupid requirement for PQ"""
        return self.timestamp > other.timestamp
