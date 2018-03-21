from math import *
from evennia import DefaultScript, create_script, search_channel, search_object
from evennia.utils.utils import inherits_from

def format_speed(speed):
    return "|C{:.2f}m/s|n".format(speed)
def format_heading(heading):
    return "|C{: 07.2f}{:+07.2f}|n".format(heading[0], heading[1])
def format_bearing(bearing):
    #same as format_heading, but strips the leading " " if xyang is positive.
    #use for display outputs don't require strict widths.
    return "|C{:06.2f}{:+07.2f}|n".format(bearing[0], bearing[1])
def format_position(position):
    xy, z, d = position
    return "|C{:06.2f}{:+07.2f} {:013.6f}|n".format(xy, z, d)
def min_num(x):
    if type(x) is str:
        if x == '':
            x = 0
    f = float(x)
    if f.is_integer():
        return int(f)
    else:
        return f
def format_distance(number):
    """
    lightseconds
    [kilometers]
    >Meters<
    """
    number = float(number)
    l = ""
    r = ""
    if number < 0.5:
        number *= 300
        l = "["
        r = "]"
        if number < 0.5:
            number *= 1000
            l = ">"
            r = "<"
    return l + "{}".format(min_num(round(number,2))) + r
convert_distance = format_distance
#------------------------------------------------------------
#
# SpaceHandler - Each spaceobj that NEEDS one will create it
# when needed. If the object isn't doing anything that requires
# updates, it will stop itself. The plan is for any and all
# UpdateFoo scripts to be in here and called as needed by the
# associated commands or external events.
#
#------------------------------------------------------------

class SpaceHandler(DefaultScript):
    """
    Facilitates movement and related functions of spaceobjs
    """

    def at_script_creation(self):
        self.key = "update_spaceobj"
        self.desc = "Makes space objects work!"
        self.interval = 1
        self.persistent = True
        self.db.update = []

    def _init_target(self, target):
        """
        This initializes handler back-reference on spaceobj
        """
        self.obj.ndb.space_handler = self

    def _cleanup_target(self, target):
        del self.obj.ndb.space_handler

    def at_start(self):
        self._init_target(self.db.target)

    def at_stop(self):
        self._cleanup_target(self.db.target)

    def at_repeat(self):
        for action in self.db.update:
            action(self.obj)

    def add_action(self, action):
        self.db.update.append(action)

    def del_action(self, action):
        self.db.update.remove(action)
        if len(self.db.update) < 1:
            self.stop()

#------------------------------------------------------------
#
# UpdateHeading - Update the heading and course of a spaceobj
# which is used in UpdatePosition to produce movement
#
#------------------------------------------------------------

def UpdateHeading(target, *semote):
    if not target.ndb.space_handler:
        target.ndb.space_handler = create_script("SpaceHandler", obj=target)
    if not UpdateHeading in target.ndb.space_handler.db.update:
        target.ndb.space_handler.add_action(UpdateHeading)
    rate = 10.0  # TODO: come up with turn rate code; hardcoded for now id:20
    xy = target.db.heading['xy']
    z = target.db.heading['z']
    dxy = (target.db.d_heading['xy'] - xy + 360) % 360
    dz = (target.db.d_heading['z'] - z + 360) % 360
    dxy2 = dxy * dxy
    dz2 = dz * dz
    if dxy2 < 0.25 and dz2 < 0.25:
        target.db.heading['xy'] = target.db.d_heading['xy']
        target.db.heading['z'] = target.db.d_heading['z']
        target.db.course = head2course(target.db.heading['xy'], target.db.heading['z'])
        for console in target.db.consoles:
            if "helm" in console.db.current_modes:
                console.notify("Now heading %s." %
                               format_bearing(target.heading()))
        target.semote("steadies on course.")
        target.ndb.space_handler.del_action(UpdateHeading)
        return
    dist = rate / sqrt(dxy2 + dz2)
    yawmsg = ''
    pitchmsg = ''
    if not target.db.heading['xy'] == target.db.d_heading['xy']:
        if ((target.db.heading['xy'] - target.db.d_heading['xy']) % 360) > 180:
            #Turn starboard
            yawmsg = 'turn starboard'
            target.db.heading['xy'] += round(dxy * dist + 360,2) % 360
        else:
            #Turn port
            yawmsg = 'turn port'
            target.db.heading['xy'] -= round(dxy * dist + 360,2) % 360
    if not target.db.heading['z'] == target.db.d_heading['z']:
        if ((target.db.heading['z'] - target.db.d_heading['z']) % 360) > 180:
            #Pitch up
            pitchmsg = 'pitch up'
            target.db.heading['z'] += round(dz * dist + 360,2) % 360
        else:
            #Pitch down
            pitchmsg = 'pitch down'
            target.db.heading['z'] -= round(dz * dist + 360,2) % 360
    if (yawmsg or pitchmsg) and semote:
        target.semote("begins to %s%s%s." % (yawmsg, " and " if yawmsg and pitchmsg else "", pitchmsg))
    if dist >= 1.0:
        target.db.heading['xy'] = target.db.d_heading['xy']
        target.db.heading['z'] = target.db.d_heading['z']
    target.db.course = head2course(target.db.heading['xy'], target.db.heading['z'])

