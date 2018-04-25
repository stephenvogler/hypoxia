"""
Spaceobj has basic settings for hull on it already
Component: Provides functionality to SpaceObject
    Reactor: Generates power
        Warp core (FTL core?)
            Antimater fuel storage
        Fusion reactors
            Matter fuel storage
    Battery: Stores power
    Distribution (EPS grid?): Distributes / allocates power
    System: Use power to produce capability
        Containment (WCCF?)
        IDF
        SIF
        Engines:            [standard/sustainable/max, max size, rating]
            FTL
            Sublight
        Weapons:            [offense value, penetration, rating]
            Beam control
            Torpedo control
        Shield manager      [protection, base threshold, max threshol, rating]
        Sensors:            [1,0,0,0 , 2,1,0,0 , 3,2,1,0 etc]
            PSR sensors
            PLR sensors
            ASR sensors
            ALR Sensors
        Communications
        Tractor beam emitters
        Transporters
        Life Support
        Computer core
        ECM
        ECCM

                    Ranges: Point blank(<=1k), Close(1-10k), Medium(50k), Long(100k), Extended(200k)
"""
class TemplateException(Exception):
    def __init__(self, msg):
        self.msg = msg

SHIP_TEMPLATES = ['defaultship', 'galaxy']
STATION_TEMPLATES = ['defaultstation']

ALL_TEMPLATES = (SHIP_TEMPLATES + STATION_TEMPLATES)

def apply_template(spaceobj, template, reset=False):
    """Set a spaceobj's systems and initialize
    Args:
        spaceobj (SpaceObject): the space object being initialized
        name (str): single system to apply
        reset (bool): if True, remove any current system and apply the named system
    """
    tname = template.lower()
    if tname not in ALL_TEMPLATES:
        raise TemplateException('Invalid template.')

    template = load_template(tname)
    spaceobj.db.spaceframe = template.name
    if reset:
        spaceobj.systems.clear()
    for key, kwargs in template.systems.iteritems():
        spaceobj.systems.add(key, **kwargs)

def load_template(template):
    template = template.title()
    try:
        template = globals().get(template, None)()
    except TypeError:
        raise TemplateException("Invalid template specified.")
    return template

class Template(object):
    """
    Sane defaults for all templates
    """
    def __init__(self):
        self.name = None
        self._desc = None

        self.systems = {
            'reactor': {'type': 'producer', 'name': 'Reactor', 'min_power': 1, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'core': {'type': 'producer', 'name': 'Core', 'min_power': 1, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'ftl_engines': {'name': 'FTL Engines', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'sublight_engines': {'name': 'Sublight Engines', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'sensors': {'name': 'Sensors', 'min_power': 10, 'max_power': 1750, 'max_hp': 100, 'extra': ({'contacts': {}})},
            'beam_control': {'name': 'Beam Control', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'torpedo_control': {'name': 'Torpedo Control', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'shield_manager': {'name': 'Shield Manager', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'communications': {'name': 'Communications Array', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'tractor_system': {'name': 'Tractor Emmiters', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'life_support': {'name': 'Life Support System', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'computer_core': {'name': 'Computer Core', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'ecm': {'name': 'ECM System', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'eccm': {'name': 'ECCM System', 'min_power': 10, 'max_power': 100, 'max_hp': 100, 'extra': {}},
            'power_grid': {'type': 'router', 'name': 'Power Grid', 'min_power': 0, 'max_power': 100, 'max_hp': 100, 'extra': ({'rate': 20, 'routing': 0})},
            'matter_storage': {'type': 'aux', 'name': 'Matter Storage', 'max_hp': 100, 'extra': {'fuel': 100}},
            'antimatter_storage': {'type': 'aux', 'name': 'Antimatter Storage', 'max_hp': 100, 'extra': {'fuel': 100}},
        }
class Defaultship(Template):
    def __init__(self):
        super(Defaultship, self).__init__()
        self.name = 'Generic Ship'

        self.systems['reactor']['name'] = 'Fusion Reactor'
        self.systems['core']['name'] = 'Warp core'

class Galaxy(Template):
    def __init__(self):
        super(Galaxy, self).__init__()
        self.name = 'Galaxy Class'

        self.systems['reactor']['name'] = 'Fusion Reactor'
        self.systems['core']['name'] = 'Warp core'

class Defaultstation(Template):
    def __init__(self):
        super(Defaultstation, self).__init__()
        self.name = 'Generic Station'

        self.systems['reactor']['name'] = 'Fusion Reactor'
        self.systems['core']['name'] = 'Warp core'
