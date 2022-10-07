# gRunner
GNOME X11/XWayland application switcher & launcher.

## Features
- Application switching.
- Application launching.
- Bash command. 
- Full, detailed local history.

## Modes
- Default:

    Application switching, same workspace.
- !name

   Application launching, new instance, GNOME + $PATH binaries, without history. 
    
    Example: !joplin (execute best "joplin" match)
- !!name

    Application launching, new instance, GNOME + $PATH binaries, only history.
    
    Example: !!joplin (start best & most recent "joplin" match)
- @

    Application switching, all workspaces.
    
    Example: @pycharm (switches to pycharm which *might* be on another workspace)
- @@ 

    Application switching, last application window that was focused on.
    
    Example: @pycharm (\...we do some work\...) @@ (return to e.g. firefox)
- $cmd

    Bash command, as user. Executes ~/.bashrc first. Starts on $HOME
    
    Example: $gedit ~/.bashrc (execute gedit ~/.bashrc)
    
- $$cmd

    Bash command, as user, only history (user bash history included). Executes ~/.bashrc first. Starts on $HOME
    
    Example: $$cd (execute best & most recent "cd" match)
- /num

    Launch something from the top 5 most frequent GNOME apps (left->right).
    
    Example: /1 (launch top 1 most frequent opened GNOME app)
- /settings

    Opens the settings modal without clicking on the button.
    
    Example: /settings (open Settings modal)
