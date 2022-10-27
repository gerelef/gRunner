import datetime
import json
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from gi.repository import Gio
from ilock import ILock, ILockException
from loguru import logger

import ipc
import ui
from globals import Global, auto_str, CfgColumn


@auto_str
class Application(ABC):

    @abstractmethod
    def run(self, args: list[str] = ""):
        pass


@auto_str
class PlainApplication(Application):
    def __init__(self, p: Path, name):
        self.exec = p
        self.name = name

    def run(self, args: list[str] = ""):
        # TODO check if .run from subprocess is safer or if this is enough
        # TODO check if method we pick is actually async
        subprocess.Popen([str(self.exec)] + args)


@auto_str
class GnomeApplication(Application):
    def __init__(self, desktop_app_info: Gio.DesktopAppInfo):
        self.desktop_app_info = desktop_app_info
        # print(desktop_app_info.get_display_name())
        # print(desktop_app_info.get_description())
        # print(desktop_app_info.get_icon())
        # print(desktop_app_info.get_executable())
        # desktop_app_info.launch()
        self.path = desktop_app_info.get_executable()
        self.executable_name = self.path.split(os.sep)[-1].replace("\"", "")

    def run(self, args: list[str] = ""):
        # TODO check if this async
        self.desktop_app_info.launch()


class Cfg:
    def __init__(self):
        self.data = None
        with Global.CFG.open(mode="r", encoding="utf-8") as cfg:
            self.data = json.loads(cfg.read())
        if CfgColumn.RECURSIVE not in self.data:
            raise ValueError(f"Key {CfgColumn.RECURSIVE} not found.")
        if CfgColumn.SHORTCUTS not in self.data:
            raise ValueError(f"Key {CfgColumn.SHORTCUTS} not found.")
        if CfgColumn.PATHS not in self.data:
            raise ValueError(f"Key {CfgColumn.PATHS} not found.")

    def get_recursive(self) -> bool:
        return self.data[CfgColumn.RECURSIVE]

    def get_shortcuts(self) -> dict[str]:
        return self.data[CfgColumn.SHORTCUTS]

    def get_paths(self) -> list[str]:
        return self.data[CfgColumn.PATHS]


@auto_str
class ExecutableFinder:
    # noinspection PyTypeChecker
    def __init__(self, cfg: Cfg):
        self.recursive: bool = cfg.get_recursive()
        self.paths: list[str] = cfg.get_paths()

        # maybe rework this to use 1 interface? not sure.
        self.plain_executables: list = None
        self.gnome_executables: list = None

    def walk(self) -> list[PlainApplication]:
        executables: list[PlainApplication] = []
        for p in self.paths:
            path = Path(p)
            if path.exists() and path.is_dir():
                for current_path, dirs, files in os.walk(path):
                    for file in files:
                        fp = Path(current_path, file)
                        # TODO: if it's not a .desktop file , put in plain application,
                        #  otherwise open .desktop file and get the thingies directly
                        if os.access(fp, os.X_OK):
                            executables.append(PlainApplication(fp, file))

                    if not self.recursive:
                        break

        return executables


# TODO find a good way to implement controller with inversion of control
def run_ui():
    gui = ui.get_ui()
    gui.run()


def main():
    from time import perf_counter
    cfg: Cfg

    try:
        cfg = Cfg()
    except Exception as e:
        logger.critical(f"Tried to read cfg, but got critical error {e}")
        print(f"Tried to read cfg, but got critical error {e}", file=sys.stderr)
        exit(3)

    search_start = perf_counter()
    # noinspection PyUnboundLocalVariable
    finder = ExecutableFinder(cfg)
    finder.walk()
    search_end = perf_counter()

    logger.debug(f"executable search took {round(search_end - search_start, 3)}s")
    run_ui()
    return ipc.loop_process(address, ipc.generate_pk(), action_map)


class LogLevels:
    TRACE = "TRACE"  # 5
    DEBUG = "DEBUG"  # 10
    INFO = "INFO"  # 20
    SUCCESS = "SUCCESS"  # 25
    WARNING = "WARNING"  # 30
    ERROR = "ERROR"  # 40
    CRITICAL = "CRITICAL"  # 50


action_map = {
    ipc.Command.CLOSE: exit,
    ipc.Command.START_GUI: run_ui
}

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
            logger.trace("Got ILock, business as usual!")
            try:
                exit(main())
            finally:
                ipc.cleanup()
    except ILockException:
        logger.debug("Another instance of my app is running, notifying & exiting...")
        ipc.notify_running_process(address, ipc.get_generated_pk(), ipc.Command.START_GUI)
        exit(0)
    except FileNotFoundError as exc:
        logger.critical(exc)
        exit(1)
