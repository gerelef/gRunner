import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


# TODO create singleton metaclass as a controller

# https://zetcode.com/python/gtk/
class GRunner(Gtk.ApplicationWindow):

    def __init__(self, app):
        super(GRunner, self).__init__(application=app)

        self.main_box = None
        self.entry = None
        self.action_label = None
        self.mode_name = "Switching"
        self.mode_symbol = "to"
        self.mode_action = "None"

        self.init_ui(app)

    def init_ui(self, app):
        self.set_title('gRunner')
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(500, 1000)

        self.action_label = Gtk.Label()
        self.action_label.set_markup(self.get_action_markup())
        self.action_label.set_halign(Gtk.Align.CENTER)

        self.entry = Gtk.Entry()
        self.entry.set_margin_start(20)
        self.entry.set_margin_end(20)

        self.main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.main_box.set_margin_start(5)
        self.main_box.set_margin_end(5)
        self.main_box.set_margin_top(5)
        self.main_box.set_margin_bottom(5)

        # FIXME add 5 buttons with the top 5 most used/called gnome apps from this app (and key them to /1/2/3/4/5)

        self.main_box.append(self.action_label)
        self.main_box.append(self.entry)
        self.main_box.set_valign(Gtk.Align.START)

        # noinspection PyUnresolvedReferences
        self.set_child(self.main_box)

    def get_action_markup(self):
        return f"{self.mode_name} {self.mode_symbol} <b>{self.mode_action}</b>"


def on_activate(app):
    win = GRunner(app)
    win.present()


if __name__ == "__main__":
    app = Gtk.Application(application_id='foss.gRunner')
    app.connect('activate', on_activate)
    app.run(None)
