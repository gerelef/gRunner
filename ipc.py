import enum
import tempfile
import os
import fnmatch
from functools import partial
from multiprocessing.connection import Client, Listener
from typing import Callable
from secrets import token_bytes

from loguru import logger

import ui


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


__pkfn: str


def generate_pk() -> bytes:
    global __pkfn
    pk = token_bytes(128)
    with tempfile.NamedTemporaryFile(suffix=ui.app_guid, delete=False) as pkf:
        pkf.write(pk)
        __pkfn = pkf.name
    return pk


def get_generated_pk() -> bytes:
    global __pkfn
    match = partial(fnmatch.fnmatch, pat=f"*{ui.app_guid}")
    files = os.listdir(tempfile.gettempdir())
    __pkfn = files[list(map(match, files)).index(True)]
    with open(tempfile.gettempdir() + os.sep + __pkfn, "rb") as pkf:
        return pkf.read()


def cleanup():
    os.remove(__pkfn)
    logger.debug(f"deleted {__pkfn}")
