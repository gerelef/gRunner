import enum
from multiprocessing.connection import Client, Listener
from typing import Callable

from loguru import logger


class Command(enum.Enum):
    CLOSE = 1
    START_GUI = 2


def notify_running_process(addr, key, cmd):
    with Client(addr, authkey=key) as serv:
        serv.send(cmd)


def loop_process(addr, key, actions: dict[Command, Callable]):
    with Listener(addr, authkey=key) as server:
        while True:
            try:
                logger.debug("Waiting for client...")

                with server.accept() as client:
                    logger.trace("Waiting for message...")
                    msg = client.recv()

                logger.debug(f"Got {msg}")
                actions[msg]()
            except Exception as e:
                logger.debug(f"Exception: {e}")


# TODO
def generate_private_key() -> bytes:
    return None


# TODO
def get_generated_private_key() -> bytes:
    return None
