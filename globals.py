from pathlib import Path
import json


class Global:
    ROOT = Path(Path.home(), ".grunner")
    DB = Path(ROOT, "db.sqlite")
    CFG = Path(ROOT, "config.json")
    LOGS = Path(ROOT, "logs")

    GTK_GUID = "com.github.gerelef.grunner"
    APP_GUID = '.jWggbq7RQEeNXln4pnDmmg'

    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    LOGS.mkdir(mode=0o700, parents=True, exist_ok=True)


if not Global.CFG.exists():
    _default_ff = {
        "recursive": False,
        "shortcuts": {
            "quit": "Escape",
            "cycle_focus_forwards": "Tab",
            "cycle_focus_backwards": "Shift+Tab"
        },
        "paths": [
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
            str(Path("/usr/share/applications")),
            str(Path("/usr/local/share/applications")),
            str(Path(Path.home(), "/.local/share/applications")),
        ]
    }

    with Global.CFG.open(mode="w", encoding="utf-8") as cfg:
        cfg.write(json.dumps(_default_ff, indent=4))
