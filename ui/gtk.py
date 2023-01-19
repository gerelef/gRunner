import functools
import os
import re
from enum import Enum
from typing import Callable, Any, Optional
from ui.resources import XML, get_resource
from globals import Global, Configuration
from model.engine import Engine

from loguru import logger

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class GtkStaticFactory:

    @staticmethod
    def create_result_box_inflatant(readable_name, path, gnome_img) -> Gtk.Box:
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
        img.set_from_icon_name(gnome_img)

        root: Gtk.Box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 10)
        root.set_margin_start(10)
        root.set_margin_end(10)
        root.set_can_focus(False)
        root.set_can_target(False)
        root.set_hexpand(False)

        root.append(img)
        root.append(root_lbl_bx)

        return root

    @staticmethod
    def create_result_list_box_row_inflatant(child, on_activate: Callable[[], None]):
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


class GRunnerModal:
    def __init__(self, cfg, parent: Adw.Application):
        builder = Gtk.Builder()
        st_builder = Gtk.Builder()
        ap_builder = Gtk.Builder()
        ab_builder = Gtk.Builder()
        builder.add_from_file(get_resource(XML.MODAL))
        st_builder.add_from_file(get_resource(XML.SETTINGS_BOX))
        ap_builder.add_from_file(get_resource(XML.APP_USAGE_BOX))
        ab_builder.add_from_file(get_resource(XML.ABOUT_BOX))

        self.modal: Gtk.Dialog = builder.get_object("root")

        self.dialog_stack: Gtk.Stack = builder.get_object("dialog_stack")
        self.dialog_stack_switcher: Gtk.StackSwitcher = builder.get_object("dialog_stack_switcher")

        self.settings_box: Gtk.Box = st_builder.get_object("settings_box")
        self.app_usage_box: Gtk.Box = ap_builder.get_object("app_usage_box")
        self.about_box: Gtk.Box = ab_builder.get_object("about_box")

        self._setup(parent)

    def _setup(self, parent):
        self.dialog_stack.add_titled(self.settings_box, "settings", "Settings")
        self.dialog_stack.add_titled(self.app_usage_box, "usage", "Statistics")
        self.dialog_stack.add_titled(self.about_box, "about", "About")

        self.dialog_stack_switcher.set_stack(self.dialog_stack)

        self.modal.connect(
            "response",
            lambda _, response_id: [parent._close_modal() if response_id == Gtk.ResponseType.DELETE_EVENT else None]
        )
        self.modal.connect("destroy", self.modal.destroy)

    def present(self, parent: Adw.ApplicationWindow):
        self.modal.set_transient_for(parent)
        self.modal.present()


