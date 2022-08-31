import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk


# TODO make arrow buttons ignore GNOME app row
# TODO add "autocomplete" support to Entry
# TODO when the input text is overfilled, expand the main window until a maximum of 1280 pixels...
#  otherwise, instantly combust and die (no, don't, this is a joke, just let it scroll)
# TODO on each keystroke, return the character typed (f,i,r,e,f,o,x), so the lexeme tree can work great
# TODO create a way to fast handle removing/adding 10 items from the gtk dropdown list
# TODO when it's a program on $PATH, and going up & down with the arrows, store the current input text at the "top row"
#  like a reverse bash termux; if we're going to execute a specific thing, show that on the input text, and make it
#  editable (so it can be executed with more parameters)...
# TODO add full accessibility support

# TODO create singleton metaclass as model
# TODO create controller to simplify interactions for MVC w/ dependency injection (Model(Controller(View)))
# TODO create history that saves BOTH the gnome apps launched, & binaries on $PATH;

# TODO add flag to launch UI on initial application launch; if it's not set, we're running as a session service...
#  otherwise, we make all initializations on first application launch, & we output errors to a dumpfile on path...
#  idk where though right now but ok
# TODO when running as a service, make sure to demote starting processes to userspace, and not root...

# https://zetcode.com/python/gtk/
class GRunner(Gtk.ApplicationWindow):

    def __init__(self, app):
        super(GRunner, self).__init__(application=app)

        self.entry = None
        self.action_label = None

        self.default_width = 500
        self.default_height = 200
        self.current_width = 500
        self.current_height = 200

        self.gnome_box = None
        self.top_box = None
        self.content_box = None
        self.wrapper_box = None

        self.init_ui(app)

    def init_ui(self, app):
        self.set_title('gRunner')
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(500, 200)

        self.action_label = Gtk.Label()
        self.action_label.set_markup(f"Switching to <b>None</b>")
        self.action_label.set_halign(Gtk.Align.CENTER)

        # https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
        self.entry = Gtk.Entry()
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "edit-delete")
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "emblem-system")
        self.entry.set_placeholder_text("...")
        self.entry.set_margin_start(0)
        self.entry.set_margin_end(0)
        self.entry.connect('icon-press', self.handle_entry_icon_buttons)

        # FIXME add 5 buttons with the top 5 most used/called gnome apps from this app (and key them to /1/2/3/4/5)
        btn1 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn2 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn3 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn4 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn5 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn1.connect('clicked', lambda _: self.set_default_size(500, 200))  # TODO CONVERT TO CONTROLLER
        btn2.connect('clicked', lambda _: self.set_default_size(500, 400))  # TODO CONVERT TO CONTROLLER
        btn3.connect('clicked', lambda _: self.set_default_size(500, 600))  # TODO CONVERT TO CONTROLLER
        btn4.connect('clicked', lambda _: self.set_default_size(500, 800))  # TODO CONVERT TO CONTROLLER
        btn5.connect('clicked', lambda _: self.entry.set_text(str(self.get_default_size())))

        self.gnome_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 25)  # 25*4 100px gap
        self.gnome_box.set_margin_start(20)
        self.gnome_box.set_margin_end(20)
        self.gnome_box.set_halign(Gtk.Align.CENTER)
        self.gnome_box.append(btn1)
        self.gnome_box.append(btn2)
        self.gnome_box.append(btn3)
        self.gnome_box.append(btn4)
        self.gnome_box.append(btn5)

        self.top_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 20)
        self.top_box.set_margin_start(20)
        self.top_box.set_margin_end(20)
        self.top_box.set_margin_top(35)
        self.top_box.set_margin_bottom(35)

        self.top_box.append(self.action_label)
        self.top_box.append(self.entry)
        self.top_box.append(self.gnome_box)
        self.top_box.set_valign(Gtk.Align.START)

        splitter = Gtk.Separator()

        self.content_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)

        self.wrapper_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.wrapper_box.append(self.top_box)
        self.wrapper_box.append(splitter)
        self.wrapper_box.append(self.content_box)

        # noinspection PyUnresolvedReferences
        self.set_child(self.wrapper_box)

        # https://docs.gtk.org/gtk4/class.EventControllerFocus.html
        win_event_focus_controller = Gtk.EventControllerFocus()
        win_event_focus_controller.connect("enter", lambda x: print(x))
        win_event_focus_controller.connect("leave", lambda x: self.close())
        self.add_controller(win_event_focus_controller)

    def handle_entry_icon_buttons(self, x, y):
        print(x, y)
        if y == Gtk.EntryIconPosition.PRIMARY:
            self.empty_entry()
        if y == Gtk.EntryIconPosition.SECONDARY:
            self.show_settings()

    def show_settings(self):
        print("Showing settings modal")

    def empty_entry(self):
        print("Deleting text")
        self.entry.set_text("")


def on_activate(app):
    win = GRunner(app)
    win.present()


def start_ui():
    app = Gtk.Application(application_id='foss.gRunner')
    app.connect('activate', on_activate)
    app.run(None)


if __name__ == "__main__":
    start_ui()
