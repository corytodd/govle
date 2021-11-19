import asyncio

from bleak import BleakScanner

from govle import color, gov, le
from govle.logging import logger


class Govle(object):
    """Creates a new Govee LE device
        async Govle("<BLE::ADDRESS>") as gle:
            gle.some_function()
    """

    def __init__(self, address: str):
        self.address = address

    async def __aenter__(self):
        self.le = le.Le()
        if not await self.le.connect(self.address):
            raise le.LeGattException(f"Failed to connect to {self.address}")
        logger.debug(f"opened govle [{self.address}]")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        _ = (exc_type, exc_value, traceback)
        await self.le.disconnet()
        logger.debug(f"closed govle [{self.address}]")

    async def set_power(self, on: bool) -> None:
        """Set power to on or off state"""
        logger.debug(f"setting power: {on}")
        packet = gov.Gov().set_power(on)
        await self.le.write(packet)

    async def set_brightness(self, level: int) -> None:
        """Set brightness level. Level is in range 0-255."""
        logger.debug(f"setting brightness: {level}")
        packet = gov.Gov().set_brightness(level)
        await self.le.write(packet)

    async def set_gradient(self, on: bool) -> None:
        """Set gradient effect to on or off"""
        logger.debug(f"setting gradient: {on}")
        packet = gov.Gov().set_gradient(on)
        await self.le.write(packet)

    async def set_color(self, rgb) -> None:
        """Set RGB color. Each color is in the range 0-255."""
        logger.debug(f"setting color: {color.to_hex(rgb)}")
        packet = gov.Gov().set_manual_color(rgb)
        await self.le.write(packet)

    async def slide(self, background=color.WHITE, spot=color.GREEN, hold=0, forward=True) -> None:
        """Moves one segment around the complete LED strip"""
        await self.set_gradient(True)

        bits = range(16) if forward else range(15, -1, -1)
        for bit in bits:
            selected = 1 << bit
            seg = gov.bitmask_to_segment(selected)
            segment_packet = gov.Gov().set_segment_color(spot, seg)
            await self.le.write(segment_packet)

            seg = gov.bitmask_to_segment(~selected)
            background_packet = gov.Gov().set_segment_color(background, seg)
            await self.le.write(background_packet)

            await asyncio.sleep(hold)

    @staticmethod
    async def discover():
        """Discover and print all BLE devices in range"""
        for device in await BleakScanner.discover():
            print(device)