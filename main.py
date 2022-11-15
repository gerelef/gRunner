import datetime
import os
import sys
from functools import partial
from pathlib import Path

from ilock import ILock, ILockException
from loguru import logger

import discoverer
import ipc
import ui
from globals import Global, Configuration

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
    gui = ui.get_ui()
    gui.load_model(cfg, engine)
    gui.run()
    if gui.exit_status == ui.ExitStatus.SHUTDOWN:
        exit(0)


def main():
    try:
        cfg = Configuration()
    except Exception as e:
        logger.critical(f"Tried to read {Global.CFG}, but got critical error {e}")
        exit(1)

    engine = discoverer.Engine(cfg)

    action_map = {
        ipc.Command.CLOSE: exit,
        ipc.Command.START_GUI: partial(run_ui, cfg, engine)
    }

    try:
        engine.future.result()
        run_ui(cfg, engine)
        return ipc.loop_process(address, ipc.generate_pk(), action_map)
    finally:
        ipc.cleanup()



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
        with ILock(Global.APP_GUID, timeout=.001):
            logger.trace("Got ILock!")
            exit(main())
    except ILockException:
        logger.debug("Another instance of gRunner is running, notifying & exiting...")
        ipc.notify_running_process(address, ipc.get_generated_pk(), ipc.Command.START_GUI)
        exit(0)
    except FileNotFoundError as exc:
        logger.critical(exc)
        exit(1)
