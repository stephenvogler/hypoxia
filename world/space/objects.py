from typeclasses.objects import Object
from evennia import search_channel

class SpaceObject(Object):
    """
    Base class for all objects in the space system
    """

    def at_object_creation(self):
        super(SpaceObject, self).at_object_creation()
        search_channel('Space')[0].msg(self.name + ' added to space system.')
        self.db.contacts = {}
        self.db.consoles = []
        self.db.local = []
        self.db.xyhead = 0
        self.db.zhead = 0
        self.db.desired_xyhead = 0
        self.db.desired_zhead = 0
        self.db.speed = [0.0, 0.0]
        #self.db.course = head2course(0, 0)
        #self.db.dest = Vector3(0, 0, 0)
        #self.db.pos = Vector3(0, 0, 0)
        #sciscan will return what is seen when the object is scanned, Ie atmosphere composition, numbe of people, etc.
        self.db.sciscan = []
        #Change pads and docks to a function that checks .db.local and looks for typeclass
        self.db.pads = {}
        self.db.docks = {}
        self.db.board_room = None
        #powerpool and related power items will live on PowerGrid when created
        self.db.powerpool = 0
        self.tags.add(str(self), category="spaceobj")

    def at_object_delete(self):
        """
        Clean up.
        """
        other = SpaceObject.objects.all_family()
        for other in other:
            if self in other.db.contacts:
                for console in other.db.consoles:
                    if "helm" in console.db.current_modes:
                        console.notify("Lost contact: %s" % (self))
                other.db.contacts.remove(self)
        for console in self.db.consoles:
            console.db.spaceobj = None
        for room in self.db.local:
            room.db.spaceobj = None
        search_channel('Space')[0].msg(
            "%s removed from space system." % (self.name))
        return 1

class Ship(SpaceObject):
    def at_object_creation(self):
        super(Ship, self).at_object_creation()
        self.tags.add(str(self), category="ship")

class Station(SpaceObject):
    def at_object_creation(self):
        super(Station, self).at_object_creation()
        self.tags.add(str(self), category="station")

class Console(Object):
    """
    Default console object.
    """

    def at_object_creation(self):
        """
        Set required attributes. Need to determine eventual start .valid_modes
        """
        super(Console, self).at_object_creation()
        self.locks.add(';'.join(['get:perm(Builders)']))
        self.cmdset.add('world.space.console_cmdset.DefaultConsole', permanent=True)
        self.db.spaceobj = []
        self.db.operator = []
        self.db.valid_modes = ['helm', 'diagnostic']
        self.db.current_modes = []
    def at_drop(self, dropper):
        """
        If the console is dropped in a location on a spaceobj, initialize the console when we drop it so there's nothing to worry about setting up!
        Note - the room must be attached to a spaceobj!
        """
        try:
            self.db.spaceobj = self.location.db.spaceobj
            self.db.spaceobj.db.consoles.append(self)
            search_channel('Space')[0].msg('Console: %s has been attached to %s.' % (
                self.name, self.location.db.spaceobj))
        except:
            dropper.msg(
                "|RThis location is not part of a space object so it hasn't been initialized!")

    def at_get(self, getter):
        """
        Clean up the console and remove it from the spaceobj.
        """
        if self.db.operator:
            self.db.operator.unman()
        if self.db.spaceobj:
            try:
                self.db.spaceobj.db.consoles.remove(self)
            except:
                search_channel('Space')[0].msg('Console: There was a problem with %s, but it has been corrected.' % self.name)
            del self.db.spaceobj
            search_channel('Space')[0].msg('Console: %s removed from %s.' % (
                self.name, self.location.location.db.spaceobj))

    def at_object_delete(self):
        """
        Clean up the console and remove it from the spaceobj.
        """
        if self.db.operator:
            self.db.operator.unman()
        if self.db.spaceobj:
            try:
                self.db.spaceobj.db.consoles.remove(self)
            except:
                del self.db.spaceobj
            search_channel('Space')[0].msg('Console: %s removed from %s on %s.' % (
                self.name, self.location.location, self.location.db.spaceobj))
        return 1

    def get_display_name(self, looker, **kwargs):
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            string = "{}(#{})".format(self.name, self.id)
        else:
            string = "%s" % self.name
        if self.db.operator:
            string += " (manned by %s)" % (self.db.operator if self.db.operator != looker else "you")
        return string


    def return_appearance(self, looker):
        string = super(Console, self).return_appearance(looker)
        current_modes = '\nCurrent mode%s: %s' % ('s' if len(
            self.db.current_modes) > 1 else '', ', '.join(self.db.current_modes))
        valid_modes = '\nValid mode%s: %s' % ('s' if len(
            self.db.valid_modes) > 1 else '', ', '.join(self.db.valid_modes))
        return string + current_modes + valid_modes

    def notify(self, msg, *args):
        try:
            self.db.operator.msg('|b<|C%s|b>|w: |n%s' % (self.name, msg))
        except:
            return
        if args:
            for console in self.db.spaceobj.db.consoles:
                if args[0] in console.db.current_modes and console != self:
                    console.notify('|c<From ' + self.name + '> |n' + msg)
