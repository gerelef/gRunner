import os
import sys
from typing import Callable, Any

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
        self.builder = Gtk.Builder()
        self.builder.add_from_file(GTK4_ROOT)

        self.win = None
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        """Create the main UI."""

        destroy_on_exit = self.__create_focus_event_controller(leave=lambda _: self.win.destroy())

        self.win = self.builder.get_object("root")
        self.win.set_application(app)
        self.win.add_controller(destroy_on_exit)
        self.win.present()

    def __create_focus_event_controller(self, enter: Callable[[Any], Any] = None,
                                        leave: Callable[[Any], Any] = None) -> Gtk.EventControllerFocus:
        focus_event_controller = Gtk.EventControllerFocus()
        if enter:
            focus_event_controller.connect("enter", enter)
        if leave:
            focus_event_controller.connect("leave", leave)
        return focus_event_controller


# https://python-gtk-3-tutorial.readthedocs.io/en/latest/builder.html
def start_ui():
    ui = GRunner(application_id=gtk_guid)
    ui.run(sys.argv)


gtk_guid = "com.github.gerelef.grunner"
app_guid = '.jWggbq7RQEeNXln4pnDmmg'
if __name__ == "__main__":
    start_ui()
