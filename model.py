import os

import pexpect
from ilock import ILock, ILockException
from loguru import logger
from pathlib import Path
import pexpect as pxp
import datetime


def get_paths_in_path() -> list[Path]:
    bash_session = pxp.spawn("bash")
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

    bash_session.close()
    for path in paths:
        p = Path(path)
        if p.exists() and p.is_dir():
            filtered_paths.append(p)

    return filtered_paths


def get_paths_in_desktop_files() -> list[Path]:

    return []


def get_executable_binaries(paths: list[Path], desktop_bins: list[Path]):
    bins = []
    for path in paths:
        for element in path.glob("**/*"):
            if element.is_file() and os.access(element, os.X_OK):
                bins.append(element)

    return bins


def _main():
    path_paths = get_paths_in_path()
    desktop_paths = get_paths_in_desktop_files()
    binaries = get_executable_binaries(path_paths, desktop_paths)
    print(binaries)


class LogLevels:
    TRACE = "TRACE"        # 5
    DEBUG = "DEBUG"        # 10
    INFO = "INFO"          # 20
    SUCCESS = "SUCCESS"    # 25
    WARNING = "WARNING"    # 30
    ERROR = "ERROR"        # 40
    CRITICAL = "CRITICAL"  # 50


if __name__ == "__main__":
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

    app_guid = '.jWggbq7RQEeNXln4pnDmmg'
    try:
        with ILock(app_guid, timeout=3):
            logger.trace("Got ILock, business as usual!")
            _main()
    except ILockException:
        logger.trace("Another instance of my app is running, exiting...")
        exit(0)
    except FileNotFoundError as exc:
        logger.critical(exc)
        exit(1)
