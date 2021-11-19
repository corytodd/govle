import asyncio
import queue
import threading
import time
from functools import wraps

from bleak import BleakClient

from govle import gov, le
from govle.logging import logger

GOVLE_SERVICE = "00010203-0405-0607-0809-0a0b0c0d1910"
GOVLE_CHARACTERISTIC = "00010203-0405-0607-0809-0a0b0c0d2b11"
GOVLE_HANDLE = 0x15
GOVEE_KEEP_ALIVE = 2 # interval in seconds
GOVLE_THROTTLE = 0.01 # mininum time between packets in seconds

GOVLE_PRIORITY_MAX = 0
GOVLE_PRIORITY_MED = 10
GOVLE_PRIORITY_MIN = 100

class LeNotConnectedException(Exception):
    """Attempted to read/write witout calling connect()"""


class Le(object):

    def __init__(self):
        self.__client = None
        self.__work_q = queue.PriorityQueue()
        self.__is_keep_alive_running = False

        self.__tx_loop = asyncio.get_event_loop()
        self.__keep_alive_loop = asyncio.get_event_loop()

    async def __transmit_worker(self):
        """Waits for messages and transmits them to device"""
        message_id = 0
        while True:
            message_id += 1

            # Fetch next . None means it is time to quit.
            work = self.__work_q.get()

            # We don't care about priority here
            _, next_packet = work
            if next_packet is None:
                logger.debug("tx worker received termination signal")
                break

            logger.debug(f">>#{message_id:02d}|{next_packet}")
            await self.__client.write_gatt_char(GOVLE_CHARACTERISTIC, next_packet.get_payload())

            self.__work_q.task_done()
            logger.debug(f"message #{message_id} tx complete")

            # Throttle our transmission rate
            time.sleep(GOVLE_THROTTLE)

        logger.debug("tx worker thread stopped")
        self.__is_keep_alive_running = False

    async def __keep_alive(self):
        """Put a keep-alive packet in the worker Q on the specified interval"""
        if self.__is_keep_alive_running:
            self.__work_q.put((GOVLE_PRIORITY_MAX, gov.Gov().keep_alive()))

    @property
    def is_connected(self):
        if self.__client is None:
            return False
        return self.__client.is_connected

    async def connect(self, address: str) -> bool:
        """Connect to the specified BLE address"""
        self.__client = BleakClient(address)
        await self.__client.connect()
        if self.is_connected:
            self.__is_keep_alive_running = True
            self.__keep_alive_loop.create_task(self.__keep_alive())
            self.__tx_loop.create_task(self.__transmit_worker())

        logger.debug(f"{address} connected: {self.is_connected}")
        return self.__client.is_connected

    async def disconnet(self) -> None:
        """Disconnect from the current device"""
        # Stop the worker q
        self.__work_q.put((GOVLE_PRIORITY_MIN, None))

        # Wait for both threads to end
        if self.is_connected:
            await self.__client.disconnect()
            self.__keep_alive_loop.stop()
            self.__tx_loop.stop()
            logger.debug("le worker queue/thread stopped")
        logger.debug("le shutdown complete")

    def write(self, message) -> None:
        """Put message in the transmit q"""
        self.__work_q.put((GOVLE_PRIORITY_MED, message))