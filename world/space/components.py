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

SHIP_TEMPLATES = ('galaxy')
STATION_TEMPLATES = ('')

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
            'reactor': {'type': 'producer', 'name': 'Reactor', 'extra': {}},
            'core': {'type': 'producer', 'name': 'Core', 'extra': {}},
            'ftl_engines': {'name': 'FTL Engines', 'extra': {}},
            'sublight_engines': {'name': 'Sublight Engines', 'extra': {}},
            'sensors': {'name': 'Sensors', 'extra': ({'contacts': {}})},
            'beam_control': {'name': 'Beam Control', 'extra': {}},
            'torpedo_control': {'name': 'Torpedo Control', 'extra': {}},
            'shield_manager': {'name': 'Shield Manager', 'extra': {}},
            'communications': {'name': 'Communications Array', 'extra': {}},
            'tractor_system': {'name': 'Tractor Emmiters', 'extra': {}},
            'life_support': {'name': 'Life Support System', 'extra': {}},
            'computer_core': {'name': 'Computer Core', 'extra': {}},
            'ecm': {'name': 'ECM System', 'extra': {}},
            'eccm': {'name': 'ECCM System', 'extra': {}},
            'power_grid': {'type': 'router', 'name': 'Power Grid', 'extra': {}},
        }

class Galaxy(Template):
    def __init__(self):
        super(Galaxy, self).__init__()
        self.name = 'Galaxy Class'

        self.systems['reactor']['name'] = 'Fusion Reactor'
        self.systems['core']['name'] = 'Warp core'
