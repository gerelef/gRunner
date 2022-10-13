import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

GTK_DIR = "gtk"
GTK4_ROOT = f"{GTK_DIR}{os.sep}root"
GTK4_RESULT_INFLATANT = f"{GTK_DIR}{os.sep}app_result_inflatant"
GTK4_SETTINGS = f"{GTK_DIR}{os.sep}settings_root"


class GRunner(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.win = None
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        builder = Gtk.Builder()
        builder.add_from_file(GTK4_ROOT)
        self.win = builder.get_object("root")
        self.win.set_application(app)
        self.win.present()


# https://python-gtk-3-tutorial.readthedocs.io/en/latest/builder.html
def start_ui():
    ui = GRunner(application_id="foss.gerelef.grunner")
    ui.run(sys.argv)


if __name__ == "__main__":
    start_ui()
