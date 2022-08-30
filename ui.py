import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio


# TODO make arrow buttons ignore GNOME app row
# TODO on lose focus, instantly combust (and die)
# TODO on minimize, instantly combust (and die)
# TODO when the input text is overfilled, expand the main window until a maximum of 1280 pixels...
#  otherwise, instantly combust and die (no, don't, this is a joke, just let it scroll)
# TODO only handle TEXT mime on drag & drop
# TODO on each keystroke, return the character typed (f,i,r,e,f,o,x), so the lexeme tree can work great
# TODO create a way to fast handle removing/adding 10 items from the gtk dropdown list
# TODO when it's a program on $PATH, and going up & down with the arrows, store the current input text at the "top row"
#  like a reverse bash termux; if we're going to execute a specific thing, show that on the input text, and make it
#  editable (so it can be executed with more parameters)...

# TODO create singleton metaclass as model
# TODO create controller to simplify interactions for MVC w/ dependency injection (Model(Controller(View)))
# TODO create history that saves BOTH the gnome apps launched, & binaries on $PATH;

# TODO add flag to launch UI on initial application launch; if it's not set, we're running as a session service...
#  otherwise, we make all initializations on first application launch, & we output errors to a dumpfile on path...
#  idk where though right now but ok

# https://zetcode.com/python/gtk/
class GRunner(Gtk.ApplicationWindow):

    def __init__(self, app):
        super(GRunner, self).__init__(application=app)

        self.entry = None
        self.action_label = None
        self.settings_button = None

        self.gnome_box = None
        self.top_box = None
        self.wrapper_box = None

        self.init_ui(app)

    def init_ui(self, app):
        self.set_title('gRunner')
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(500, 200)

        self.action_label = Gtk.Label()
        self.action_label.set_markup(f"<i>Switching</i> to <b>None</b>")
        self.action_label.set_halign(Gtk.Align.CENTER)

        self.entry = Gtk.Entry()
        self.entry.set_margin_start(0)
        self.entry.set_margin_end(0)

        # FIXME add 5 buttons with the top 5 most used/called gnome apps from this app (and key them to /1/2/3/4/5)
        btn1 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn2 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn3 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn4 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        btn5 = Gtk.Button(label="")  # FIXME THIS SHOULD BE A GNOME APP
        # https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
        self.settings_button = Gtk.Button.new_from_icon_name("emblem-system")

        self.gnome_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 25)  # 25*4 100px gap
        self.gnome_box.set_margin_start(20)
        self.gnome_box.set_margin_end(20)
        self.gnome_box.set_halign(Gtk.Align.CENTER)
        self.gnome_box.append(btn1)
        self.gnome_box.append(btn2)
        self.gnome_box.append(btn3)
        self.gnome_box.append(btn4)
        self.gnome_box.append(btn5)
        self.gnome_box.append(self.settings_button)

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

        self.wrapper_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.wrapper_box.append(self.top_box)
        self.wrapper_box.append(splitter)

        # noinspection PyUnresolvedReferences
        self.set_child(self.wrapper_box)


def on_activate(app):
    win = GRunner(app)
    win.present()


if __name__ == "__main__":
    app = Gtk.Application(application_id='foss.gRunner')
    app.connect('activate', on_activate)
    app.run(None)
