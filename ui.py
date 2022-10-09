import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio
from loguru import logger


# TODO add *ding* when doing invalid actions (with gnome settings)
# TODO on each keystroke, return the character typed (f,i,r,e,f,o,x), so the lexeme tree can work great
# TODO make the damn program not fucking die when opening the modal, jesus
# TODO make the damn program not fucking die when cycling TAB after the last focusable element, jesus
# TODO create a way to fast handle removing/adding 10 items from the gtk dropdown list
# TODO add full accessibility support
# TODO create first config file UI/template

# TODO create model
# TODO create controller to simplify interactions for MVC w/ dependency injection (Model(Controller(View)))
# TODO create history that saves BOTH the gnome apps launched, & binaries on $PATH;
# TODO when it's a program on $PATH, and going up & down with the arrows, store the current input text at the "top row"
#  like a reverse bash termux; if we're going to execute a specific thing, show that on the input text, and make it
#  editable (so it can be executed with more parameters)...
# TODO add "autocomplete" support to Entry
# TODO refine config file round 2

# TODO add flag to start a terminal session whenever running the command.
# TODO finish config file


class GSettings(Gtk.Dialog):
    def __init__(self, parent):
        super(GSettings, self).__init__(title="Settings", transient_for=parent)
        self.set_modal(True)
        self.set_decorated(False)
        self.set_resizable(False)
        self.response(Gtk.ResponseType.CLOSE)
        self.parent = parent

        self.set_default_size(400, 600)

        self.box = self.get_content_area()
        # self.box.append()

        self.connect("response", self.finalize)

    def finalize(self, *args):
        logger.debug(f"FINALIZING SETTINGS {args}")
        self.parent.settings_page_workaround = True


