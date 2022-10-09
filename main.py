import datetime
import os
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod

import pexpect
import pexpect as pxp
from gi.repository import Gio
from ilock import ILock, ILockException
from loguru import logger

import ipc
import ui


# Writing boilerplate code to avoid writing boilerplate code!
# https://stackoverflow.com/questions/32910096/is-there-a-way-to-auto-generate-a-str-implementation-in-python
def auto_str(cls):
    """Automatically implements __str__ for any class."""

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )

    cls.__str__ = __str__
    return cls


@auto_str
class Application(ABC):

    @abstractmethod
    def run(self, args: list[str] = ""):
        pass


@auto_str
class PlainApplication(Application):
    def __init__(self, p):
        self.exec = p
        self.name = str(p).split(os.sep)[-1]

    def run(self, args: list[str] = ""):
        subprocess.Popen([self.exec] + args)


@auto_str
class GnomeApplication(Application):
    def __init__(self, desktop_app_info, executable):
        self.desktop_app_info = desktop_app_info
        # print(desktop_app_info.get_display_name())
        # print(desktop_app_info.get_description())
        # print(desktop_app_info.get_icon())
        # print(desktop_app_info.get_executable())
        # desktop_app_info.launch()
        self.executable_name = executable.split(os.sep)[-1].replace("\"", "")

    def run(self, args: list[str] = ""):
        self.desktop_app_info.launch()


@auto_str
class Executables:
    def __init__(self):
        self.plain_executables: list[PlainApplication] = []
        self.gnome_executables: list[GnomeApplication] = []
        self.aggregate_executables: list[Application] = []

    def check_cache(self) -> bool:
        """Checks if cache needs refreshing. Non-blocking, threaded operation."""
        # TODO
        pass

    def refresh_cache(self):
        """Refreshes cache."""
        # TODO refresh cache here!
        self.aggregate_executables = filter_execs_from_gnome(self.plain_executables, self.gnome_executables)


def parse_directory_for_executables(paths: list[Path]):
    bins: list[PlainApplication] = []
    for path in paths:
        for element in path.glob("**/*"):
            if element.is_file() and element.exists() and os.access(element, os.X_OK):
                try:
                    bins.append(PlainApplication(element))
                except PermissionError:
                    logger.warning(f"{element} raised permissionerror on resolve")
    return bins


def get_executables_in_path() -> list[PlainApplication]:
    def filter_paths():
        for path in paths:
            p = Path(path)
            if p.exists() and p.is_dir():
                try:
                    filtered_paths.append(p.resolve(True))
                except RuntimeError:
                    # https://docs.python.org/3.10/library/pathlib.html#pathlib.Path.resolve
                    # infinite loop or non executable, skipping...
                    continue

    with pxp.spawn("bash") as bash_session:
        while True:
            try:
                bash_session.expect("\r\n", timeout=1)
            except pexpect.exceptions.TIMEOUT:
                break
        bash_session.sendline("echo $PATH")
        bash_session.expect("\r\n", timeout=1)
        bash_session.expect("\r\n", timeout=5)
        paths = str(bash_session.before, "utf-8").split(":")

    filtered_paths: list[Path] = []
    filter_paths()
    bins: list[PlainApplication] = parse_directory_for_executables(filtered_paths)

    return bins


def get_executables_in_gnome() -> list[GnomeApplication]:
    bins = []

    all_apps = Gio.AppInfo.get_all()  # Returns a list of DesktopAppInfo objects (see docs)

    app: Gio.DesktopAppInfo
    for app in all_apps:
        if app.get_executable() is not None:
            bins.append(GnomeApplication(app, app.get_executable()))

    return bins


def filter_execs_from_gnome(plain: list[PlainApplication], gnome: list[GnomeApplication]) -> list[Application]:
    def exists_in_g(x: PlainApplication):
        for app in gnome:
            if x.name == app.executable_name:
                return True
        return False

    intersection = []
    for exe in plain:
        if exists_in_g(exe):
            intersection.append(exe)

    mixed = plain.copy()

    for element in intersection:
        mixed.remove(element)

    return mixed


def run_ui():
    ui.start_ui()


def _main():
    from time import perf_counter
    exes = Executables()

    start = perf_counter()
    exes.plain_executables = get_executables_in_path()
    exes.gnome_executables = get_executables_in_gnome()
    exes.refresh_cache()
    end = perf_counter()

    logger.debug(f"application processing took {round(end - start, 3)}s, running gui")
    run_ui()
    ipc.loop_process(address, ipc.generate_private_key(), action_map)


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
    app_guid = '.jWggbq7RQEeNXln4pnDmmg'

    logger.add(
        level=LogLevels.TRACE,
        sink=f"./logs/gRunner-{datetime.datetime.utcnow()}.log",
        enqueue=True,
        rotation="4 weeks",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,  # FIXME set false in production
        catch=False
    )
    try:
        with ILock(app_guid, timeout=.001):
            logger.trace("Got ILock, business as usual!")
            exit(_main())
    except ILockException:
        logger.debug("Another instance of my app is running, notifying & exiting...")
        ipc.notify_running_process(address, ipc.get_generated_private_key(), ipc.Command.START_GUI)
        exit(0)
    except FileNotFoundError as exc:
        logger.critical(exc)
        exit(1)