class GRunner(Adw.Application):
    # TODO when the last TAB cycle is pressed, return to the first element (so we don't lose focus & die)
    # TODO make TAB cycle between entry & listbox strictly; navigation in listbox should be done by J & K (vim)
    #  or with arrow keys (up/down)

    # TODO add up & down arrow to switch focus to entry & then focus next/previous element of listbox, strictly
    #  https://stackoverflow.com/questions/50210510/gtk-entry-box-disable-tab-moving-focus
    # TODO there's an issue that, when using the arrow keys while focused in gtk.entry, if the gnome button wrapper
    #  box is invisible, the "cursor" will disappear when trying to move the focus "down" to the listbox

    # TODO set gnome buttons to be a configurable amount, make sure the regex matches it correctly as well
    #  if the rows are more than 1, the regex should be 11 for row 1 column 1, 22 for row 2 column 2 etc...

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        builder = Gtk.Builder()
        builder.add_from_file(get_resource(XML.ROOT))

        self.shortcut_controller_global: Gtk.ShortcutController = Gtk.ShortcutController()
        self.shortcut_controller_global.set_scope(Gtk.ShortcutScope.GLOBAL)

        self.win: Adw.ApplicationWindow = builder.get_object("root")
        self.entry: Gtk.Entry = builder.get_object("root_bx_entry")
        self.gnome_box_wrapper: Gtk.Entry = builder.get_object("root_gnome_bx")
        self.gnome_box_1: Gtk.Entry = builder.get_object("gnome_bx1")
        self.gnome_btns: list[Gtk.Button] = [
            builder.get_object("gnome_btn0"),
            builder.get_object("gnome_btn1"),
            builder.get_object("gnome_btn2"),
            builder.get_object("gnome_btn3"),
            builder.get_object("gnome_btn4")
        ]
        self.cached_button_state = False
        self.res_win: Gtk.ScrolledWindow = builder.get_object("root_res_win")
        self.res_lstbx: Gtk.ListBox = builder.get_object("root_res_lstbx")

        # we are lazy loading this because upon initialization, this will load all the data & formatting
        self.modal: Optional[GRunnerModal] = None
        self.modal_is_active = False

        self.gnome_btn_regex = re.compile(r"/[1-5]$")
        self.settings_regex = re.compile(r"/[Ss]$")
        self.quit_regex = re.compile(r"/[Qq]$")
        self.reload_regex = re.compile(r"/[Rr]$")

        self.cfg_model: Optional[Configuration] = None
        self.app_model: Optional[Engine] = None

        self._add_controllers()
        self.__inflate_listbox_with_mock()

        self.connect('activate', self._on_activate)

    def load_model(self, cfg: Configuration, apps: Engine):
        self.cfg_model = cfg
        self.app_model = apps

        # TODO get & set icons of the N most recent applicationgnome btns

    def _on_activate(self, app):
        """Create the main UI."""
        self.win.set_application(app)
        self.win.present()

    def _add_controllers(self):
        self.entry.connect(
            "activate",
            self._entry_callback
        )
        self.entry.connect(
            "changed",
            self._entry_progressive_callback
        )

        self.entry.connect(
            'icon-press',
            self._handle_entry_icon_buttons
        )

        # self.gnome_btns[0].connect("clicked", lambda *args: self.res_win.set_visible(not self.res_win.get_visible()))

        # https://askubuntu.com/questions/597395/how-to-set-custom-keyboard-shortcuts-from-terminal
        # Super key:                 <Super>
        # Control key:               <Primary> or <Control>
        # Alt key:                   <Alt>
        # Shift key:                 <Shift>
        # numbers:                   1 (just the number)
        # Spacebar:                  space
        # Slash key:                 slash
        # Asterisk key:              asterisk (so it would need `<Shift>` as well)
        # Ampersand key:             ampersand (so it would need <Shift> as well)
        #
        # a few numpad keys:
        # Numpad divide key (`/`):   KP_Divide
        # Numpad multiply (Asterisk):KP_Multiply
        # Numpad number key(s):      KP_1
        # Numpad `-`:                KP_Subtract

        self.shortcut_controller_global.add_shortcut(
            GtkStaticFactory.create_gtk_shortcut(
                "Escape",
                Gtk.CallbackAction.new(
                    callback=functools.partial(self._nuke, self.ExitStatus.QUIT)
                )
            )
        )

        # Focus the entry bar when typing slash
        self.shortcut_controller_global.add_shortcut(
            GtkStaticFactory.create_gtk_shortcut(
                "slash",
                Gtk.CallbackAction.new(
                    callback=lambda *args: self.entry.grab_focus_without_selecting()
                )
            )
        )

        self.win.add_controller(self.shortcut_controller_global)

        self.win.add_controller(
            GtkStaticFactory.create_focus_event_controller(
                leave=functools.partial(self._nuke, self.ExitStatus.LOST_FOCUS)
            )
        )

    def _handle_entry_icon_buttons(self, x, y):
        logger.debug(f"x:{type(x)} y:{type(y)}")
        if y == Gtk.EntryIconPosition.PRIMARY:
            self._entry_callback(x)
        if y == Gtk.EntryIconPosition.SECONDARY:
            self._show_modal()

    def _entry_callback(self, entry: Gtk.Entry):
        s = entry.get_text().strip()
        if self.gnome_btn_regex.match(s):
            # OFFSET INDEX - 1 BECAUSE OF REGEX MATCH
            self.gnome_btns[int(s[1]) - 1].emit("clicked")
            self._clear_entry()
            return

        if self.settings_regex.match(s):
            self._show_modal()
            self._clear_entry()
            return

        if self.quit_regex.match(s):
            self._nuke(self.ExitStatus.SHUTDOWN)
            return

        if self.reload_regex.match(s):
            self._nuke(self.ExitStatus.RELOAD)
            return

    def _entry_progressive_callback(self, entry):
        s = entry.get_text().strip()
        if 0 < len(s) <= 2:
            return

        if self.cached_button_state != bool(s):
            self.res_win.set_visible(bool(s))
            self.toggle_gnome_btns_focus(not bool(s))

            self.cached_button_state = bool(s)

    def toggle_gnome_btns_focus(self, state: bool):
        self.gnome_box_wrapper.set_can_focus(state)

    def _clear_entry(self):
        self.entry.set_text("")

    def _show_modal(self):
        self.modal = GRunnerModal(self.cfg_model, self)
        self.modal_is_active = True
        self.modal.present(self.win)

    def _close_modal(self):
        self.modal_is_active = False

    def _nuke(self, status, *args, **kwargs):
        if not self.modal_is_active:
            self.exit_status = status
            self.win.destroy()

    # FIXME remove
    def __inflate_listbox_with_mock(self):
        for i in range(1, 20):
            self.res_lstbx.append(
                GtkStaticFactory.create_result_list_box_row_inflatant(
                    GtkStaticFactory.create_result_box_inflatant(
                        f"Name{i}", f"{os.sep}path" * i, "application-x-executable-symbolic"
                    ),
                    lambda x: logger.debug(f"Hello world! {x}")
                )
            )

    class ExitStatus(Enum):
        LOST_FOCUS = 0,
        RELOAD = 1,
        QUIT = 2,
        SHUTDOWN = 3,


# https://python-gtk-3-tutorial.readthedocs.io/en/latest/builder.html
def get_ui():
    return GRunner(application_id=Global.GTK_GUID)


if __name__ == "__main__":
    get_ui().run()
