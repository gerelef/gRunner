# gRunner
Minimal GTK4 application launcher.

## Build
1. ```bash
   sudo dnf install -y \
   cairo cairo-devel* cairo-tools* \
   cairo-gobject-devel \
   python3-devel* \
   gobject-introspection-devel 
   ```
2. `pip install -r ./requirements.txt`
3. [OPTIONAL] `pip install pygobject-stubs --no-cache-dir --config-settings=config=Gtk4`

## Project status
**Stalled!** I'm waiting on the next GTK release since there's no sane way (as far as I know) to handle keyboard shortcuts, especially redirecting "global" shortcuts for accessibility (TAB, \<Shift\>TAB). Work will resume as soon as possible.
