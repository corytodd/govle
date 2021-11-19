#!/usr/bin/env python3

import argparse
import asyncio
import sys
from govle import govle
from govle.logging import logging

from config import *

logging.getLogger('govle').setLevel(logging.DEBUG)


async def main(device_name: str, operation: str, brightness: int, color: tuple):

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
            await gle.set_brightness(brightness)
        elif operation == "color":
            await gle.set_color(*color)
        elif operation == "slide":
            for _ in range(100):
                await gle.slide()
        else:
            raise RuntimeError(f"Unknown operation: {operation}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("description='govle LED strip tool'")
    parser.add_argument("device", help="Which device to control", choices=devices.keys())

    operation_choices = ("on", "off", "gradient-on", "gradient-off", "color", "brightness", "slide", "discover")
    parser.add_argument('-o', "--operation", help="Operation to perform", choices=operation_choices, default="on")

    parser.add_argument('-l', "--level", help="Brightness level, 0-255", type=int)
    parser.add_argument('-c', "--color", nargs=3, type=int)
    args = parser.parse_args()

    if args.operation == "brightness" and args.level is None:
        parser.error("brightness operation requires --level parameter")
    elif args.operation == "color" and args.color is None:
        parser.error("color operation requires --color parameter")

    asyncio.run(main(args.device, args.operation, args.level, args.color))