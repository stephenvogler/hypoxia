
from evennia.utils.dbserialize import _SaverDict
from evennia.utils import logger, lazy_property
from functools import total_ordering

SYSTEM_TYPES = ('producer', 'consumer', 'static')
RANGE_TRAITS = ('counter', 'gauge')


class SystemException(Exception):
    """Base exception class raised by `System` objects.
    Args:
        msg (str): informative error message
    """
    def __init__(self, msg):
        self.msg = msg


class SystemHandler(object):
    """Factory class that instantiates system objects.
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
        return self.get(trait)

    def __getitem__(self, system):
        """Returns `System` instances accessed as dict keys."""
        return self.get(trait)

    def get(self, system):
        """
        Args:
            system (str): key from the systems dict containing config data
                for the system. "all" returns a list of all trait keys.
        Returns:
            (`System` or `None`): named System class or None if system key
            is not found in system collection.
        """
        if system not in self.cache:
            if system not in self.attr_dict:
                return None
            data = self.attr_dict[system]
            self.cache[system] = System(data)
        return self.cache[system]

    def add(self, key, name, type='consumer',
            base=0, mod=0, min=None, max=None, extra={}):
        """Create a new Trait and add it to the handler."""
        if key in self.attr_dict:
            raise TraitException("Trait '{}' already exists.".format(key))

        if type in TRAIT_TYPES:
            trait = dict(name=name,
                         type=type,
                         base=base,
                         mod=mod,
                         extra=extra)
            if min:
                trait.update(dict(min=min))
            if max:
                trait.update(dict(max=max))

            self.attr_dict[key] = trait
        else:
            raise TraitException("Invalid trait type specified.")

    def remove(self, trait):
        """Remove a Trait from the handler's parent object."""
        if trait not in self.attr_dict:
            raise TraitException("Trait not found: {}".format(trait))

        if trait in self.cache:
            del self.cache[trait]
        del self.attr_dict[trait]

    def clear(self):
        """Remove all Traits from the handler's parent object."""
        for trait in self.all:
            self.remove(trait)

    @property
    def all(self):
        """Return a list of all trait keys in this TraitHandler."""
        return self.attr_dict.keys()


