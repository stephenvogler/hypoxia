from typeclasses.objects import Object
from evennia import search_channel
from evennia.utils import lazy_property
from world.space.systems import *
from world.space.templates import apply_template

class SpaceObject(Object):
    """
    Base class for all objects in the space system
    """

    def at_object_creation(self):
        super(SpaceObject, self).at_object_creation()
        search_channel('Space')[0].msg(self.name + ' added to space system.')
        self.db.spaceframe = None
        self.db.consoles = []
        self.db.local = []
        #Movement info
        self.db.heading = {'xy':0,'z':0}
        self.db.d_heading = {'xy':0,'z':0}
        self.db.speed = 0.0
        self.db.d_speed = 0.0
        self.db.course = head2course(0, 0)
        self.db.dest = Vector3(0, 0, 0)
        self.db.pos = Vector3(0, 0, 0)
        #Interaction info
        self.db.scandata = {"atmosphere":None,"lifesigns":None,"composition":None,"engineering":None}
        self.db.landing_pads = {}
        self.db.docking_ports = {}
        self.db.airlocks = {}
        self.db.docked = None
        self.tags.add(str(self), category="spaceobj")

    @lazy_property
    def systems(self):
        return SystemHandler(self)

    def reset(self):
        """Resets the object to sane defaults at 0,0,0"""
        self.location = self.home
        self.db.pos = Vector3(0, 0, 0)
        self.db.speed = 0.0
        self.db.d_speed = 0.0
        self.db.course = head2course(0, 0)
        self.db.heading = {'xy':0,'z':0}
        self.db.d_heading = {'xy':0,'z':0}

    def at_object_delete(self):
        """
        Clean up.
        """
        other = self.location.contents
        for other in other:
            if other.db.spaceframe and self in other.systems.sensors.contacts:
                for console in other.db.consoles:
                    if "helm" in console.db.current_modes:
                        console.notify("Lost contact: %s" % (self))
                del other.systems.sensors.contacts[self]
        for console in self.db.consoles:
            console.db.spaceobj = None
        for room in self.db.local:
            room.db.spaceobj = None
        search_channel('Space')[0].msg(
            "%s removed from space system." % (self.name))
        return 1
    def position(self):
        vector = Vector3.from_points([0,0,0], self.db.pos)
        x, y, z = vector
        r = sqrt(x * x + y * y + z * z)
        xyang = (round(degrees(atan2(x, y)),2)) % 360
        if xyang > 180:
            xyang -=360
        zang = (round(degrees(atan2(z, sqrt(x * x + y * y))),2)) % 360
        if zang > 180:
            zang -=360
        distance = self.dist3d([0, 0, 0])
        return [xyang, zang, round(distance, 6)]

    def set_pos(self, x, y, z):
        self.db.pos = Vector3(x, y, z)

    def heading(self):
        return [self.db.heading['xy'], self.db.heading['z']]

    def setheading(self, heading):
        self.db.d_heading['xy'] = float(heading[0])
        self.db.d_heading['z'] = float(heading[1])

        UpdateHeading(self, 1)

    def move_to_coord(self,xyhead, zhead, distance):
        self.db.pos = Vector3(head2course(xyhead, zhead)).scale(distance)

    def speed(self):
        return self.db.speed

    def maxspeed(self):
        # TODO: Need to add function to determine max speed
        return 100

    def setspeed(self, speed):
        self.db.d_speed = speed
        UpdatePosition(self)

    def powerpool(self):
        powerpool = 0
        for system in self.systems.all:
            system = self.systems[system]
            if system._data['type'] == 'producer':
                powerpool += system.current_power
        return powerpool
    # default, return status. If option is provided, change status and return
    def sensors(self, *status):
        if status:
            self.db.sensors = status
        self.db.sensors

    def sensor_range(self):
        """
        Hardcoded sensor range for now.
        """
        return self.systems.sensors.current_power * 0.00003 * self.systems.sensors.health()
    def semote(self, msg):
        """
        Broadcasts action to sensors of other spaceobjs
        """
        #will need to limit this to objects that have the target on screen or some other way of actually seeing it
        self.location.msg_contents("%s %s" % (self, msg))

    def tflag(self):
        return "|yU|n"

    def dist3d(self, contact):
        x, y, z = self.db.pos
        try:
            xx, yy, zz = contact.db.pos
        except:
            xx, yy, zz = contact
        dx = x - xx
        dy = y - yy
        dz = z - zz
        return sqrt(dx * dx + dy * dy + dz * dz)

    #returns relative bearing to spaceobj
    def bearing_to(self, contact):
        vector = Vector3.from_points(self.db.pos, contact.db.pos)
        x, y, z = vector
        r = sqrt(x * x + y * y + z * z)
        xyang = (round(degrees(atan2(x, y)),2) - self.db.heading['xy']) % 360
        if xyang > 180:
            xyang -=360
        zang = (round(degrees(atan2(z, sqrt(x * x + y * y))),2) - self.db.heading['z']) % 360
        if zang > 180:
            zang -=360
        return [xyang, zang]

class Ship(SpaceObject):
    def at_object_creation(self):
        super(Ship, self).at_object_creation()
        self.tags.add(str(self), category="ship")
        apply_template(self, 'DefaultShip')

class Station(SpaceObject):
    def at_object_creation(self):
        super(Station, self).at_object_creation()
        self.tags.add(str(self), category="station")
        apply_template(self, 'DefaultStation')

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
            self.db.operator.msg('|w<|g{}: |b{}|w>'.format(self.name.title(), msg))
        except:
            return
        if args:
            for console in self.db.spaceobj.db.consoles:
                if args[0] in console.db.current_modes and console != self:
                    console.notify('|c<From ' + self.name + '> |n' + msg)
