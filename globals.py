import json
from pathlib import Path


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


class Global:
    ROOT = Path(Path.home(), ".grunner")
    DB = Path(ROOT, "db.sqlite")
    CFG = Path(ROOT, "config.json")
    LOGS = Path(ROOT, "logs")

    GTK_GUID = "com.github.gerelef.grunner"
    APP_GUID = '.jWggbq7RQEeNXln4pnDmmg'

    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    LOGS.mkdir(mode=0o700, parents=True, exist_ok=True)


class CfgColumn:
    RECURSIVE = "recursive"
    SHORTCUTS = "shortcuts"
    PATHS = "paths"


if not Global.CFG.exists():
    _default_ff = {
        CfgColumn.RECURSIVE: False,
        CfgColumn.SHORTCUTS: {
            "quit": "Escape",
            "cycle_focus_forwards": "Tab",
            "cycle_focus_backwards": "Shift+Tab"
        },
        CfgColumn.PATHS: [
            # all of these directories are (primarily) for binary files, not .desktop files
            str(Path(Path.home(), ".local", "bin")),
            str(Path(Path.home(), ".bin")),
            str(Path(Path.home(), "bin")),
            str(Path(Path.home(), "Desktop")),
            str(Path(Path.home(), "Downloads")),
            str(Path("/bin")),
            str(Path("/usr/bin")),
            str(Path("/usr/local/bin")),
            str(Path("/usr/sbin")),
            str(Path("/usr/local/sbin")),
            # these directories are primarily for .desktop (GNOME) applications
            #  https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#recognized-keys
            str(Path("/usr/share/applications")),
            str(Path("/usr/local/share/applications")),
            str(Path(Path.home(), "/.local/share/applications")),
        ]
    }

    with Global.CFG.open(mode="w", encoding="utf-8") as cfg:
        cfg.write(json.dumps(_default_ff, indent=4))