#------------------------------------------------------------
#
# UpdatePosition - Update the db.pos attribute on a spaceobj
# according to vector of db.course * (db.speed[0] / 1000.0)
#
# target.db.speed has the following values: [<current speed>, <desired speed>, <max speed>]
#
#------------------------------------------------------------


def UpdatePosition(target):
    if not target.ndb.space_handler:
        target.ndb.space_handler = create_script("SpaceHandler", obj=target)
    if not UpdatePosition in target.ndb.space_handler.db.update:
        target.ndb.space_handler.add_action(UpdatePosition)
    # clunky speed handling code here
    speed = target.db.speed
    #CHANGE THIS to get from engines
    dspeed = target.db.d_speed
    maxspeed = target.maxspeed()
    # TODO: semote speed change to ship rooms, at least for 'major' speed changes; ie 'the ship shakes as it accelerates' id:22
    # need to add!
    if not speed == dspeed:
        rate = 100  # CHANGEME hardcoded accelleration rate for now -- speed currently in meters per second
        if dspeed > speed:
            speed += rate
            if speed > dspeed:
                speed = dspeed
            if speed > maxspeed:
                speed = maxspeed
        else:
            speed -= rate
            if speed < dspeed:
                speed = dspeed
        target.db.speed = speed
        if speed == dspeed:
            for console in target.db.consoles:
                if "helm" in console.db.current_modes:
                    console.notify("Speed is now %s." % (format_speed(speed)))
    if speed == 0.0 and dspeed == 0.0:
        target.ndb.space_handler.del_action(UpdatePosition)
    target.db.pos += Vector3(target.db.course).scale(
        target.db.speed / 300000)
    return

#------------------------------------------------------------
#
# UpdateSensors - Handle updating sensor contacts and range/bearing
# dist3d can be moved to the spaceobj
#
#------------------------------------------------------------


def UpdateSensors(target):
    # Check if there's a handler, make one if needed
    if not target.ndb.space_handler:
        target.ndb.space_handler = create_script("world.space.system.SpaceHandler", obj=target)
    if not UpdateSensors in target.ndb.space_handler.db.update:
        target.ndb.space_handler.add_action(UpdateSensors)
    # grab ALL space objects... Whew!
    #contacts = SpaceObject.objects.all_family()
    contacts = []
    if target.db.sensors:
        for contact in target.location.contents:
            if inherits_from(contact, "world.space.objects.SpaceObject"):
                    contacts.append(contact)
    for contact in contacts:
        # identify new contacts we can see based on sensor range
        # put them in our contact list and notify consoles
        if target.dist3d(contact) <= target.sensor_range():
            if not contact in target.db.contacts and contact != target:
                # TODO: Figure out flags that we want to use in dict
                target.db.contacts[contact]=["Initial","Resolution"]
                for console in target.db.consoles:
                    """
                    if "helm" in console.db.current_modes:
                    """
                    console.notify("New contact: %s. Bearing: %s Range: %s" % (contact, format_bearing(target.bearing_to(contact)), convert_distance(target.dist3d(contact))))
        # drop contacts we can't see any more from our contact list and
        # notify consoles
        if target.dist3d(contact) > target.sensor_range():
            if contact in target.db.contacts and contact != target:
                for console in target.db.consoles:
                    if "helm" in console.db.current_modes:
                        console.notify("Lost contact: %s" % (contact))
                del target.db.contacts[contact]
    # Clean things up when the sensors go offlione
    # TODO: Plan out sane sensor handling for offline situations id:12
    for contact in target.db.contacts.keys():
        if not contact in contacts:
            for console in target.db.consoles:
                if "helm" in console.db.current_modes:
                    console.notify("Lost contact: %s. Last seen bearing: %s Range: %s " % (contact, format_bearing(target.bearing_to(contact)), convert_distance(target.dist3d(contact))))
            del target.db.contacts[contact]
    if not target.db.sensors:
        target.ndb.space_handler.del_action(UpdateSensors)
