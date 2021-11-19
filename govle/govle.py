
from govle import gov, le
from govle.logging import logger

import time

class Govle(object):

    def __init__(self, address: str):
        self.address = address

    def __enter__(self):
        self.le = le.Le()
        if not self.le.connect(self.address):
            raise le.LeGattException(f"Failed to connect to {self.address}")
        logger.debug(f"opened govle [{self.address}]")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.le.disconnet()
        logger.debug(f"closed govle [{self.address}]")

    def set_power(self, on: bool) -> None:
        packet = gov.Gov().set_power(on)
        self.le.write(packet)

    def set_brightness(self, level: int) -> None:
        packet = gov.Gov().set_brightness(level)
        self.le.write(packet)

    def set_gradient(self, on: bool) -> None:
        packet = gov.Gov().set_gradient(on)
        self.le.write(packet)

    def set_color(self, red, green, blue) -> None:
        packet = gov.Gov().set_manual_color((red, green, blue))
        self.le.write(packet)

    def slide(self) -> None:
        white = (255,255,255)
        red = (255,0,0)

        def make_seg(x):
            return x & 0xFF, (x >> 8) & 0xFF

        for bit in range(16):
            selected = 1 << bit
            seg = make_seg(selected)
            segment_packet = gov.Gov().set_segment_color(red, seg)
            self.le.write(segment_packet)

            seg = make_seg(~selected)
            backgroun_packet = gov.Gov().set_segment_color(white, seg)
            self.le.write(backgroun_packet)

