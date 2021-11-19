#!/usr/bin/env python3

import argparse
import asyncio
import sys
from govle import govle, color
from govle.logging import logging

from config import *

logging.getLogger('govle').setLevel(logging.DEBUG)


async def main():
    parser = argparse.ArgumentParser("description='govle LED strip tool'")
    parser.add_argument("device", help="Which device to control", choices=devices.keys())
    parser.add_argument('-o', "--operation", help="Operation to perform", default="discover")
    parser.add_argument('-l', "--level", help="Brightness level, 0-255", type=int)
    parser.add_argument('-r', "--rgb", nargs=3, type=int)
    args = parser.parse_args()

    if args.operation == "brightness" and args.level is None:
        parser.error("brightness operation requires --level parameter")
    elif args.operation == "color" and args.rgb is None:
        parser.error("color operation requires --rgb parameter")

    device_name = args.device
    operation = args.operation
    level = args.level
    rgb = args.rgb

    if operation == "discover":
        await govle.Govle.discover()
        return

    async with govle.Govle(devices[device_name]) as gle:
        if operation == "on":
            await gle.set_power(True)
        elif operation == "off":
            await gle.set_power(False)
        elif operation == "gradient-on":
            await gle.set_gradient(True)
        elif operation == "gradient-off":
            await gle.set_gradient(False)
        elif operation == "brightness":
            await gle.set_brightness(level)
        elif operation == "color":
            await gle.set_color(rgb)
        elif operation == "slide":
            forward = True
            back, spot = color.get_random_complementary_pair()
            for _ in range(100):
                await gle.slide(back, spot, hold=0.1, forward=forward)
                forward = not forward
        elif operation == "diy":
            await gle.diy()
        else:
            parser.error(f"unknown operation '{operation}'")

if __name__ == "__main__":
    asyncio.run(main())