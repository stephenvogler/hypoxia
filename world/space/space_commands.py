from evennia import Command, default_cmds, search_tag, search_channel
from evennia.utils.utils import inherits_from
from evennia.utils.create import create_object
from world.space.objects import *

class CmdBoard(Command):
    """
    Usage:
      board <ship>
    """
    key = 'board'
    help_category = 'Space'

    def func(self):
        ship = self.caller.search(self.args.strip())
        if not ship:
            return
        elif not inherits_from(ship, 'world.space.objects.SpaceObject'):
            return self.caller.msg("You can't board %s!" % ship)
        elif not ship.db.board_room:
            return self.caller.msg("|rError trying to board |C%s|r. Please let a staff member know.|n" % ship)
        else:
            self.caller.notify_location("You board %s." % ship, "%s boards %s." % (self.caller, ship))
            self.caller.move_to(ship.db.board_room, quiet=True)
            self.caller.location.msg_contents("%s arrives from outside." % self.caller.name, exclude=self.caller)

class CmdSpaceobj(default_cmds.MuxCommand):
    """
    Usage:
      @spaceobj[/<switch>] <object> [= <spaceobj>]

    @spaceobj/list - List all valid space objects
    @spaceobj/create [<spaceobj> named <name>] OR [<name>=<spaceobj>]
        * @spaceobj/create ship named HMS Bounty
        * @spaceobj/create HMS Bounty = ship
    @spaceobj/attach <spaceobj> - Attach your current location to <spaceobj> (adds consoles as well)
    @spaceobj/detach - Detach your current location from its assigned spaceobj (clears consoles as well)
    """
    key = '@spaceobj'
    locks = 'perm(Builders)'
    #arg_regex = '\\s|$|/\w'
    help_category = 'Space'

    def create_spaceobj(self, name, spaceobj):

        try:
            # One entry for each type of spaceobj that can be created
            if "ship" in spaceobj:
                spaceobj = Ship
            elif "station" in spaceobj:
                spaceobj = Station
            elif "console" in spaceobj:
                spaceobj = Console
                self.caller.msg("You create a console named %s." % name)
            else:
                return self.caller.msg("Invalid type of spaceobj specified.")
            new_spaceobj = create_object(spaceobj, key = name, location = self.caller)

        except TypeError:
            self.caller.msg("You must specify the type of spaceobj you want to create!")

    def func(self):
        if self.switches:
            # Create a new spaceobj <name> of type <spaceobj>
            if "create" in self.switches:
                if not self.rhs and "named" in self.args:
                    name = self.args.split("named")[1].strip()
                    spaceobj = self.args.split("named")[0].strip()
                    return self.create_spaceobj(name, spaceobj)
                elif not self.rhs:
                    return self.caller.msg("You might want to see 'help @spaceobj'")
                else:
                    name = self.lhs
                    try:
                        spaceobj = self.rhs.lower()
                    except:
                        spaceobj = self.rhs
                    self.create_spaceobj(name, spaceobj)
            # Attach the current room to specified SpaceObject
            elif "attach" in self.switches:
                obj = self.caller.location
                if not self.args:
                    return self.caller.msg("You must specify the spaceobj you want to attach %s to." % obj)
                try:
                    spaceobj = self.caller.search(self.args,candidates=search_tag(category="spaceobj"))
                except:
                    return self.caller.msg("I'm sorry %s, I'm affraid I can't do that." % self.caller.key)
                if not spaceobj:
                    return self.caller.msg("Unknown spaceobj.")
                if spaceobj == obj.db.spaceobj:
                    return self.caller.msg("%s is already attached to %s." % (obj, spaceobj))
                if obj.db.spaceobj and not obj.db.spaceobj == spaceobj:
                    obj.db.spaceobj.db.local.remove(obj)
                    search_channel('Space')[0].msg("Room: %s has been removed from %s." % (obj, obj.db.spaceobj))
                obj.db.spaceobj = spaceobj
                if not obj in spaceobj.db.local:
                    spaceobj.db.local.append(obj)
                search_channel('Space')[0].msg("Rooom: %s has been added to %s." % (obj, spaceobj))
                for x in obj.contents:
                    if x.is_typeclass("world.space.objects.Console"):
                        if x.db.spaceobj:
                            search_channel('Space')[0].msg("Console: %s has been removed from %s." % (x.key, x.db.spaceobj))
                            x.db.spaceobj.db.consoles.remove(x)
                        x.db.spaceobj = spaceobj
                        spaceobj.db.consoles.append(x)
                        search_channel('Space')[0].msg("Console: %s has been attached to %s." % (x.key, obj.db.spaceobj))
            elif "detach" in self.switches:
                obj = self.caller.location
                spaceobj = obj.db.spaceobj
                if self.args:
                    return self.caller.msg("No arguments are necessary. If you want to remove %s from %s, just type @spaceobj/detach" % (obj, spaceobj))
                else:
                    if not spaceobj:
                        return self.caller.msg("%s is not attached to a spaceobj." % obj.key)
                    for x in obj.contents:
                        if x.is_typeclass("world.space.objects.Console"):
                            try:
                                x.db.spaceobj.db.consoles.remove(x)
                                x.db.spaceobj = None
                                search_channel('Space')[0].msg("Console: %s has been removed from %s." % (x, spaceobj))
                            except:
                                self.caller.msg("There was a problem removing %s." % x)
                    spaceobj.db.local.remove(obj)
                    obj.db.spaceobj = None
                    search_channel('Space')[0].msg("Room: %s has been removed from %s." % (obj, spaceobj))
            elif "list" in self.switches:
                return self.caller.msg("Current Space Objects: %s" % search_tag(category="spaceobj"))
        elif self.args:
            try:
                spaceobj = self.caller.search(self.args,candidates=search_tag(category="spaceobj"))
            except:
                return self.caller.msg("I'm sorry %s, I'm affraid I can't do that." % self.caller.key)
            if not spaceobj:
                return self.caller.msg("Unknown spaceobj")
            return self.caller.msg("%s [#%s] - %s" % (spaceobj.key, spaceobj.id, type(spaceobj)))
        else:
            return self.caller.msg("You might want to see 'help @spaceobj'")
