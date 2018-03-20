from evennia import CmdSet
from world.space.console_commands import *

class DefaultConsole(CmdSet):
    key = "Console Commands!"
    def at_cmdset_creation(self):
        """
        Consoles, yo!
        """
        self.add(NavStat())
