"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
from evennia.utils.utils import inherits_from

def to_english(list):
    if len(list) == 0:
        return 'nothing'
    elif len(list) == 1:
        return str(list[0])
    elif len(list) == 2:
        return str(list[0] + ' and ' + list[1])
    else:
        return ', '.join(list[:len(list) - 1]) + ', and %s' % list[len(list) - 1:][0]

class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    pass
    def at_object_creation(self):
        self.db.spaceobj = None

    def return_appearance(self, looker):
        from evennia.utils import pad
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
            looker (Object): Object doing the looking.
        """
        if not looker:
            return
        visible = (con for con in self.contents if con != looker and con.access(looker, 'view'))
        exits, users, things, ships, actions = ([],
         [],
         [],
         [],
         [])
        for con in visible:
            key = con.get_display_name(looker)
            if con.db.doing:
                actions.append('%s is %s' % (con.key, to_english(con.db.doing)))
            if con.destination:
                exits.append('%s%s' % (key, (' |g<|w' if con.key else ' |g<|r') + str(con.aliases) + '|g>' if con.aliases else ''))
            elif inherits_from(con, "characters.Character"):
                users.append(key)
            elif inherits_from(con, "world.space.objects.Ship"):
                ships.append(key)
            else:
                things.append(key)
        string = '|y=' * 80 + '|n\n'
        string += '|G%s%s%s|n\n' % (self.get_display_name(looker), ' |G(|w' + str(self.db.level) + '|G)' if self.db.level else '', ' <|w' + str(self.db.spaceobj) + '|G>' if self.db.spaceobj else '')
        string += '|Y-' * 80 + '|n\n'
        desc = self.db.desc
        if desc:
            string += '%s\n' % desc
        else: string +='It is pitch black. You are likely to be eaten by a grue.\n'
        if actions:
            string += '. '.join(actions) + '.\n'
        if users:
            string += '\n%s %s here.' % (str(to_english(users)), 'is' if len(users) < 2 else 'are')
        if things:
            string += '\n|nYou see ' + str(to_english(things)) + ' here.'
        if ships:
            string += '\n%s %s landed here.' % (str(to_english(ships)), 'is' if len(ships) < 2 else 'are')
        if exits:
            string += '\n' + '|Y-' * 80 + '|n\n'
            string += '|GExits: [|w' + ' |G|||w '.join(exits) + '|G]|n'
        else: string +='\nThere are no visible exits here.'
        string += '\n' + '|Y-' * 80 + '|n'
        return string
    pass
