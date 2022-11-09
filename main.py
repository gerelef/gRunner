import datetime
import json
import os
import subprocess
import sys
from typing import Optional

import desktop_entry_lib as dtl
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

    def __init__(self, fdesktop_path: Path, name, icon, exec):
        # Type should be Application, consider this a given
        # icon is optional, wtf
        # if the icon doesn't exist, use the first two characters, or 1 character from the first two words
        self.fp: str = str(fdesktop_path)  # the file path of the .desktop file
        self.name: str = name.default_text
        self.icon: Optional[str] = icon
        # exec files will always be found in $PATH if it's not an absolute path, so we're good
        self.exec: str = exec

        # TODO check if the "exec" is on path (no absolute or relative path)
        #  if it is, resolve path
        self.exec_path: Path = None

    def run(self, args: list[str] = ""):
        # TODO
        #  if the exec is on path, run as-is
        #  if the exec is not on path, resolve path then run
        pass

    @classmethod
    def decode_df(cls, desktop_file) -> Optional[object]:
        entry: dtl.DesktopEntry = dtl.DesktopEntry.from_file(desktop_file)
        if not entry.should_show() or not entry.Exec:
            return None

        return cls.__init__(desktop_file, entry.Name, entry.Icon, entry.Exec)


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

    def _filter_common(self, plain, gnome) -> list[Application]:
        # TODO keep as many gnome applications and discard the duplicate plain applications in $PATH
        #  it's possible for .desktop files to be duplicate
        for g in gnome:
            print(g)
        pass

    def _walk_path(self, path: Path):
        plain: list[PlainApplication] = []
        gnome: list[GnomeApplication] = []

        for current_path, _, files in os.walk(path):
            for file in files:
                fp = Path(current_path, file)
                if str(fp).endswith(".desktop") and (g := GnomeApplication.decode_df(fp)):
                    gnome.append(g)
                    continue

                if os.access(fp, os.X_OK):
                    plain.append(PlainApplication(fp, file))

            if not self.recursive:
                break

        return plain, gnome

    def walk(self) -> list[Application]:
        plain: list[PlainApplication] = []
        gnome: list[GnomeApplication] = []

        for p in self.paths:
            path = Path(p)
            if path.exists() and path.is_dir():
                p, g = self._walk_path(path)
                plain += p
                gnome += g

        return self._filter_common(plain, gnome)


# TODO find a good way to implement controller with inversion of control
def run_ui():
    gui = ui.get_ui()
    gui.run()


def main():
    from time import perf_counter
    cfg: Cfg

    search_start = perf_counter()
    try:
        cfg = Cfg()
    except Exception as e:
        logger.critical(f"Tried to read cfg, but got critical error {e}")
        print(f"Tried to read cfg, but got critical error {e}", file=sys.stderr)
        exit(3)

    # noinspection PyUnboundLocalVariable
    finder = ExecutableFinder(cfg)
    finder.walk()

    search_end = perf_counter()
    logger.debug(f"executable search took {round(search_end - search_start, 3)}s")

    run_ui()
    try:
        return ipc.loop_process(address, ipc.generate_pk(), action_map)
    finally:
        ipc.cleanup()


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
            logger.trace("Got ILock!")
            exit(main())
    except ILockException:
        logger.debug("Another instance of gRunner is running, notifying & exiting...")
        ipc.notify_running_process(address, ipc.get_generated_pk(), ipc.Command.START_GUI)
        exit(0)
    except FileNotFoundError as exc:
        logger.critical(exc)
        exit(1)
