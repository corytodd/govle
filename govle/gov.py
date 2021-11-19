"""
@file gov.py
@brief Implements Govee BLE packet protocol
"""
import datetime

GOVLE_SERVICE = "00010203-0405-0607-0809-0a0b0c0d1910"
GOVLE_CHARACTERISTIC = "00010203-0405-0607-0809-0a0b0c0d2b11"

H6127_PROTOCOL_MAP = {
    "packet_length": 0x14,
    "indicator": 0x33,
    "arg_start": 0x01,
    "limits" : {
        "gradient" : { "min": 0x14, "max": 0xFE},
        "color" : { "min": 0x00, "max": 0xFF},
        "brightness" : { "min": 0x14, "max": 0xFE},
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

def bitmask_to_segment(u16):
    """Converts a 16-bit field into left and right sements for Govee LED strip"""
    return u16 & 0xFF, (u16 >> 8) & 0xFF

class GovPacket(object):
    """Govee packet builder"""
    def __init__(self, pm, data=None) -> None:
        """Create a new packet
            :param pm: dict packet attributes
            :param data: optional command data to insert
        """
        # timestamp is required for message queue
        self.timestamp = datetime.datetime.now()
        self.pm = pm
        self.__payload = [
            self.pm["indicator"],
            0x00, # Command
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, # XOR
        ]
        if data:
            self.__payload[self.pm["arg_start"]:self.pm["arg_start"]+len(data)] = data
        assert len(self.__payload) == self.pm["packet_length"], "Incorrect payload size"

    def pack(self, full_packet):
        """Manually specify a complete packet"""
        self.__payload = full_packet
        assert len(self.__payload) == self.pm["packet_length"], "Incorrect payload size"

    def get_payload(self) -> bytearray:
        """Returns CRC'd payload as a bytearray"""
        self.__crc()
        return bytearray(self.__payload)

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
        """Comparison function uses timestamp property"""
        return self.timestamp < other.timestamp

    def __gt__(self, other):
        """Comparison function uses timestamp property"""
        return self.timestamp > other.timestamp


class Gov(object):
    """Govee command builder"""

    def __init__(self) -> None:
        super().__init__()
        self.pm = H6127_PROTOCOL_MAP

    def set_power(self, on: bool):
        """Create a set power packet
            :param on: bool True for on
            :return GovPacket
        """
        command = [self.pm["commands"]["power"], self.pm["constants"][on]]
        packet = GovPacket(self.pm, command)
        return packet

    def set_brightness(self, level: int):
        """Create a set brightness packet
            This seems to be either 0x14-0xFE or 0-0xFF depending on the source
            so we'll allow the wider range.
            :param level: 0 to 255
            :return GovPacket
        """
        level = clamp(level, self.pm["limits"]["brightness"])
        command = [self.pm["commands"]["brightness"], level]
        packet = GovPacket(self.pm, command)
        return packet

    def set_gradient(self, on: bool):
        """Create a set gradient enable state packet
            :param on: bool True for on
            :return GovPacket
        """
        command = [self.pm["commands"]["gradient"], self.pm["constants"][on]]
        packet = GovPacket(self.pm, command)
        return packet

    def set_manual_color(self, rgb: tuple):
        """Create a packet to set entire LED strip to one color
            :param rgb: tuple(int, int, int) color codes 0-255
            :return GovPacket
        """
        red, green, blue = rgb
        red = clamp(red, self.pm["limits"]["color"])
        green = clamp(green, self.pm["limits"]["color"])
        blue = clamp(blue, self.pm["limits"]["color"])
        command = [self.pm["commands"]["color"], self.pm["args"]["color"]["manual"], red, green, blue,
            # 0x00, 0xFF, 0xAE, 0x54 # TODO Warm/Cold seems to be required sometimes
        ]
        packet = GovPacket(self.pm, command)
        return packet

    def set_segment_color(self, rgb: tuple, seg: tuple):
        """Create a packet to set segment of LED strip to one color
            :param rgb: tuple(int, int, int) color codes 0-255
            :param seg: tuple(int, int) segment id for (left, right)
            :return GovPacket
        """
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
        packet = GovPacket(self.pm, command)
        return packet

    def keep_alive(self):
        """Create a keep alive packet
            :return GovPacket
        """
        command = [0xAA, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xAB]
        packet = GovPacket(self.pm)
        packet.pack(command)
        return packet

    def make_diys(self):
        """Builds a sample set of DIY packets
            :return list(GovPacket)
        """
        return [
            GovPacket(self.pm).pack([0xAA, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), # Keep Alive
            GovPacket(self.pm).pack([0xa1, 0x02,
             0x00, # Packet number: always zero
             0x02, # Total data packets
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), # Start Data

            GovPacket(self.pm).pack([0xa1, 0x02,
             0x01, # Packet number
             0x0a, # Name?
             0x02, # Style: Fade, Jumping, Flicker, Marquee, Music
             0x01, # Mode
             0x32, # Speed: 0x00-0x64
             0x18, # Padding
             0xff, 0x00, 0x00, # RGB
             0xff, 0x00, 0x00, # RGB
             0xff, 0x00, 0x00, # RGB
             0xff, 0xff,       # RG
             0x00              # XOR
            ]), # Data
            GovPacket(self.pm).pack([0xa1, 0x02,
             0x02, # Packet number
             0xff, # B
             0x00, 0x00, 0xff, # RGB
             0x00, 0x00, 0xff, # RGB
             0x00, 0x00, 0xff, # RGB
             0x00, 0x00, 0xff, # RGB
             0x00, 0x00, 0x00, # Padding
             0x00              # XOR
            ]), # Data

            GovPacket(self.pm).pack([0xa1, 0x02, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), # End Data
            GovPacket(self.pm).pack([0x33, 0x05, 0x0a, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), # DIY Command
        ]