@total_ordering
class Trait(object):
    """Represents an object or Character trait.
    Note:
        See module docstring for configuration details.
    """
    def __init__(self, data):
        if not 'name' in data:
            raise TraitException(
                "Required key not found in trait data: 'name'")
        if not 'type' in data:
            raise TraitException(
                "Required key not found in trait data: 'type'")
        self._type = data['type']
        if not 'base' in data:
            data['base'] = 0
        if not 'mod' in data:
            data['mod'] = 0
        if not 'extra' in data:
            data['extra'] = {}
        if 'min' not in data:
            data['min'] = 0 if self._type == 'gauge' else None
        if 'max' not in data:
            data['max'] = 'base' if self._type == 'gauge' else None

        self._data = data
        self._keys = ('name', 'type', 'base', 'mod',
                      'current', 'min', 'max', 'extra')
        self._locked = True

        if not isinstance(data, _SaverDict):
            logger.log_warn(
                'Non-persistent {} class loaded.'.format(
                    type(self).__name__
                ))

    def __repr__(self):
        """Debug-friendly representation of this Trait."""
        return "{}({{{}}})".format(
            type(self).__name__,
            ', '.join(["'{}': {!r}".format(k, self._data[k])
                for k in self._keys if k in self._data]))

    def __str__(self):
        """User-friendly string representation of this `Trait`"""
        if self._type == 'gauge':
            status = "{actual:4} / {base:4}".format(
                actual=self.actual,
                base=self.base)
        else:
            status = "{actual:11}".format(actual=self.actual)

        return "{name:12} {status} ({mod:+3})".format(
            name=self.name,
            status=status,
            mod=self.mod)

    def __unicode__(self):
        """User-friendly unicode representation of this `Trait`"""
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
        Arbitrary attributes set on a Trait object will be
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
                super(Trait, self).__setattr__(key, value)

    def __delattr__(self, key):
        """Delete extra parameters as attributes."""
        if key in self._data['extra']:
            del self._data['extra'][key]

    # Numeric operations magic

    def __eq__(self, other):
        """Support equality comparison between Traits or Trait and numeric.
        Note:
            This class uses the @functools.total_ordering() decorator to
            complete the rich comparison implementation, therefore only
            `__eq__` and `__lt__` are implemented.
        """
        if type(other) == Trait:
            return self.actual == other.actual
        elif type(other) in (float, int):
            return self.actual == other
        else:
            return NotImplemented

    def __lt__(self, other):
        """Support less than comparison between `Trait`s or `Trait` and numeric."""
        if isinstance(other, Trait):
            return self.actual < other.actual
        elif type(other) in (float, int):
            return self.actual < other
        else:
            return NotImplemented

    def __pos__(self):
        """Access `actual` property through unary `+` operator."""
        return self.actual

    def __add__(self, other):
        """Support addition between `Trait`s or `Trait` and numeric"""
        if isinstance(other, Trait):
            return self.actual + other.actual
        elif type(other) in (float, int):
            return self.actual + other
        else:
            return NotImplemented

    def __sub__(self, other):
        """Support subtraction between `Trait`s or `Trait` and numeric"""
        if isinstance(other, Trait):
            return self.actual - other.actual
        elif type(other) in (float, int):
            return self.actual - other
        else:
            return NotImplemented

    def __mul__(self, other):
        """Support multiplication between `Trait`s or `Trait` and numeric"""
        if isinstance(other, Trait):
            return self.actual * other.actual
        elif type(other) in (float, int):
            return self.actual * other
        else:
            return NotImplemented

    def __floordiv__(self, other):
        """Support floor division between `Trait`s or `Trait` and numeric"""
        if isinstance(other, Trait):
            return self.actual // other.actual
        elif type(other) in (float, int):
            return self.actual // other
        else:
            return NotImplemented

    # yay, commutative property!
    __radd__ = __add__
    __rmul__ = __mul__

    def __rsub__(self, other):
        """Support subtraction between `Trait`s or `Trait` and numeric"""
        if isinstance(other, Trait):
            return other.actual - self.actual
        elif type(other) in (float, int):
            return other - self.actual
        else:
            return NotImplemented

    def __rfloordiv__(self, other):
        """Support floor division between `Trait`s or `Trait` and numeric"""
        if isinstance(other, Trait):
            return other.actual // self.actual
        elif type(other) in (float, int):
            return other // self.actual
        else:
            return NotImplemented

    # Public members

    @property
    def name(self):
        """Display name for the trait."""
        return self._data['name']

    @property
    def actual(self):
        """The "actual" value of the trait."""
        if self._type == 'gauge':
            return self.current
        elif self._type == 'counter':
            return self._mod_current()
        else:
            return self._mod_base()

    @property
    def base(self):
        """The trait's base value.
        Note:
            The setter for this property will enforce any range bounds set
            on this `Trait`.
        """
        return self._data['base']

    @base.setter
    def base(self, amount):
        if self._data.get('max', None) == 'base':
            self._data['base'] = amount
        if type(amount) in (int, float):
            self._data['base'] = self._enforce_bounds(amount)

    @property
    def mod(self):
        """The trait's modifier."""
        return self._data['mod']

    @mod.setter
    def mod(self, amount):
        if type(amount) in (int, float):
            delta = amount - self._data['mod']
            self._data['mod'] = amount
            if self._type == 'gauge':
                if delta >= 0:
                    # apply increases to current
                    self.current = self._enforce_bounds(self.current + delta)
                else:
                    # but not decreases, unless current goes out of range
                    self.current = self._enforce_bounds(self.current)

    @property
    def min(self):
        """The lower bound of the range."""
        if self._type in RANGE_TRAITS:
            return self._data['min']
        else:
            raise AttributeError(
                "static 'Trait' object has no attribute 'min'.")

    @min.setter
    def min(self, amount):
        if self._type in RANGE_TRAITS:
            if amount is None: self._data['min'] = amount
            elif type(amount) in (int, float):
                self._data['min'] = amount if amount < self.base else self.base
        else:
            raise AttributeError(
                "static 'Trait' object has no attribute 'min'.")

    @property
    def max(self):
        """The maximum value of the `Trait`.
        Note:
            This property may be set to the string literal 'base'.
            When set this way, the property returns the value of the
            `mod`+`base` properties.
        """
        if self._type in RANGE_TRAITS:
            if self._data['max'] == 'base':
                return self._mod_base()
            else:
                return self._data['max']
        else:
            raise AttributeError(
                "static 'Trait' object has no attribute 'max'.")

    @max.setter
    def max(self, value):
        if self._type in RANGE_TRAITS:
            if value == 'base' or value is None:
                self._data['max'] = value
            elif type(value) in (int, float):
                self._data['max'] = value if value > self.base else self.base
        else:
            raise AttributeError(
                "static 'Trait' object has no attribute 'max'.")

    @property
    def current(self):
        """The `current` value of the `Trait`."""
        if self._type == 'gauge':
            return self._data.get('current', self._mod_base())
        else:
            return self._data.get('current', self.base)

    @current.setter
    def current(self, value):
        if self._type in RANGE_TRAITS:
            if type(value) in (int, float):
                self._data['current'] = self._enforce_bounds(value)
        else:
            raise AttributeError(
                "'current' property is read-only on static 'Trait'.")

    @property
    def extra(self):
        """Returns a list containing available extra data keys."""
        return self._data['extra'].keys()

    def reset_mod(self):
        """Clears any mod value on the `Trait`."""
        self.mod = 0

    def reset_counter(self):
        """Resets `current` property equal to `base` value."""
        self.current = self.base

    def fill_gauge(self):
        """Adds the `mod`+`base` to the `current` value.
        Note:
            Will honor the upper bound if set.
        """
        self.current = \
            self._enforce_bounds(self.current + self._mod_base())

    def percent(self):
        """Returns the value formatted as a percentage."""
        if self._type in RANGE_TRAITS:
            if self.max:
                return "{:3.1f}%".format(self.current * 100.0 / self.max)
            elif self._type == 'counter' and self.base != 0:
                return "{:3.1f}%".format(self.current * 100.0 / self._mod_base())
            elif self._type == 'gauge' and self._mod_base() != 0:
                return "{:3.1f}%".format(self.current * 100.0 / self._mod_base())
        # if we get to this point, it's either a static trait or
        # a divide by zero situation
        return "100.0%"

    # Private members

    def _mod_base(self):
        return self._enforce_bounds(self.mod + self.base)

    def _mod_current(self):
        return self._enforce_bounds(self.mod + self.current)

    def _enforce_bounds(self, value):
        """Ensures that incoming value falls within trait's range."""
        if self._type in RANGE_TRAITS:
            if self.min is not None and value <= self.min:
                return self.min
            if self._data['max'] == 'base' and value >= self.mod + self.base:
                return self.mod + self.base
            if self.max is not None and value >= self.max:
                return self.max
        return value