# https://zetcode.com/python/gtk/
class GRunner(Gtk.ApplicationWindow):

    def __init__(self, app):
        super(GRunner, self).__init__(application=app)

        self.entry = None
        self.entry_key_event_controller = None
        self.entry_completion = None
        self.store = None
        self.action_label = None

        self.default_width = 500
        self.default_height = 200
        self.current_width = self.default_width
        self.current_height = self.default_height

        self.gnome_box = None
        self.top_box = None
        self.content_box = None
        self.wrapper_box = None

        self.win_focus_event_controller = None
        self.settings_page_workaround = True

        self.init_ui(app)

    def init_ui(self, app):
        self.set_title('gRunner')
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(500, 200)

        self.action_label = Gtk.Label()
        self.action_label.set_markup(f"Switching to <b>None</b>")
        self.action_label.set_halign(Gtk.Align.CENTER)

        self.entry_completion = self.create_entry_completion()

        # https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
        self.entry = Gtk.Entry()
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "edit-delete")
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "emblem-system")
        self.entry.set_placeholder_text("...")
        self.entry.set_margin_start(0)
        self.entry.set_margin_end(0)
        self.entry.connect('icon-press', self.handle_entry_icon_buttons)  # TODO CONVERT TO CONTROLLER
        self.entry.set_completion(self.entry_completion)

        # FIXME add 5 buttons with the top 5 most used/called gnome apps from this app (and key them to /1/2/3/4/5)
        gnome_buttons = [self.create_gnome_app_button() for _ in range(5)]

        self.gnome_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 25)  # 25*4 100px gap
        self.gnome_box.set_halign(Gtk.Align.CENTER)
        for btn in gnome_buttons:
            self.gnome_box.append(btn)

        self.top_box = self.create_box(Gtk.Orientation.VERTICAL, 20, 35, 20, 35, 20)

        self.top_box.append(self.action_label)
        self.top_box.append(self.entry)
        self.top_box.append(self.gnome_box)
        self.top_box.set_valign(Gtk.Align.START)

        splitter = Gtk.Separator()

        self.content_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)

        self.wrapper_box = self.create_box(Gtk.Orientation.VERTICAL, 0, 0, 0, 0, 0)
        self.wrapper_box.append(self.top_box)
        self.wrapper_box.append(splitter)
        self.wrapper_box.append(self.content_box)

        # noinspection PyUnresolvedReferences
        self.set_child(self.wrapper_box)

        # https://docs.gtk.org/gtk4/class.EventControllerFocus.html
        self.win_focus_event_controller = Gtk.EventControllerFocus()
        self.win_focus_event_controller.reset()
        # self.win_focus_event_controller.connect("enter", lambda x: logger.debug(f"focus enter {XlibAdapter().get_focused_window_name()}"))
        self.win_focus_event_controller.connect("leave", self.handle_win_lost_focus_event)  # FIXME
        self.add_controller(self.win_focus_event_controller)

        self.entry_key_event_controller = Gtk.EventControllerKey()
        self.entry_key_event_controller.connect('key-released', self.handle_entry_key_released_event)
        self.entry.add_controller(self.entry_key_event_controller)

    def handle_entry_icon_buttons(self, x, y):
        logger.debug(x, y)
        if y == Gtk.EntryIconPosition.PRIMARY:
            self.empty_entry()
        if y == Gtk.EntryIconPosition.SECONDARY:
            self.show_settings()

    def show_settings(self):
        logger.debug("Showing settings modal")
        self.settings_page_workaround = False  # TODO this is a hack!

        setting_dialog = GSettings(self)
        setting_dialog.present()

    def empty_entry(self):
        logger.debug("Deleting text")
        self.entry.set_text("")

    def create_entry_completion(self):
        # TODO
        completion: Gtk.EntryCompletion = Gtk.EntryCompletion.new()
        self.store: Gtk.ListStore = Gtk.ListStore.new([str])
        self.store.append(["firefox"])
        self.store.append(["firefoz"])
        self.store.append(["firezof"])
        self.store.append(["spotify"])
        completion.set_model(self.store)
        completion.set_text_column(0)
        completion.set_inline_completion(False)
        completion.set_popup_completion(False)
        completion.set_inline_selection(False)
        return completion

    def create_gnome_app_layer(self):
        pass

    def create_gnome_app_button(self):
        btn = Gtk.Button()  # FIXME THIS SHOULD BE A GNOME APP
        btn.set_focusable(False)
        btn.connect('clicked', lambda _: logger.debug("hi"))  # TODO CONVERT TO CONTROLLER
        return btn

    def create_box(self, orientation, gap, top, right, bottom, left):
        box = Gtk.Box.new(orientation, gap)
        box.set_margin_top(top)
        box.set_margin_end(right)
        box.set_margin_bottom(bottom)
        box.set_margin_start(left)
        return box

    # noinspection PyMethodMayBeStatic
    def handle_entry_key_released_event(self, *args):
        txt = self.entry.get_text()
        logger.debug(args)
        if len(txt) > 0:
            # TODO change state here
            if txt[0] == "!":
                # execute bash command, cwd should be user home ~
                logger.debug("BASH STATE")
                pass
            elif txt[0] == "@":
                # cd to specific path and open in file manager
                logger.debug("CD STATE")
                pass
            elif txt[0] == "#":
                # search for file path and default open action (do NOT execute!)
                logger.debug("FILE STATE")
                pass
            elif txt[0] == "$":
                # SSH ALIAS STATE
                logger.debug("SSH STATE")
                pass
            else:
                # NORMAL STATE
                logger.debug("NORMAL STATE")
                pass
        logger.debug(txt)

    def handle_win_lost_focus_event(self, *_):
        if self.settings_page_workaround:
            self.close()


def on_activate(app):
    win = GRunner(app)
    win.present()


def start_ui():
    app = Gtk.Application(application_id='foss.gRunner', flags=Gio.ApplicationFlags.FLAGS_NONE)
    app.connect('activate', on_activate)
    app.run(None)


if __name__ == "__main__":
    start_ui()
