from evennia import CmdSet
from world.space.space_commands import *
from world.space.console_commands import CmdMan

class SpaceCmdSet(CmdSet):
    key = "Space Commands!"
    def at_cmdset_creation(self):
        """
        Testing
        """
        self.add(CmdBoard())
        self.add(CmdSpaceobj())
        self.add(CmdMan())
