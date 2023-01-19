import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any

from loguru import logger


# Writing boilerplate code to avoid writing boilerplate code!
# https://stackoverflow.com/questions/32910096/is-there-a-way-to-auto-generate-a-str-implementation-in-python
def autostr(cls):
    """Automatically implements __str__ for any class."""

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )

    cls.__str__ = __str__
    return cls


def timeit(fn):
    def wrapper(*args, **kwargs):
        st = perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            en = perf_counter()
            logger.debug(f"{fn.__name__} took {round(en - st, 4)}s")

    return wrapper


class Global:
    ROOT = Path(Path.home(), ".grunner")
    DB = Path(ROOT, "db.sqlite")
    CFG = Path(ROOT, "config.json")
    LOGS = Path(ROOT, "logs")
    # this is the $PATH bash variable
    PATH_VALUES = os.getenv("PATH").split(":")
    # these directories are primarily for desktop entries
    #  https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
    XDG_DATA_DIRS_VALUES = os.getenv("XDG_DATA_DIRS").split(":")

    GTK_GUID = "com.github.gerelef.grunner"
    APP_GUID = '.jWggbq7RQEeNXln4pnDmmg'

    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    LOGS.mkdir(mode=0o700, parents=True, exist_ok=True)


@autostr
class Configuration:
    RECURSIVE = "recursive"
    SHORTCUTS = "shortcuts"
    PATHS = "paths"
    GTK = "gtk"

    def __init__(self):
        self.data = None
        with Global.CFG.open(mode="r", encoding="utf-8") as cfg:
            self.data = json.loads(cfg.read())
        if Configuration.RECURSIVE not in self.data:
            raise ValueError(f"Key {Configuration.RECURSIVE} not found.")
        if Configuration.SHORTCUTS not in self.data:
            raise ValueError(f"Key {Configuration.SHORTCUTS} not found.")
        if Configuration.PATHS not in self.data:
            raise ValueError(f"Key {Configuration.PATHS} not found.")
        if Configuration.GTK not in self.data:
            raise ValueError(f"Key {Configuration.GTK} not found.")

    def get_recursive(self) -> bool:
        return self.data[Configuration.RECURSIVE]

    def get_shortcuts(self) -> dict[str, str]:
        return self.data[Configuration.SHORTCUTS]

    def get_paths(self) -> list[str]:
        return self.data[Configuration.PATHS]

    def get_gtk(self) -> dict[str, Any]:
        return self.data[Configuration.GTK]

    def update_recursive(self, column: bool):
        self.data[Configuration.RECURSIVE] = column

    def update_shortcuts(self, column: dict[str, str]):
        self.data[Configuration.SHORTCUTS] = column

    def update_paths(self, column: list[str]):
        self.data[Configuration.PATHS] = column

    def update_gtk(self, column: dict[str, Any]):
        self.data[Configuration.GTK] = column

    def dump(self):
        with Global.CFG.open(mode="w", encoding="utf-8") as cfg:
            cfg.write(json.dumps(self.data, indent=4))


if not Global.CFG.exists():
    _default_ff = {
        Configuration.RECURSIVE: False,
        Configuration.SHORTCUTS: {
            "quit": "Escape",
            "cycle_focus_forwards": "Tab",
            "cycle_focus_backwards": "Shift+Tab"
        },
        Configuration.PATHS: [
            # all of these directories are (primarily) for binary files, not .desktop files
            *Global.PATH_VALUES,
            # appending ./applications to the XDG dirs, since that's where .desktop files are
            *[str(Path(p, "applications")) for p in Global.XDG_DATA_DIRS_VALUES],
            # most common user-defined paths
            str(Path(Path.home(), ".local", "bin")),
            str(Path(Path.home(), ".bin")),
            str(Path(Path.home(), "bin")),
            str(Path(Path.home(), "Downloads")),
        ],
        Configuration.GTK: {
            "hitcount": 10,
            "applicationrows": 1,
        },
    }

    with Global.CFG.open(mode="w", encoding="utf-8") as cfg:
        cfg.write(json.dumps(_default_ff, indent=4))
