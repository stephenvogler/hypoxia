from evennia.utils.dbserialize import _SaverDict
from evennia.utils.utils import inherits_from
from evennia.utils import logger, lazy_property, delay
from world.space.utils import *
from functools import total_ordering
from math import *
from evennia import DefaultScript, create_script, search_channel, search_object

SYSTEM_TYPES = ('producer', 'consumer', 'router', 'aux')

class SystemException(Exception):
    """Base exception class raised by `System` objects.
    Args:
        msg (str): informative error message
    """
    def __init__(self, msg):
        self.msg = msg

class SystemHandler(object):
    """Factory class that instantiates System objects.
    Args:
        obj (Object): parent Object typeclass for this SystemHandler
        db_attribute (str): name of the DB attribute for system data storage
    """
    def __init__(self, obj, db_attribute='systems'):
        if not obj.attributes.has(db_attribute):
            obj.attributes.add(db_attribute, {})

        self.attr_dict = obj.attributes.get(db_attribute)
        self.cache = {}

    def __len__(self):
        """Return number of Systems in 'attr_dict'."""
        return len(self.attr_dict)

    def __setattr__(self, key, value):
        """Returns error message if system objects are assigned directly."""
        if key in ('attr_dict', 'cache'):
            super(SystemHandler, self).__setattr__(key, value)
        else:
            raise SystemException(
                "System object not settable. Assign one of "
                "`{0}.base`, `{0}.mod`, or `{0}.current` ".format(key) +
                "properties instead."
            )

    def __setitem__(self, key, value):
        """Returns error message if system objects are assigned directly."""
        return self.__setattr__(key, value)

    def __getattr__(self, system):
        """Returns System instances accessed as attributes."""
        return self.get(system)

    def __getitem__(self, system):
        """Returns `System` instances accessed as dict keys."""
        return self.get(system)

    def get(self, system):
        """
        Args:
            system (str): key from the systems dict containing config data
                for the system. "all" returns a list of all system keys.
        Returns:
            (`System` or `None`): named System class or None if system key
            is not found in systems collection.
        """
        if system not in self.cache:
            if system not in self.attr_dict:
                return None
            data = self.attr_dict[system]
            self.cache[system] = System(data)
        return self.cache[system]

    def add(self, key, name, type='consumer',
            min_power=0, max_power=0, set_power=0, current_power=0, max_hp=0, dmg=0, spaceobj=None, script=None, extra={}):
        """Create a new System and add it to the handler."""
        if key in self.attr_dict:
            raise SystemException("System '{}' already exists.".format(key))

        if type in SYSTEM_TYPES:
            system = dict(name=name,
                         type=type,
                         min_power=min_power,
                         max_power=max_power,
                         set_power=set_power,
                         current_power=current_power,
                         max_hp=max_hp,
                         dmg=dmg,
                         spaceobj=spaceobj,
                         script=script,
                         extra=extra)

            self.attr_dict[key] = system
        else:
            raise SystemException("Invalid system type specified.")

    def remove(self, system):
        """Remove a System from the handler's parent object."""
        if system not in self.attr_dict:
            raise SystemException("System not found: {}".format(system))

        if system in self.cache:
            del self.cache[system]
        del self.attr_dict[system]

    def clear(self):
        """Remove all Systems from the handler's parent object."""
        for system in self.all:
            self.remove(system)

    @property
    def all(self):
        """Return a list of all system keys in this SystemHandler."""
        return self.attr_dict.keys()

