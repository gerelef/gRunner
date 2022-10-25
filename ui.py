import os
import sys
from typing import Callable, Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from loguru import logger

GTK_DIR = "gtk"
GTK4_ROOT = f"{GTK_DIR}{os.sep}root"
GTK4_RESULT_INFLATANT = f"{GTK_DIR}{os.sep}app_result_inflatant"
GTK4_SETTINGS = f"{GTK_DIR}{os.sep}settings_root"


class InflatantFactory:

    @staticmethod
    def create_inflatant(readable_name, path, execute: Callable[[], None], gnome_img=None) -> Gtk.Box:
        readable_lbl: Gtk.Label = Gtk.Label()
        readable_lbl.set_markup(f"<b>{readable_name}</b>")
        readable_lbl.set_can_focus(False)
        readable_lbl.set_can_target(False)
        readable_lbl.set_halign(Gtk.Align.START)
        readable_lbl.set_wrap(True)
        readable_lbl.set_wrap_mode(Gtk.WrapMode.CHAR)
        readable_lbl.set_max_width_chars(30)

        path_lbl: Gtk.Label = Gtk.Label()
        path_lbl.set_markup(f"<i>{path}</i>")
        path_lbl.set_can_focus(False)
        path_lbl.set_can_target(False)
        path_lbl.set_sensitive(False)
        path_lbl.set_halign(Gtk.Align.START)
        path_lbl.set_wrap(True)
        path_lbl.set_wrap_mode(Gtk.WrapMode.CHAR)
        path_lbl.set_max_width_chars(30)

        root_lbl_bx: Gtk.Box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        root_lbl_bx.set_can_focus(False)
        root_lbl_bx.set_can_target(False)
        root_lbl_bx.set_hexpand(True)

        root_lbl_bx.append(readable_lbl)
        root_lbl_bx.append(path_lbl)

        img: Gtk.Image = Gtk.Image.new()
        img.set_can_focus(False)
        img.set_can_target(False)
        img.set_from_icon_name("application-x-executable-symbolic")
        if gnome_img:
            # TODO add app img here
            pass

        root: Gtk.Box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 10)
        root.set_margin_start(10)
        root.set_margin_end(10)
        root.set_can_focus(True)
        root.set_can_target(True)
        root.set_hexpand(True)

        root.append(img)
        root.append(root_lbl_bx)

        # TODO controller to add to call execute() when enter or some other confirm key is pressed

        return root


class GRunner(Adw.Application):
    # TODO add ESC to "lose focus" & kill gui
    # TODO when the last TAB cycle is pressed, to the first element (so we don't lose focus & die)
    # TODO add up & down arrow to cycle focus to next/previous element of Entry
    #  https://stackoverflow.com/questions/50210510/gtk-entry-box-disable-tab-moving-focus
    # TODO make /1/2/3/4/5 call gnome btn 1 etc.

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.builder = Gtk.Builder()
        self.builder.add_from_file(GTK4_ROOT)

        self.win: Gtk.ApplicationWindow = self.builder.get_object("root")
        self.res_win: Gtk.ScrolledWindow = self.builder.get_object("root_res_win")
        self.res_lstbx: Gtk.ListBox = self.builder.get_object("root_res_lstbx")
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        """Create the main UI."""
        self.win.set_application(app)
        self.add_event_handlers()
        self.win.present()

    def add_event_handlers(self):
        destroy_on_exit = self.__create_focus_event_controller(leave=lambda _: self.win.destroy())

        self.win.add_controller(destroy_on_exit)

    def __create_focus_event_controller(self, enter: Callable[[Any], Any] = None,
                                        leave: Callable[[Any], Any] = None) -> Gtk.EventControllerFocus:
        focus_event_controller = Gtk.EventControllerFocus()
        if enter:
            focus_event_controller.connect("enter", enter)
        if leave:
            focus_event_controller.connect("leave", leave)
        return focus_event_controller

    # FIXME
    def inflate_listbox_with_mock(self):
        self.res_win.set_visible(True)
        for i in range(1, 15):
            self.res_lstbx.append(InflatantFactory.create_inflatant(f"Name{i}", f"{os.sep}path"*i, lambda: logger.debug("Hello world!")))


# https://python-gtk-3-tutorial.readthedocs.io/en/latest/builder.html
def get_ui():
    return GRunner(application_id=gtk_guid)


gtk_guid = "com.github.gerelef.grunner"
app_guid = '.jWggbq7RQEeNXln4pnDmmg'
if __name__ == "__main__":
    get_ui().run()