#------------------------------------------------------------
#
# UpdatePower - Engineering code to handle power allocation and subsystem performance
#
#------------------------------------------------------------
# TODO: We're going to need some power soon! id:6
def UpdatePower(target):
    # Check if there's a handler, make one if needed
    if not target.ndb.space_handler:
        target.ndb.space_handler = create_script("SpaceHandler", obj=target)
    if not UpdatePower in target.ndb.space_handler.db.update:
        target.ndb.space_handler.add_action(UpdatePower)

#------------------------------------------------------------
#
# get_xyang - Gets the XY angle between two points.
#
#------------------------------------------------------------
def get_xyang(p1, p2):

    x0 = p1[0]
    x1 = p2[0]
    y0 = p1[1]
    y1 = p2[1]
    return atan2(y1 - y0, x1 - x0)
#------------------------------------------------------------
#
# get_zang - Gets the Z angle between two points.
#
#------------------------------------------------------------

def get_zang(p1, p2):

    r0 = sqrt(p1[0] * p1[0] + p1[1] * p1[1])
    r1 = sqrt(p2[0] * p2[0] + p2[1] * p2[1])
    z0 = p1[2]
    z1 = p2[2]
    return atan2(r1 - r0, z1 - z0)

#------------------------------------------------------------
#
# head2course - Converts <xyhead> and <zhead> degrees into
# radians, then [x,y,z] course adjustments.
#
#------------------------------------------------------------

def head2course(xyhead, zhead):
    zfac = cos(radians(zhead))
    if xyhead == 0 or xyhead == 180:
        vx = 0.0
    else:
        vx = round(zfac * cos(radians(450 - xyhead)),4)
    if xyhead == 90 or xyhead == 270:
        vy = 0.0
    else:
        vy = round(zfac * sin(radians(450 - xyhead)),4)
    if zhead == 0 or zhead == 90:
        vz = 0.0
    else:
        vz = round(sin(radians(zhead)),4)
    return Vector3(vx, vy, vz)

#------------------------------------------------------------
#
# Vector3 - Creates a 3D vector for space objects.
#
#------------------------------------------------------------

