import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio


# TODO create singleton metaclass as a controller

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
        self.action_label.set_markup(self.get_action_markup())
        self.action_label.set_halign(Gtk.Align.CENTER)

        self.entry = Gtk.Entry()
        self.entry.set_margin_start(0)
        self.entry.set_margin_end(0)

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

        # FIXME add 5 buttons with the top 5 most used/called gnome apps from this app (and key them to /1/2/3/4/5)

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

    def get_action_markup(self):
        return f"<i>Switching</i> to <b>None</b>"


def on_activate(app):
    win = GRunner(app)
    win.present()


if __name__ == "__main__":
    app = Gtk.Application(application_id='foss.gRunner')
    app.connect('activate', on_activate)
    app.run(None)
