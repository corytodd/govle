import asyncio
import queue
import time

from bleak import BleakClient

from govle import gov
from govle.logging import logger

GOVEE_KEEP_ALIVE = 2 # interval in seconds
GOVLE_THROTTLE = 0 # mininum time between packets in seconds

# Message queue priorities
GOVLE_PRIORITY_MAX = 0
GOVLE_PRIORITY_MED = 10
GOVLE_PRIORITY_MIN = 100

class LeNotConnectedException(Exception):
    """Attempted to read/write witout calling connect()"""

class Le(object):

    def __init__(self):
        self.address = None
        self.__client = None

        # In order to guarantee our keep-alive packets arive on time, they
        # are given max priority. All other messages will be processed in
        # order in which they are received via their timestamp.
        self.__work_q = asyncio.PriorityQueue()
        self.__is_keep_alive_running = False
        self.__consumers = []

    async def __transmit_worker(self):
        """Waits for messages and transmits them to device"""
        message_id = 0

        async def tx_with_retry(packet, retries=3):
            """Simple retry loop returns success if tranmission succeeds"""
            retry = 0
            success = False
            while not success and retry < retries:
                try:
                    retry -= 1
                    await self.__client.write_gatt_char(gov.GOVLE_CHARACTERISTIC, packet.get_payload())
                    success = True
                except Exception as ex:
                    logger.exception(ex)
                    if not self.is_connected:
                        await self.connect(self.address)
            return success

        while True:
            message_id += 1

            # Wait for next message to send
            work = await self.__work_q.get()

            # Priority can be discarded, we just want the packet now
            _, next_packet = work
            if next_packet is not None:
                logger.debug(f">>#{message_id:02d}|{next_packet}")
                if await tx_with_retry(next_packet):
                    logger.debug(f"message #{message_id} tx complete")
            else:
                logger.debug("tx worker received termination signal")
                self.__work_q.task_done()
                break

            self.__work_q.task_done()

            # Throttle our transmission rate
            time.sleep(GOVLE_THROTTLE)

        logger.debug("tx worker thread stopped")
        self.__is_keep_alive_running = False

    async def __keep_alive(self):
        """Put a keep-alive packet in the worker Q on the specified interval"""
        if self.__is_keep_alive_running:
            packet = gov.Gov().keep_alive()
            await self.__work_q.put((GOVLE_PRIORITY_MAX, packet))

    @property
    def is_connected(self):
        """Returns true of device is connected"""
        if self.__client is None:
            return False
        return self.__client.is_connected

    async def connect(self, address: str) -> bool:
        """Connect to the specified BLE address"""
        self.address = address
        self.__client = BleakClient(address)
        await self.__client.connect()
        if self.is_connected:
            self.__is_keep_alive_running = True
            loop = asyncio.get_event_loop()
            self.__consumers = [
                loop.create_task(self.__keep_alive()),
                loop.create_task(self.__transmit_worker())
            ]

        logger.debug(f"{address} connected: {self.is_connected}")
        return self.__client.is_connected

    async def disconnet(self) -> None:
        """Disconnect from the current device"""
        # Stop the worker q
        await self.__work_q.put((GOVLE_PRIORITY_MIN, None))
        logger.debug("joinging work queue")
        await self.__work_q.join()
        for c in self.__consumers:
            c.cancel()

        # Wait for both threads to end
        if self.is_connected:
            await self.__client.disconnect()
            logger.debug("le worker queue/thread stopped")
        logger.debug(f"le shutdown complete: unprocessed items: {self.__work_q.qsize()}")

    async def write(self, message) -> None:
        """Put message in the transmit q"""
        await self.__work_q.put((GOVLE_PRIORITY_MED, message))