class Vector3(object):

    __slots__ = ('_v',)

    _gameobjects_vector = 3

    def __init__(self, *args):
        """Creates a Vector3 from 3 numeric values or a list-like object
        containing at least 3 values. No arguments result in a null vector.
        """
        if len(args) == 3:
            self._v = list(map(float, args[:3]))
            return

        if not args:
            self._v = [0., 0., 0.]
        elif len(args) == 1:
            self._v = list(map(float, args[0][:3]))
        else:
            raise ValueError("Vector3.__init__ takes 0, 1 or 3 parameters")

    @classmethod
    def from_points(cls, p1, p2):

        v = cls.__new__(cls, object)
        ax, ay, az = p1
        bx, by, bz = p2
        v._v = [round(bx - ax,4), round(by - ay,4), round(bz - az,4)]

        return v

    @classmethod
    def from_floats(cls, x, y, z):
        """Creates a Vector3 from individual float values.
        Warning: There is no checking (for efficiency) here: x, y, z _must_ be
        floats.
        """
        v = cls.__new__(cls, object)
        v._v = [round(x,6), round(y,6), round(z,6)]
        return v

    @classmethod
    def from_iter(cls, iterable):
        """Creates a Vector3 from an iterable containing at least 3 values."""
        next = iter(iterable).__next__
        v = cls.__new__(cls, object)
        v._v = [float(next()), float(next()), float(next())]
        return v

    @classmethod
    def _from_float_sequence(cls, sequence):
        v = cls.__new__(cls, object)
        v._v = list(sequence[:3])
        return v

    def copy(self):
        """Returns a copy of this vector."""

        v = self.__new__(self.__class__, object)
        v._v = self._v[:]
        return v
        # return self.from_floats(self._v[0], self._v[1], self._v[2])

    __copy__ = copy

    def _get_x(self):
        return self._v[0]

    def _set_x(self, x):
        try:
            self._v[0] = 1.0 * x
        except:
            raise TypeError("Must be a number")
    x = property(_get_x, _set_x, None, "x component.")

    def _get_y(self):
        return self._v[1]

    def _set_y(self, y):
        try:
            self._v[1] = 1.0 * y
        except:
            raise TypeError("Must be a number")
    y = property(_get_y, _set_y, None, "y component.")

    def _get_z(self):
        return self._v[2]

    def _set_z(self, z):
        try:
            self._v[2] = 1.0 * z
        except:
            raise TypeError("Must be a number")
    z = property(_get_z, _set_z, None, "z component.")

    def _get_length(self):
        x, y, z = self._v
        return sqrt(x * x + y * y + z * z)

    def _set_length(self, length):
        v = self._v
        try:
            x, y, z = v
            l = length / sqrt(x * x + y * y + z * z)
        except ZeroDivisionError:
            v[0] = 0.
            v[1] = 0.
            v[2] = 0.
            return self

        v[0] = x * l
        v[1] = y * l
        v[2] = z * l

    length = property(_get_length, _set_length, None, "Length of the vector")

    def unit(self):
        """Returns a unit vector."""
        x, y, z = self._v
        l = sqrt(x * x + y * y + z * z)
        return self.from_floats(x / l, y / l, z / l)

    def set(self, x, y, z):
        """Sets the components of this vector.
        x -- x component
        y -- y component
        z -- z component
        """

        v = self._v
        try:
            v[0] = x * 1.0
            v[1] = y * 1.0
            v[2] = z * 1.0
        except TypeError:
            raise TypeError("Must be a number")
        return self

    def __str__(self):

        x, y, z = self._v
        return "(%s, %s, %s)" % (x,
                                 y,
                                 z)

    def __repr__(self):

        x, y, z = self._v
        return "Vector3(%s, %s, %s)" % (x, y, z)

    def __len__(self):

        return 3

    def __iter__(self):
        """Iterates the components in x, y, z order."""
        return iter(self._v[:])

    def __getitem__(self, index):
        """Retrieves a component, given its index.
        index -- 0, 1 or 2 for x, y or z
        """
        try:
            return self._v[index]
        except IndexError:
            raise IndexError(
                "There are 3 values in this object, index should be 0, 1 or 2!")

    def __setitem__(self, index, value):
        """Sets a component, given its index.
        index -- 0, 1 or 2 for x, y or z
        value -- New (float) value of component
        """

        try:
            self._v[index] = 1.0 * value
        except IndexError:
            raise IndexError(
                "There are 3 values in this object, index should be 0, 1 or 2!")
        except TypeError:
            raise TypeError("Must be a number")

    def __eq__(self, rhs):
        """Test for equality
        rhs -- Vector or sequence of 3 values
        """

        x, y, z = self._v
        xx, yy, zz = rhs
        return x == xx and y == yy and z == zz

    def __ne__(self, rhs):
        """Test of inequality
        rhs -- Vector or sequenece of 3 values
        """

        x, y, z = self._v
        xx, yy, zz = rhs
        return x != xx or y != yy or z != zz

    def __hash__(self):

        return hash(self._v)

    def __add__(self, rhs):
        """Returns the result of adding a vector (or collection of 3 numbers)
        from this vector.
        rhs -- Vector or sequence of 2 values
        """

        x, y, z = self._v
        ox, oy, oz = rhs
        return self.from_floats(x + ox, y + oy, z + oz)

    def __iadd__(self, rhs):
        """Adds another vector (or a collection of 3 numbers) to this vector.
        rhs -- Vector or sequence of 2 values
        """
        ox, oy, oz = rhs
        v = self._v
        v[0] += ox
        v[1] += oy
        v[2] += oz
        return self

    def __radd__(self, lhs):
        """Adds vector to this vector (right version)
        lhs -- Left hand side vector or sequence
        """

        x, y, z = self._v
        ox, oy, oz = lhs
        return self.from_floats(x + ox, y + oy, z + oz)

    def __sub__(self, rhs):
        """Returns the result of subtracting a vector (or collection of
        3 numbers) from this vector.
        rhs -- 3 values
        """

        x, y, z = self._v
        ox, oy, oz = rhs
        return self.from_floats(x - ox, y - oy, z - oz)

    def _isub__(self, rhs):
        """Subtracts another vector (or a collection of 3 numbers) from this
        vector.
        rhs -- Vector or sequence of 3 values
        """

        ox, oy, oz = rhs
        v = self._v
        v[0] -= ox
        v[1] -= oy
        v[2] -= oz
        return self

    def __rsub__(self, lhs):
        """Subtracts a vector (right version)
        lhs -- Left hand side vector or sequence
        """

        x, y, z = self._v
        ox, oy, oz = lhs
        return self.from_floats(ox - x, oy - y, oz - z)

    def scalar_mul(self, scalar):

        v = self._v
        v[0] *= scalar
        v[1] *= scalar
        v[2] *= scalar

    def vector_mul(self, vector):

        x, y, z = vector
        v = self._v
        v[0] *= x
        v[1] *= y
        v[2] *= z

    def get_scalar_mul(self, scalar):

        x, y, z = self._v
        return self.from_floats(x * scalar, y * scalar, z * scalar)

    def get_vector_mul(self, vector):

        x, y, z = self._v
        xx, yy, zz = vector
        return self.from_floats(x * xx, y * yy, z * zz)

    def __mul__(self, rhs):
        """Return the result of multiplying this vector by another vector, or
        a scalar (single number).
        rhs -- Vector, sequence or single value.
        """

        x, y, z = self._v
        if hasattr(rhs, "__getitem__"):
            ox, oy, oz = rhs
            return self.from_floats(x * ox, y * oy, z * oz)
        else:
            return self.from_floats(x * rhs, y * rhs, z * rhs)

    def __imul__(self, rhs):
        """Multiply this vector by another vector, or a scalar
        (single number).
        rhs -- Vector, sequence or single value.
        """

        v = self._v
        if hasattr(rhs, "__getitem__"):
            ox, oy, oz = rhs
            v[0] *= ox
            v[1] *= oy
            v[2] *= oz
        else:
            v[0] *= rhs
            v[1] *= rhs
            v[2] *= rhs

        return self

    def __rmul__(self, lhs):

        x, y, z = self._v
        if hasattr(lhs, "__getitem__"):
            ox, oy, oz = lhs
            return self.from_floats(x * ox, y * oy, z * oz)
        else:
            return self.from_floats(x * lhs, y * lhs, z * lhs)

    def __div__(self, rhs):
        """Return the result of dividing this vector by another vector, or a scalar (single number)."""

        x, y, z = self._v
        if hasattr(rhs, "__getitem__"):
            ox, oy, oz = rhs
            return self.from_floats(x / ox, y / oy, z / oz)
        else:
            return self.from_floats(x / rhs, y / rhs, z / rhs)

    def __idiv__(self, rhs):
        """Divide this vector by another vector, or a scalar (single number)."""

        v = self._v
        if hasattr(rhs, "__getitem__"):
            v[0] /= ox
            v[1] /= oy
            v[2] /= oz
        else:
            v[0] /= rhs
            v[1] /= rhs
            v[2] /= rhs

        return self

    def __rdiv__(self, lhs):

        x, y, z = self._v
        if hasattr(lhs, "__getitem__"):
            ox, oy, oz = lhs
            return self.from_floats(ox / x, oy / y, oz / z)
        else:
            return self.from_floats(lhs / x, lhs / y, lhs / z)

    def scalar_div(self, scalar):

        v = self._v
        v[0] /= scalar
        v[1] /= scalar
        v[2] /= scalar

    def vector_div(self, vector):

        x, y, z = vector
        v = self._v
        v[0] /= x
        v[1] /= y
        v[2] /= z

    def get_scalar_div(self, scalar):

        x, y, z = self.scalar
        return self.from_floats(x / scalar, y / scalar, z / scalar)

    def get_vector_div(self, vector):

        x, y, z = self._v
        xx, yy, zz = vector
        return self.from_floats(x / xx, y / yy, z / zz)

    def __neg__(self):
        """Returns the negation of this vector (a vector pointing in the opposite direction.
        eg v1 = Vector(1,2,3)
        print -v1
        >>> (-1,-2,-3)
        """
        x, y, z = self._v
        return self.from_floats(-x, -y, -z)

    def __pos__(self):

        return self.copy()

    def __bool__(self):

        x, y, z = self._v
        return bool(x or y or z)

    def __call__(self, keys):
        """Returns a tuple of the values in a vector
        keys -- An iterable containing the keys (x, y or z)
        eg v = Vector3(1.0, 2.0, 3.0)
        v('zyx') -> (3.0, 2.0, 1.0)
        """
        ord_x = ord('x')
        v = self._v
        return tuple(v[ord(c) - ord_x] for c in keys)

    def as_tuple(self):
        """Returns a tuple of the x, y, z components. A little quicker than
        tuple(vector)."""

        return tuple(self._v)

    def scale(self, scale):
        """Scales the vector by onther vector or a scalar. Same as the
        *= operator.
        scale -- Value to scale the vector by
        """
        v = self._v
        if hasattr(scale, "__getitem__"):
            ox, oy, oz = scale
            v[0] *= ox
            v[1] *= oy
            v[2] *= oz
        else:
            v[0] *= scale
            v[1] *= scale
            v[2] *= scale

        return self

    def get_length(self):
        """Calculates the length of the vector."""

        x, y, z = self._v
        return sqrt(x * x + y * y + z * z)
    get_magnitude = get_length

    def set_length(self, new_length):
        """Sets the length of the vector. (Normalizes it then scales it)
        new_length -- The new length of the vector.
        """
        v = self._v
        try:
            x, y, z = v
            l = new_length / sqrt(x * x + y * y + z * z)
        except ZeroDivisionError:
            v[0] = 0.0
            v[1] = 0.0
            v[2] = 0.0
            return self

        v[0] = x * l
        v[1] = y * l
        v[2] = z * l

        return self

    def get_distance_to(self, p):
        """Returns the distance of this vector to a point.
        p -- A position as a vector, or collection of 3 values.
        """
        ax, ay, az = self._v
        bx, by, bz = p
        dx = ax - bx
        dy = ay - by
        dz = az - bz
        return sqrt(dx * dx + dy * dy + dz * dz)

    def get_distance_to_squared(self, p):
        """Returns the squared distance of this vector to a point.
        p -- A position as a vector, or collection of 3 values.
        """
        ax, ay, az = self._v
        bx, by, bz = p
        dx = ax - bx
        dy = ay - by
        dz = az - bz
        return dx * dx + dy * dy + dz * dz

    def normalize(self):
        """Scales the vector to be length 1."""
        v = self._v
        x, y, z = v
        l = sqrt(x * x + y * y + z * z)
        try:
            v[0] /= l
            v[1] /= l
            v[2] /= l
        except ZeroDivisionError:
            v[0] = 0.0
            v[1] = 0.0
            v[2] = 0.0
        return self

    def get_normalized(self):

        x, y, z = self._v
        l = sqrt(x * x + y * y + z * z)
        try:
            return self.from_floats(x / l, y / l, z / l)
        except ZeroDivisionError:
            return self.from_floats(0, 0, 0)

    def in_sphere(self, sphere):
        """Returns true if this vector (treated as a position) is contained in
        the given sphere.
        """

        return distance3d(sphere.position, self) <= sphere.radius

    def dot(self, other):
        """Returns the dot product of this vector with another.
        other -- A vector or tuple
        """
        x, y, z = self._v
        ox, oy, oz = other
        return x * ox + y * oy + z * oz

    def cross(self, other):
        """Returns the cross product of this vector with another.
        other -- A vector or tuple
        """

        x, y, z = self._v
        bx, by, bz = other
        return self.from_floats(y * bz - by * z,
                                z * bx - bz * x,
                                x * by - bx * y)

    def cross_tuple(self, other):
        """Returns the cross product of this vector with another, as a tuple.
        This avoids the Vector3 construction if you don't need it.
        other -- A vector or tuple
        """

        x, y, z = self._v
        bx, by, bz = other
        return (y * bz - by * z,
                z * bx - bz * x,
                x * by - bx * y)


def center3d(points):

    return sum(Vector3(p) for p in points) / len(points)
