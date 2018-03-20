from evennia import Command

class CmdMan(Command):
    """
    Usage:
      man [console] || unman [console]

    Man or unman a console.
    """
    key = 'man'
    aliases = 'unman'
    locks = 'cmd:all()'
    arg_regex = '\\s|$'
    help_category = 'Console'

    def func(self):
        target = self.caller
        console = target.search(self.args.strip())
        if 'unman' in self.cmdstring:
            if not target.db.console:
                target.msg("You're not manning anything!")
                return
            target.unman()
        else:
            if target.db.console:
                target.msg("You're already manning " +
                           target.db.console.name + '.')
                return
            if not self.args:
                target.msg('You must specify a console you wish to man.')
                return
            console = target.search(self.args.strip())
            if not console:
                return
            if not console.is_typeclass("world.space.objects.Console"):
                target.msg("You'd like that, wouldn't you?")
                return
            target.man(console)

class NavStat(Command):
    key = "navstat"
    locks = 'cmd:is_operator()'
    help_category = 'Console'
    '''
    Navstat, Yo!
    '''
    def func(self):
        return self.caller.msg("Navstating...")
