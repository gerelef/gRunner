import datetime
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Literal

import desktop_entry_lib as dtl
from ilock import ILock, ILockException
from loguru import logger

import ipc
import ui
from globals import Global, autostr, timeit, Cfg

# If we're running as root, BAIL! This is a HUGE security risk!
if os.geteuid() == 0:
    print("This application is not meant to be run as root, and doing so is a huge security risk!", file=sys.stderr)
    exit(1)


@autostr
class ExecutableFile:

    def __init__(self, directory: str, fname: str):
        self.dir = directory
        self.fname = fname
        self.path = Path(self.dir, self.fname)
        self.is_on_path = str(self.dir) in Global.PATH_VALUES

    def get_path(self):
        return self.path

    def is_bin_in_path(self):
        return self.is_on_path


@autostr
class Application(ABC):

    @abstractmethod
    def get_application_type(self) -> Literal["binary", "dotdesktop", "flatpak", "snap"]:
        pass

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_full_path(self):
        pass

    @abstractmethod
    def get_readable_path(self):
        pass

    @abstractmethod
    def run(self, args: list[str] = ""):
        pass


# TODO find a way to support snap packages
@autostr
class XDGDesktopApplication(Application):

    def __init__(self, dotdesktop_fp: Path | str, df_name: str, df_exec: Optional[str], df_icon: Optional[str]):
        self.dfp: str = str(dotdesktop_fp)
        self.name: str = df_name
        self.exec: str = df_exec
        self.icon: str = df_icon

        self.sanitized_exec = self.exec.split(" ")

    def is_bin_path_exec(self):
        return os.sep not in self.sanitized_exec[0]

    def get_application_type(self):
        if "flatpak" in self.sanitized_exec[0]:
            return "flatpak"
        # FIXME confirm this is legit
        if "snap" in self.sanitized_exec[0]:
            return "snap"

        return "dotdesktop"

    def get_name(self):
        return self.name

    def get_full_path(self) -> str:
        return self.sanitized_exec[0]

    def get_readable_path(self):
        # TODO enchance with shortening long paths/pathnames
        return self.dfp.replace(str(Path.home()), "~")

    def run(self, args: list[str] = ""):
        # TODO implement
        pass


@autostr
class ExecutableFinder:
    # noinspection PyTypeChecker
    def __init__(self, cfg: Cfg):
        self.recursive: bool = cfg.get_recursive()
        self.paths: list[str] = cfg.get_paths()

    @timeit
    def _filter_xdg_from_binary_entries(self,
                                        executable: list[ExecutableFile],
                                        xdg_applications: list[XDGDesktopApplication]):
        common_bins: list[ExecutableFile] = []
        for xdg in xdg_applications:
            for binary in executable:
                if xdg.get_full_path() == binary.fname or xdg.get_full_path() == str(binary.get_path()):
                    if binary not in common_bins:
                        common_bins.append(binary)
                    break

        for binary in common_bins:
            executable.remove(binary)

    @timeit
    def _join_application_entries(self,
                                  executables: list[ExecutableFile],
                                  dotdesktops: list[ExecutableFile]) -> list[Application]:
        # TODO get all relevant data for all dotdesktop files found
        # TODO remove the executables that are already defined in the dotdesktop list
        # Note:
        # according to the freedesktop spec (https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html)
        # the "Exec=" key is not required, if DBusActivatable is set to true; however I've found that (on my system)
        # any desktop entry, that's an "Application" & set to be shown, even if the DBusActivatable is set to true,
        # they will have a valid "Exec=" key for "compatibility reasons", as the spec suggests.
        # This, ofcourse, favours us. However, in the future, when all critical issues & other bugs have been fixed,
        # means we should definitely take a look into this.
        binary_applications: list = [] # FIXME add type
        dotdesktop_applications: list[XDGDesktopApplication] = []
        for d in dotdesktops:
            dp = d.get_path()
            if dp.exists():
                df = dtl.DesktopEntry.from_file(dp)
                if df.Type == "Application" and df.should_show():
                    dotdesktop_applications.append(
                        XDGDesktopApplication(dp, df.Name.get_translated_text(), df.Exec, df.Icon)
                    )

        self._filter_xdg_from_binary_entries(executables, dotdesktop_applications)

        # TODO continue with making executables into Applications subtype

        return binary_applications + dotdesktop_applications

    def _walk_path(self, path: Path) -> tuple[list[ExecutableFile], list[ExecutableFile]]:
        executable: list[ExecutableFile] = []
        dotdesktop: list[ExecutableFile] = []

        for current_path, _, files in os.walk(path):
            for file in files:
                fp = Path(current_path, file)
                if str(fp).endswith(".desktop"):
                    dotdesktop.append(ExecutableFile(current_path, file))
                    continue

                if os.access(fp, os.X_OK):
                    executable.append(ExecutableFile(current_path, file))

            if not self.recursive:
                break

        return executable, dotdesktop

    @timeit
    def walk(self) -> list[Application]:
        executables: list[ExecutableFile] = []
        dotdesktops: list[ExecutableFile] = []

        for p in self.paths:
            path = Path(p)
            if path.exists() and path.is_dir():
                p, g = self._walk_path(path)
                executables += p
                dotdesktops += g

        return self._join_application_entries(executables, dotdesktops)


# TODO find a good way to implement controller with inversion of control
def run_ui():
    gui = ui.get_ui()
    gui.run()


def main():
    cfg: Cfg

    try:
        cfg = Cfg()
    except Exception as e:
        logger.critical(f"Tried to read cfg, but got critical error {e}")
        print(f"Tried to read cfg, but got critical error {e}", file=sys.stderr)
        exit(3)

    # noinspection PyUnboundLocalVariable
    finder = ExecutableFinder(cfg)
    # FIXME maybe make async, and add
    finder.walk()

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
