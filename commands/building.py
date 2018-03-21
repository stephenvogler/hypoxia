from evennia import ObjectDB
from evennia.utils.evmenu import EvMenu
from evennia import Command

def start_build(caller):
    text = """
    Welcome to the building menu.

    Enter the name of the room you want to create, or press 'q' to quit.
    """
    options = ({"key": ("Quit", "quit", "q", "Q"),
                "desc": "Exit the build menu.",
                "goto": "end_build"},
               {"key": "_default",
                "goto": "assign_spaceobj"})
    return text, options

def assign_spaceobj(caller)

def build_room(caller, raw_string):
    name = raw_string.strip()
    text = """
    You entered '%s'. To create the room, press 'Enter'. To rename it, press 'r'.
    Exit the menu with 'q'.
    """ % name
    options = ({"key": ("Rename", "r"),
                "desc": "Rename the room to create.",
                "goto": "start_build"},
               {"key": ("Quit", "quit", "q", "Q"),
                "desc": "Exit the build menu.",
                "goto": "end_build"},
               {"key": "_default",
                "goto": "name_exit"})
    return text, options

def name_exit(self):
    text = """
    Now we're ready to create the exit.
    """

    options = ({"key": ("Quit", "quit", "q", "Q"),
     "desc": "Exit the build menu.",
     "goto": "end_build"})

    return text, options

def end_build(caller):
    text = """
    Bye!
    """
    return text, None

class CmdBuild(Command):
    """
    Usage:
      @build <type>

    Switches:
      @build/type : See what types are available to choose from

    This will walk you through creating anything that exists in the game world!
    """
    key = "@build"

    def func(self):
        # start menu
        EvMenu(self.caller, "commands.building",
               startnode="start_build",
               cmdset_mergetype="Replace")
