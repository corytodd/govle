from functools import wraps
import queue
import threading
import time

import pygatt
from pygatt import exceptions

from govle import gov, le
from govle.logging import logger

class LeGattException(Exception):
    """Exceptions originating from GATT interface (i.e. not this library)"""

class LeNoAdapaterException(Exception):
    """Attempted to use Govle object without an adapter"""

class LeNotConnectedException(Exception):
    """Attempted to read/write witout calling connect()"""

GOVLE_SERVICE = "00010203-0405-0607-0809-0a0b0c0d1910"
GOVLE_CHARACTERISTIC = "00010203-0405-0607-0809-0a0b0c0d2b11"
GOVLE_HANDLE = 0x15
GOVEE_KEEP_ALIVE = 2 # interval in seconds
GOVLE_THROTTLE = 0.1 # mininum time between packets in seconds

GOVLE_PRIORITY_MAX = 0
GOVLE_PRIORITY_MED = 10
GOVLE_PRIORITY_MIN = 100

def adapter_check(method):
    """Ensures there is a valid adapter or raise LeNoAdapaterException"""
    @wraps(method)
    def _impl(self, *method_args, **method_kwargs):
        if self.adapter is None:
            raise LeNoAdapaterException()
        return method(self, *method_args, **method_kwargs)
    return _impl

def connected_check(method):
    """Ensures there is a valid device or raise LeNotConnectedException"""
    @wraps(method)
    def _impl(self, *method_args, **method_kwargs):
        if not self.is_connected:
            raise LeNotConnectedException()
        return method(self, *method_args, **method_kwargs)
    return _impl

class Le(object):

    def __init__(self):
        self.__address = None
        self.adapter = None
        self.__device = None
        self.__work_q = queue.PriorityQueue()
        self.__is_keep_alive_running = False
        try:
            self.adapter = pygatt.GATTToolBackend()
            self.adapter.start()
            logger.debug(f"GATT adapter created: {self.adapter}")

            # Services the message transmit queue
            self.__transmit_worker_thread = threading.Thread(target=self.__transmit_worker, daemon=True, name="Tx Worker ")

            # Puts a keep alive message in the work Q periodically
            self.__keep_alive_thread = threading.Thread(target=self.__keep_alive, daemon=True, name="Keep Alive")
        except Exception as ex:
            raise LeGattException(ex)

    def __transmit_worker(self, retry_limit=3):
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
            if not self.__tx_with_retry(next_packet, retry_limit):
               logger.error(f"message #{message_id} failed to send")

            self.__work_q.task_done()
            logger.debug(f"message #{message_id} tx complete")

            # Throttle our transmission rate
            time.sleep(GOVLE_THROTTLE)

        logger.debug("tx worker thread stopped")
        self.__is_keep_alive_running = False

    def __keep_alive(self, interval=GOVEE_KEEP_ALIVE):
        """Put a keep-alive packet in the worker Q on the specified interval in seconds"""
        while self.__is_keep_alive_running:
            self.__work_q.put((GOVLE_PRIORITY_MAX, gov.Gov().keep_alive()))
            time.sleep(interval)
        logger.debug("keep alive thread stopped")


    @adapter_check
    def connect(self, address: str) -> bool:
        """Connect to the specified BLE address"""
        self.__address = address
        self.__device = self.adapter.connect(address)
        self.is_connected = self.__device != None

        if self.is_connected:
            self.__is_keep_alive_running = True
            self.__keep_alive_thread.start()
            self.__transmit_worker_thread.start()

        logger.debug(f"{address} connected: {self.is_connected}")
        return self.is_connected

    @adapter_check
    @connected_check
    def disconnet(self) -> None:
        """Disconnect from the current device"""
        # Stop the worker q
        self.__work_q.put((GOVLE_PRIORITY_MIN, None))

        # Wait for both threads to end
        if self.is_connected:
            self.__keep_alive_thread.join()
            self.__transmit_worker_thread.join()
            logger.debug("le worker queue/thread stopped")

        # Connection cleanup
        if self.is_connected:
            self.__device.disconnect()
        self.adapter.stop()
        logger.debug("GATT adapter stopped")

    @adapter_check
    @connected_check
    def write(self, message) -> None:
        """Put message in the transmit q"""
        self.__work_q.put((GOVLE_PRIORITY_MED, message))

    def __tx_with_retry(self, message, retries):
        """Write message to message with retry and auto-reconnect"""
        retry = 0
        success = False
        while retry < retries:
            retry += 1
            try:
                if not self.is_connected:
                    raise pygatt.exceptions.NotConnectedError()
                self.__device.char_write_handle(GOVLE_HANDLE, message.get_payload(), wait_for_response=False)
                success = True
                break
            except pygatt.exceptions.NotificationTimeout:
                # Don't care, we're not reading anything back
                success = True
                pass
            except pygatt.exceptions.NotConnectedError:
                logger.error(f"lost connection, retry attempt #{retry}")
                try:
                    self.__device = self.adapter.connect(self.__address)
                except:
                    pass
        return success