@total_ordering
class System(object):
    """Represents a system on a spaceobj.
    Note:
        See module docstring for configuration details.
    """
    def __init__(self, data):
        if not 'name' in data:
            raise SystemException(
                "Required key not found in system data: 'name'")
        if not 'type' in data:
            raise SystemException(
                "Required key not found in system data: 'type'")
        self._type = data['type']
        if not 'min_power' in data:
            data['min_power'] = 0
        if not 'max_power' in data:
            data['max_power'] = 0
        if not 'set_power' in data:
            data['set_power'] = 0
        if not 'current_power' in data:
            data['current_power'] = 0
        if not 'max_hp' in data:
            data['max_hp'] = 0
        if not 'dmg' in data:
            data['dmg'] = 0
        if not 'spaceobj' in data:
            data['spaceobj'] = None
        if not 'script' in data:
            data['script'] = None
        if not 'extra' in data:
            data['extra'] = {}

        self._data = data
        self._keys = ('name', 'type', 'min_power', 'max_power',
                      'set_power', 'current_power', 'max_hp', 'dmg', 'spaceobj', 'script', 'extra')
        self._locked = True

        if not isinstance(data, _SaverDict):
            logger.log_warn(
                'Non-persistent {} class loaded.'.format(
                    type(self).__name__
                ))

    def __repr__(self):
        """Debug-friendly representation of this System."""
        return "{}({{{}}})".format(
            type(self).__name__,
            ', '.join(["'{}': {!r}".format(k, self._data[k])
                for k in self._keys if k in self._data]))

    def __str__(self):
        """User-friendly string representation of this `System`"""
        status = "{current_power:4} / {max_power:4}".format(
                current_power=self.current_power,
                max_power=self.max_power)
        health = "{hp:4} / {max_hp:4}".format(
                hp=(self.max_hp - self.dmg),
                max_hp=self.max_hp
        )
        return "{name:12} {status} ({health})".format(
            name=self.name,
            status=status,
            health=health)

    def __unicode__(self):
        """User-friendly unicode representation of this `System`"""
        return unicode(str(self))

    # Extra Properties magic

    def __getitem__(self, key):
        """Access extra parameters as dict keys."""
        try:
            return self.__getattr__(key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        """Set extra parameters as dict keys."""
        self.__setattr__(key, value)

    def __delitem__(self, key):
        """Delete extra prameters as dict keys."""
        self.__delattr__(key)

    def __getattr__(self, key):
        """Access extra parameters as attributes."""
        if key in self._data['extra']:
            return self._data['extra'][key]
        else:
            raise AttributeError(
                "{} '{}' has no attribute {!r}".format(
                    type(self).__name__, self.name, key
                ))

    def __setattr__(self, key, value):
        """Set extra parameters as attributes.
        Arbitrary attributes set on a System object will be
        stored in the 'extra' key of the `_data` attribute.
        This behavior is enabled by setting the instance
        variable `_locked` to True.
        """
        propobj = getattr(self.__class__, key, None)
        if isinstance(propobj, property):
            if propobj.fset is None:
                raise AttributeError("can't set attribute")
            propobj.fset(self, value)
        else:
            if (self.__dict__.get('_locked', False) and
                    key not in ('_keys',)):
                self._data['extra'][key] = value
            else:
                super(System, self).__setattr__(key, value)

    def __delattr__(self, key):
        """Delete extra parameters as attributes."""
        if key in self._data['extra']:
            del self._data['extra'][key]

    # Numeric operations magic

    def __eq__(self, other):
        """Support equality comparison between Systems or System and numeric.
        Note:
            This class uses the @functools.total_ordering() decorator to
            complete the rich comparison implementation, therefore only
            `__eq__` and `__lt__` are implemented.
        """
        if type(other) == System:
            return self.actual == other.actual
        elif type(other) in (float, int):
            return self.actual == other
        else:
            return NotImplemented

    def __lt__(self, other):
        """Support less than comparison between `System`s or `System` and numeric."""
        if isinstance(other, System):
            return self.actual < other.actual
        elif type(other) in (float, int):
            return self.actual < other
        else:
            return NotImplemented

    def __pos__(self):
        """Access `actual` property through unary `+` operator."""
        return self.actual

    def __add__(self, other):
        """Support addition between `System`s or `System` and numeric"""
        if isinstance(other, System):
            return self.actual + other.actual
        elif type(other) in (float, int):
            return self.actual + other
        else:
            return NotImplemented

    def __sub__(self, other):
        """Support subtraction between `System`s or `System` and numeric"""
        if isinstance(other, System):
            return self.actual - other.actual
        elif type(other) in (float, int):
            return self.actual - other
        else:
            return NotImplemented

    def __mul__(self, other):
        """Support multiplication between `System`s or `System` and numeric"""
        if isinstance(other, System):
            return self.actual * other.actual
        elif type(other) in (float, int):
            return self.actual * other
        else:
            return NotImplemented

    def __floordiv__(self, other):
        """Support floor division between `System`s or `System` and numeric"""
        if isinstance(other, System):
            return self.actual // other.actual
        elif type(other) in (float, int):
            return self.actual // other
        else:
            return NotImplemented

    # yay, commutative property!
    __radd__ = __add__
    __rmul__ = __mul__

    def __rsub__(self, other):
        """Support subtraction between `System`s or `System` and numeric"""
        if isinstance(other, System):
            return other.actual - self.actual
        elif type(other) in (float, int):
            return other - self.actual
        else:
            return NotImplemented

    def __rfloordiv__(self, other):
        """Support floor division between `System`s or `System` and numeric"""
        if isinstance(other, System):
            return other.actual // self.actual
        elif type(other) in (float, int):
            return other // self.actual
        else:
            return NotImplemented

    # Public members

    @property
    def name(self):
        """Display name for the system."""
        return self._data['name']

    @property
    def actual(self):
        """The "actual" power level of the system."""
        return self.current_power

    @property
    def min_power(self):
        """The system's minimum power level to be functional.
        """
        return self._data['min_power']

    @min_power.setter
    def min_power(self, amount):
        self._data['min_power'] = amount

    @property
    def max_power(self):
        """The system's maximum power level."""
        return self._data['max_power']

    @max_power.setter
    def max_power(self, amount):
        self._data['max_power'] = amount

    @property
    def set_power(self):
        """The systems desired power level."""
        return self._data['set_power']

    @set_power.setter
    def set_power(self, amount):
        self._data['set_power'] = self._enforce_bounds(amount)

    @property
    def current_power(self):
        """The `current` power level of the `System`."""
        return self._data['current_power']

    @current_power.setter
    def current_power(self, amount):
        self._data['current_power'] = self._enforce_bounds(amount)

    @property
    def max_hp(self):
        """The systems maximum hit points."""
        return self._data['max_hp']

    @max_hp.setter
    def max_hp(self, amount):
        self._data['max_hp'] = amount

    @property
    def dmg(self):
        """The systems current damage."""
        return self._data['dmg']

    @dmg.setter
    def dmg(self, amount):
        self._data['dmg'] = amount
        if self._data['dmg'] >= self._data['max_hp']:
            self._data['set_power'] = 0
            self._data['current_power'] = 0

    @property
    def extra(self):
        """Returns a list containing available extra data keys."""
        return self._data['extra'].keys()

    # Private members

    def _enforce_bounds(self, value):
        """Ensures that incoming value falls within system's range."""
        if self.set_power is not None and value >= self.max_power:
            return self.max_power
        if self.current_power is not None and value >= self.max_power:
            return self.max_power
        return value

    def percent(self):
        return "{:.0%}".format(float(self.current_power) / float(self.max_power))

    def health(self):
        return (float(self.max_hp) - float(self.dmg)) / float(self.max_hp)

    def destroyed(self):
        if self.health() <= 0:
            return True
        else:
            return False
    def online(self):
        if self.current_power >= self.min_power and not self.destroyed():
            return True
        else:
            return False
"""
Maximum sublight speed is 74,770kps (~1/4 speed of light)
Sublight engines have a setting to determine their maximum
speed as a percentage of this maximum. For example:
    <sublight_engine>.efficiency = 1 (can go 74,770kps)
    <sublight_engine>.efficiency = .7 (can go 52,339kps)
"""

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
        target.ndb.space_handler = create_script("world.space.system.SpaceHandler", obj=target)
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
        target.ndb.space_handler = create_script(SpaceHandler, obj=target)
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
        rate = 10  # CHANGEME hardcoded accelleration rate for now
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
        #Speed is in kps
    target.db.pos += Vector3(target.db.course).scale(
        target.speed() / 299792)
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
        target.ndb.space_handler = create_script(SpaceHandler, obj=target)
    if not UpdateSensors in target.ndb.space_handler.db.update:
        target.ndb.space_handler.add_action(UpdateSensors)
    contacts = []
    for contact in target.location.contents:
        if inherits_from(contact, "world.space.objects.SpaceObject"):
                contacts.append(contact)
    for contact in contacts:
        # identify new contacts we can see based on sensor range
        # put them in our contact list and notify consoles
        if target.dist3d(contact) <= target.sensor_range():
            if not contact in target.systems.sensors.contacts and contact != target:
                # TODO: Figure out flags that we want to use
                target.systems.sensors.contacts[contact]=["Initial",100]
                for console in target.db.consoles:
                    if "helm" in console.db.current_modes:
                        console.notify("New contact %s bearing %s %s" % (contact, format_bearing(target.bearing_to(contact)), target.dist3d(contact)))
        # drop contacts we can't see any more from our contact list and
        # notify consoles
        if target.dist3d(contact) > target.sensor_range():
            if contact in target.systems.sensors.contacts and contact != target:
                for console in target.db.consoles:
                    if "helm" in console.db.current_modes:
                        console.notify("Lost contact %s last seen bearing %s %s" % (contact, format_bearing(target.bearing_to(contact)), target.dist3d(contact)))
                del target.systems.sensors.contacts[contact]
    # Clean things up when the sensors go offline
    for contact in target.systems.sensors.contacts.keys():
        if not contact in contacts:
            for console in target.db.consoles:
                if "helm" in console.db.current_modes:
                    console.notify("Lost contact %s last seen bearing %s %s" % (contact, format_bearing(target.bearing_to(contact)), target.dist3d(contact)))
            del target.systems.sensors.contacts[contact]
    if not target.systems.sensors.online():
        for contact in target.systems.sensors.contacts:
            for console in target.db.consoles:
                if "helm" in console.db.current_modes:
                    console.notify("Lost contact %s last seen bearing %s %s" % (contact, format_bearing(target.bearing_to(contact)), target.dist3d(contact)))
                    del target.systems.sensors.contacts[contact]
        target.ndb.space_handler.del_action(UpdateSensors)

#------------------------------------------------------------
#
# UpdatePower - Engineering code to handle power allocation and subsystem performance
#
#------------------------------------------------------------
def UpdatePower(target):
    # Check if there's a handler, make one if needed
    if not target.ndb.space_handler:
        target.ndb.space_handler = create_script(SpaceHandler, obj=target)
    if not UpdatePower in target.ndb.space_handler.db.update:
        target.ndb.space_handler.add_action(UpdatePower)
    producing = []
    consuming = []
    grid = target.systems.power_grid
    for system in target.systems.all:
        system = target.systems[system]
        if system._data['type'] == 'producer':
            if system.set_power != system.current_power:
                producing.append(system)
        if system._data['type'] == 'consumer':
            if system.set_power != system.current_power:
                consuming.append(system)
    if not producing and not consuming:
        return target.ndb.space_handler.del_action(UpdatePower)
    if producing:
        rate = grid.rate / len(producing)
    for system in producing:
        if system.set_power > system.current_power:
            if system.current_power + rate > system.set_power:
                rate = system.set_power - system.current_power
            if not system.online() and system.current_power + rate >= system.min_power:
                system.current_power += rate
                for console in target.db.consoles:
                    console.notify("{} online.".format(system.name))
            else:
                system.current_power += rate
            if system.current_power > system.max_power:
                system.current_power = system.max_power
            if system.set_power == system.current_power:
                producing.remove(system)
                for console in target.db.consoles:
                    console.notify("{} output now at {}".format(system.name, system.percent()))
        if system.set_power < system.current_power:
            if system.current_power - rate < system.set_power:
                rate = system.current_power - system.set_power
            if system.online() and system.current_power - rate < system.min_power:
                for console in target.db.consoles:
                    console.notify("{} offline.".format(system.name))
            system.current_power -= rate
            if system.current_power < 0:
                system.set_power = 0
                system.current_power = 0
            if system.set_power == system.current_power:
                producing.remove(system)
                for console in target.db.consoles:
                    console.notify("{} output now at {}".format(system.name, system.percent()))
    #Rate adjusted to account for the number of systems currently routing power
    if consuming:
        rate = grid.rate / len(consuming)
    for system in consuming:
        if system.set_power > system.current_power:
            if system.current_power + rate > system.set_power:
                rate = system.set_power - system.current_power
            if not system.online() and system.current_power + rate >= system.min_power:
                system.current_power += rate
                for console in target.db.consoles:
                    console.notify("{} online.".format(system.name))
                if system == target.systems.sensors:
                    UpdateSensors(target)
            else:
                system.current_power += rate
            if system.current_power > system.max_power:
                system.current_power = system.max_power
            if system.set_power == system.current_power:
                consuming.remove(system)
                for console in target.db.consoles:
                    console.notify("{} now at {}".format(system.name, system.percent()))
        if system.set_power < system.current_power:
            if system.current_power - rate < system.set_power:
                rate = system.current_power - system.set_power
            if system.online() and system.current_power - rate < system.min_power:
                for console in target.db.consoles:
                    console.notify("{} offline.".format(system.name))
            system.current_power -= rate
            if system.current_power < 0:
                system.set_power = 0
                system.current_power = 0
            if system.set_power == system.current_power:
                consuming.remove(system)
                for console in target.db.consoles:
                    console.notify("{} now at {}".format(system.name, system.percent()))
