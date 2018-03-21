from evennia import CmdSet
from world.space.console_commands import *

class DefaultConsole(CmdSet):
    """
    Default CmdSet for consoles.
    """
    key = 'DefaultConsole'

    def at_cmdset_creation(self):
        """
        Called when the cmdset is created.
        """
        self.add(CmdMode())

#I know, I know ... a command in cmdset...
class CmdMode(Command):
    """
    Usage:
      cmdset [mode]

    Changes the console mode, loading the appropriate commands.
    """
    key = 'cmdset'
    locks = 'cmd:is_operator()'
    help_category = 'Console'

    def func(self):
        """
        Usag:
            cmdset <add || del> <mode>

        Add or remove modes to consoles. Look at the console to see what modes are available.
        """
        arg = self.args
        adding = 'add' in arg
        removing = 'del' in arg
        if adding:
            oper = 'add'
            mode = arg.replace('add', '').strip()
        elif removing:
            oper = 'remove'
            mode = arg.replace('del', '').strip()
        else:
            self.caller.msg('Syntax: cmdset <add | del> <mode>')
            return
        if mode not in self.obj.db.valid_modes:
            self.caller.msg('Not a valid mode: %s.' % mode)
            return
        if oper == 'add':
            if mode in self.obj.db.current_modes:
                self.caller.msg('Console already has mode: %s' % mode)
                return
            if mode == 'helm':
                self.obj.cmdset.add(HelmConsole, permanent=True)
            if mode == 'diagnostic':
                self.obj.cmdset.add(DiagnosticConsole, permanent=True)
            self.obj.db.current_modes.append(str(mode))
        if oper == 'remove':
            if mode not in self.obj.db.current_modes:
                self.caller.msg('Console does not have active mode: %s' % mode)
                return
            if mode == 'helm':
                self.obj.cmdset.delete(HelmConsole)
            if mode == 'diagnostic':
                self.obj.cmdset.delete(DiagnosticConsole)
            self.obj.db.current_modes.remove(str(mode))
        self.caller.msg('%s mode %s %s console.' % (
            'added' if oper == 'add' else 'removed', mode, 'to' if oper == 'add' else 'from'))

class HelmConsole(CmdSet):
    """
    Helm commands.
    """
    key = 'HelmConsole'

    def at_cmdset_creation(self):
        """
        Called when the cmdset is created.
        """
        self.add(CmdNavset())
        self.add(CmdNavstat())
        self.add(CmdSensors())
        self.add(CmdSrep())
        self.add(CmdLand())
