import datetime
import os
import sys
from functools import partial
from pathlib import Path

from ilock import ILock, ILockException
from loguru import logger

from ui import get_ui
from engine import Engine
from globals import Global, Configuration
from ipc import Command, cleanup, loop_process, generate_pk, get_generated_pk, notify_running_process

# If we're running as root, BAIL! This is a HUGE security risk!
if os.geteuid() == 0:
    print("This application is not meant to be run as root, and doing so is a huge security risk!", file=sys.stderr)
    exit(1)


class LogLevels:
    TRACE = "TRACE"  # 5
    DEBUG = "DEBUG"  # 10
    INFO = "INFO"  # 20
    SUCCESS = "SUCCESS"  # 25
    WARNING = "WARNING"  # 30
    ERROR = "ERROR"  # 40
    CRITICAL = "CRITICAL"  # 50


def run_ui(cfg, engine):
    gui = get_ui()
    gui.load_model(cfg, engine)
    gui.run()

    match gui.exit_status:
        case gui.ExitStatus.SHUTDOWN:
            exit(0)
        case gui.ExitStatus.RELOAD:
            engine.reload()


def main():
    try:
        cfg = Configuration()
    except Exception as e:
        logger.critical(f"Tried to read {Global.CFG}, but got critical error {e}")
        exit(1)

    engine = Engine(cfg)

    action_map = {
        Command.CLOSE: exit,
        Command.START_GUI: partial(run_ui, cfg, engine)
    }

    run_ui(cfg, engine)
    try:
        return loop_process(address, generate_pk(), action_map)
    finally:
        cleanup()


if __name__ == "__main__":
    address = ('localhost', 23012)

    logger.add(
        level=LogLevels.TRACE,
        sink=Path(Global.LOGS, f"grunner-{datetime.datetime.utcnow()}.log"),
        enqueue=True,
        rotation="4 weeks",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,  # FIXME set false in production
        catch=False
    )
    try:
        with ILock(Global.APP_GUID, timeout=.005):
            logger.trace("Got ILock!")
            exit(main())
    except ILockException:
        logger.debug("Another instance of gRunner is running, notifying & exiting...")
        notify_running_process(address, get_generated_pk(), Command.START_GUI)
        exit(0)
    except FileNotFoundError as exc:
        logger.critical(exc)
        exit(1)
