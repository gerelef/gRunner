import os
import re
from typing import Callable, Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from loguru import logger

GTK_DIR = "gtk"
GTK4_ROOT = f"{GTK_DIR}{os.sep}root"
GTK4_SETTINGS = f"{GTK_DIR}{os.sep}settings_root"


class GtkStaticFactory:

    @staticmethod
    def create_gtk_box_inflatant(readable_name, path, gnome_img=None) -> Gtk.Box:
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

        row = Gtk.ListBoxRow()
        row.set_child(root)

        return root

    @staticmethod
    def create_list_box_row_inflatant(child, on_activate: Callable[[], None]):
        row = Gtk.ListBoxRow()
        row.set_child(child)
        row.connect("activate", on_activate)
        return row

    @staticmethod
    def create_key_event_controller(
            im_update: Callable[[Any], None] = None,
            key_pressed: Callable[[Any], None] = None,
            key_released: Callable[[Any], None] = None,
            modifiers: Callable[[Any], None] = None) -> Gtk.EventControllerKey:
        key_event_controller = Gtk.EventControllerKey()
        if im_update:
            key_event_controller.connect("im-update", im_update)
        if key_pressed:
            key_event_controller.connect("key-pressed", key_pressed)
        if key_released:
            key_event_controller.connect("key-released", key_released)
        if modifiers:
            key_event_controller.connect("modifiers", modifiers)
        return key_event_controller

    @staticmethod
    def create_focus_event_controller(enter: Callable[[Any], None] = None,
                                      leave: Callable[[Any], None] = None) -> Gtk.EventControllerFocus:
        focus_event_controller = Gtk.EventControllerFocus()
        if enter:
            focus_event_controller.connect("enter", enter)
        if leave:
            focus_event_controller.connect("leave", leave)
        return focus_event_controller

    @staticmethod
    def create_gtk_shortcut(key, action: Gtk.ShortcutAction):
        return Gtk.Shortcut.new(
            trigger=Gtk.ShortcutTrigger.parse_string(key),
            action=action
        )


class GRunner(Adw.Application):
    # TODO when the last TAB cycle is pressed, to the first element (so we don't lose focus & die)
    # TODO make TAB cycle between entry & listbox strictly; navigation in listbox should be done by J & K (vim)
    # TODO add up & down arrow to switch focus to listbox & then focus next/previous element of Entry, strictly
    #  https://stackoverflow.com/questions/50210510/gtk-entry-box-disable-tab-moving-focus

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.builder = Gtk.Builder()
        self.builder.add_from_file(GTK4_ROOT)

        self.shortcut_controller_global: Gtk.ShortcutController = Gtk.ShortcutController()
        self.shortcut_controller_global.set_scope(Gtk.ShortcutScope.GLOBAL)

        self.win: Gtk.ApplicationWindow = self.builder.get_object("root")
        self.entry: Gtk.Entry = self.builder.get_object("root_bx_entry")
        self.gnome_btns: list[Gtk.Button] = [
            self.builder.get_object("gnome_btn0"),
            self.builder.get_object("gnome_btn1"),
            self.builder.get_object("gnome_btn2"),
            self.builder.get_object("gnome_btn3"),
            self.builder.get_object("gnome_btn4")
        ]
        self.res_win: Gtk.ScrolledWindow = self.builder.get_object("root_res_win")
        self.res_lstbx: Gtk.ListBox = self.builder.get_object("root_res_lstbx")
        self.connect('activate', self.on_activate)

        self.gnome_btn_re = re.compile(r"/[1-5]$")

    def on_activate(self, app):
        """Create the main UI."""
        self.win.set_application(app)
        self.add_controllers()
        self.__inflate_listbox_with_mock()  # FIXME
        self.win.present()

    def add_controllers(self):
        self.entry.connect(
            "activate",
            self.entry_callback
        )

        #self.gnome_btns[0].connect("clicked", lambda *args: self.res_win.set_visible(not self.res_win.get_visible()))

        self.shortcut_controller_global.add_shortcut(
            GtkStaticFactory.create_gtk_shortcut(
                "Escape",
                Gtk.CallbackAction.new(
                    callback=lambda *args: self.win.destroy()
                )
            )
        )

        self.win.add_controller(self.shortcut_controller_global)

        self.win.add_controller(
            GtkStaticFactory.create_focus_event_controller(
                leave=lambda _: self.win.destroy()
            )
        )

    def entry_callback(self, entry: Gtk.Entry):
        s = entry.get_text().strip()
        if self.gnome_btn_re.match(s):
            # OFFSET INDEX - 1 BECAUSE OF REGEX MATCH
            self.gnome_btns[int(s[1]) - 1].emit("clicked")
            self.clear_entry()
            return

        # TODO somehow, add a callback here so if it's not any /1/2/3/4/5 call, we call the function

    def clear_entry(self):
        self.entry.set_text("")

    # FIXME
    def __inflate_listbox_with_mock(self):
        self.res_win.set_visible(True)
        for i in range(1, 15):
            self.res_lstbx.append(
                GtkStaticFactory.create_list_box_row_inflatant(
                    GtkStaticFactory.create_gtk_box_inflatant(
                        f"Name{i}", f"{os.sep}path" * i
                    ),
                    lambda x: logger.debug(f"Hello world! {x}")
                )
            )


# https://python-gtk-3-tutorial.readthedocs.io/en/latest/builder.html
def get_ui():
    return GRunner(application_id=gtk_guid)


gtk_guid = "com.github.gerelef.grunner"
app_guid = '.jWggbq7RQEeNXln4pnDmmg'
if __name__ == "__main__":
    get_ui().run()
