"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia import DefaultCharacter


class Character(DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """
    pass
    def at_object_creation(self):
        self.cmdset.add('world.space.space_cmdset.SpaceCmdSet', permanent=True)
        self.db.console = None
        self.db.doing = []
        self.db.org = None
        self.db.rank = None
        self.db.hidden = False

    def unfindable(self):
        return self.db.hidden

    def at_before_move(self, destination):
        """
        Called just before starting to move this object to
        destination.

        Args:
            destination (Object): The object we are moving to

        Returns:
            shouldmove (bool): If we should move or not.

        Notes:
            If this method returns False/None, the move is cancelled
            before it is even started.

        """
        if self.db.console:
            self.msg('You unman %s.' % self.db.console)
            self.db.console.db.operator = None
            self.db.console = None
        return True
    def announce_move_from(self, destination, msg=None, mapping=None):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location.

        Args:
            destination (Object): The place we are going to.
            msg (str, optional): a replacement message.
            mapping (dict, optional): additional mapping objects.

        You can override this method and call its parent with a
        message to simply change the default message.  In the string,
        you can use the following as mappings (between braces):
            object: the object which is moving.
            exit: the exit from which the object is moving (if found).
            origin: the location of the object before the move.
            destination: the location of the object after moving.

        """
        super(Character, self).announce_move_from(destination, msg="{object} leaves, heading through {exit}.")
    def announce_move_to(self, source_location, msg=None, mapping=None, **kwargs):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location.

        Args:
            destination (Object): The place we are going to.
            msg (str, optional): a replacement message.
            mapping (dict, optional): additional mapping objects.

        You can override this method and call its parent with a
        message to simply change the default message.  In the string,
        you can use the following as mappings (between braces):
            object: the object which is moving.
            exit: the exit from which the object is moving (if found).
            origin: the location of the object before the move.
            destination: the location of the object after moving.

        """
        super(Character, self).announce_move_to(source_location, msg="{object} arrives from {exit}.")
    def man(self, console):
        self.db.console = console
        console.db.operator = self
        self.db.doing.append('manning %s' % console)
        self.notify_location('You man %s.' %
                             console, '%s mans %s.' % (self, console))

    def unman(self):
        console = self.db.console
        self.db.doing.remove('manning %s' % console)
        del console.db.operator
        del self.db.console
        self.notify_location('You unman %s.' % console,
                             'location: %s unmans %s.' % (self, console))

    def notify_location(self, toyou, tolocation):
        self.msg(toyou)
        self.location.msg_contents(tolocation, exclude=[self])

    def notify_target(self, target, toyou, totarget, tolocation):
        self.msg(toyou)
        target.msg(totarget)
        self.location.msg_contents(tolocation, exclude=[self, target])

    def get_display_name(self, looker, **kwargs):
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            string = "{}(#{})".format(self.name, self.id)
        else:
            string = "%s" % self.name
        if not self.account:
            string += " (OOC)"
        return string
