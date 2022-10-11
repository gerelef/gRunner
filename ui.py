import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

GTK3_DIR = "gtk3"
GTK3_ROOT = f"{GTK3_DIR}{os.sep}root.glade"


class Handler:
    pass

# https://python-gtk-3-tutorial.readthedocs.io/en/latest/builder.html 
def start_ui():
    builder: Gtk.Builder = Gtk.Builder()
    builder.add_from_file(GTK3_ROOT)
    root = builder.get_object("root")
    builder.connect_signals(Handler())
    root.show_all()
    Gtk.main()


if __name__ == "__main__":
    start_ui()
