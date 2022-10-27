import enum
import fnmatch
import os
import tempfile
from functools import partial
from multiprocessing.connection import Client, Listener
from secrets import token_bytes
from typing import Callable

from loguru import logger

from globals import Global


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
    with tempfile.NamedTemporaryFile(suffix=Global.APP_GUID, delete=False) as pkf:
        pkf.write(pk)
        __pkfn = pkf.name
    return pk


def get_generated_pk() -> bytes:
    global __pkfn
    match = partial(fnmatch.fnmatch, pat=f"*{Global.APP_GUID}")
    files = os.listdir(tempfile.gettempdir())
    __pkfn = files[list(map(match, files)).index(True)]
    with open(tempfile.gettempdir() + os.sep + __pkfn, "rb") as pkf:
        return pkf.read()


def cleanup():
    try:
        os.remove(__pkfn)
        logger.debug(f"deleted {__pkfn}")
    except Exception as e:
        logger.warning(f"couldn't remove {__pkfn}, got exception {e}")
