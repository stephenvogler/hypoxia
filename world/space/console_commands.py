from evennia import Command, utils
#from evennia.utils import search
#from objects import *
import re
from world.space.objects import *
from evennia.utils.utils import inherits_from

class CmdMan(Command):
    """
    Usage:
      man [console] || unman [console]

    Man or unman a console.
    """
    key = 'man'
    aliases = 'unman'
    locks = 'cmd:all()'
    arg_regex = '\\s|$'
    help_category = 'Console'

    def func(self):
        target = self.caller
        console = target.search(self.args.strip())
        if 'unman' in self.cmdstring:
            if not target.db.console:
                target.msg("You're not manning anything!")
                return
            target.unman()
        else:
            if target.db.console:
                target.msg("You're already manning " +
                           target.db.console.name + '.')
                return
            if not self.args:
                target.msg('You must specify a console you wish to man.')
                return
            console = target.search(self.args.strip())
            if not console:
                return
            if not console.is_typeclass("world.space.objects.Console"):
                target.msg("You'd like that, wouldn't you?")
                return
            target.man(console)


class CmdLand(Command):
    """
    Usage:
      land <contact>

    <contact> must be able to be landed upon.
    """
    key = 'land'
    locks = 'cmd:is_operator()'
    help_category = 'Console'

    def func(self):
        console = self.caller.db.console
        spaceobj = console.db.spaceobj
        contacts = spaceobj.db.contacts
        target = spaceobj.search(self.args)
        #if target && target.landable():
        if target:
            console.notify("landing on %s." % target)
        else:
            console.notify("Invalid contact")

class CmdNavset(Command):
    """
    Usage:
      navset <mode> <parameters>

     |cnavset heading <#.##[+||-]#.##>|n - Sets absolute heading
     |cnavset relative <#.##[+||-]#.##>|n - Sets relative heading
     |cnavset speed <#>%|n - Sets speed to percentage of maximum
     |cnavset autopilot <on||off>|n -Turns autopilot off an on
    """
    key = 'navset'
    locks = 'cmd:is_operator()'
    help_category = 'Console'
    console_mode = 'helm'

    def parse(self):

        if "speed" in self.args:
            self.mode = "speed"
        elif "heading" in self.args:
            self.mode = "heading"
        elif "relative" in self.args:
            self.mode = "relative"
        elif "autopilot" in self.args:
            self.mode = "autopilot"
        else:
            self.mode = "unknown"
        try:
            self.args = self.args.replace(self.mode, "").strip()
        except:
            self.args = self.args.strip()

    def func(self):
        cmode = self.console_mode
        console = self.obj
        spaceobj = console.db.spaceobj

        if self.mode == "speed":
            if re.match("^[\d]+(\.\d+)?%?$", self.args):
                self.args = float(self.args.strip("%"))
                if self.args > 120:
                    console.notify(
                        "You cannot exceed 120% of the maximum rated setting.")
                    return
                cspeed = spaceobj.db.speed
                mspeed = spaceobj.maxspeed()
                dspeed = round(mspeed * (self.args / 100), 2)
                if dspeed == cspeed:
                    console.notify("Speed already set to {}% ({}).".format(
                        min_num(self.args), format_speed(dspeed)))
                    return
                console.notify("Speed set to {}% ({}).".format(
                    min_num(self.args), format_speed(dspeed)), cmode)
                spaceobj.setspeed(dspeed)
                return
        elif self.mode == "heading":
            match = re.match(
                "^([-\+]?\d+(\.\d+)?)([-\+]\d+(\.\d+)?)$", self.args)
            if match:
                heading = [round(float(match.group(1)), 2),
                           round(float(match.group(3)), 2)]
                if heading[0] == spaceobj.db.heading['xy'] and heading[1] == spaceobj.db.heading['z']:
                    console.notify("The ship is already heading %s." %
                                   format_bearing(heading))
                    return
                console.notify("Bringing the ship to %s." %
                               format_bearing(heading), cmode)
                spaceobj.setheading(heading)
                return
            else:
                console.notify("Invalid command syntax.")
                return
        elif self.mode == "relative":
            match = re.match(
                "^([-\+]?\d+(\.\d+)?)([-\+]\d+(\.\d+)?)$", self.args)
            if match:
                heading = [(round(float(match.group(1)), 2) + spaceobj.db.heading['xy'] + 360) %
                           360, (round(float(match.group(3)), 2) + spaceobj.db.heading['z'] + 360) % 360]
                console.notify("Bringing the ship to %s." %
                               format_bearing(heading), cmode)
                spaceobj.setheading(heading)
                return
            else:
                console.notify("Invalid command syntax.")
                return
            console.notify("Relative heading of %s set." % self.args, cmode)
        elif self.mode == "autopilot":
            console.notify("Autopilot turned %s." % self.args, cmode)
        console.notify("Invalid command syntax.")


class CmdNavstat(Command):
    """
    Usage:
      navset <mode> <parameters>
      navset speed <int>
      navset heading <xy mark z>

    Controls the spaceobj's helm and navigation
    """
    key = 'navstat'
    aliases = ["navinfo"]
    locks = 'cmd:is_operator()'
    help_category = 'Console'

    def func(self):
        spaceobj = self.obj.db.spaceobj
        position = spaceobj.position()
        heading = spaceobj.heading()
        speed = spaceobj.speed()
        header = '|[B|w[|yNavigation Status|w]|n\n'
        string = 'Position: %s\n' % format_position(position)
        string += 'Heading: %s Speed: %s' % (
            format_heading(heading), format_speed(speed))
        self.caller.msg(header + string)

class CmdSrep(Command):
    """
    Usage:
        fullscan || srep

    Returns a list of all objects that can be seen by the current space object's sensors, sorted by distance.

    Type flags: |cS|n: Ship |bP|n: Planet |M*|n: Star |mA|n: Anomaly |xB|n: Probe/Buoy |yU|n: Unknown

    ID: Transponder ID

    Range: Range is given in 'light seconds', '[Megameters]', or '>Kilometers<'
    """
    key = 'fullscan'
    aliases = 'srep'
    locks = 'cmd:is_operator()'
    help_category = 'Console'

    def func(self):
        spaceobj = self.obj.db.spaceobj
        if not spaceobj.systems.sensors.online():
            self.caller.db.console.notify("Sensors are offline.")
            return
        header = '|[B|w[|ySensor Report|w]|n Max Range: {}\n'.format(format_distance(spaceobj.sensor_range()))
        header += '|C-' * 78 + '\n' + '|c%1s %-20s %-22s %-14s%-12s %-7s' % (
            'T', 'Contact', 'ID', 'Bearing', 'Range', 'Speed') + '\n' + '|C-' * 78
        sort_list = sorted(spaceobj.systems.sensors.contacts.keys(), key=lambda o:o.dist3d(self.obj.db.spaceobj))
        contacts = ''
        for contact in sort_list:
            try:
                contacts += '\n%1s |w%-20s|n %-22s%-15s |n%-12s |n%-7s' % (contact.tflag(),
                                                                           contact.name, "[" + contact.name + "]",
                                                                           format_heading(spaceobj.bearing_to(
                                                                               contact)),
                                                                           format_distance(spaceobj.dist3d(
                                                                               contact)),
                                                                           contact.db.speed)
            except:
                # if we can't run that, it shouldn't be in here!
                self.caller.msg("Error!")
                del spaceobj.db.contacts[contact]
        if not contacts:
            contacts = "\n|rNo contacts|n"
        footer = '\n' + '|C-' * 78
        self.caller.msg(header + contacts + footer)

class CmdEngstat(Command):
    key = 'engstat'
    locks = 'cmd:is_operator()'
    def func(self):
        spaceobj = self.obj.db.spaceobj
        header = "|Y-" * 78
        producers = ""
        routers = ""
        consumers = ""
        footer = "|Y-" * 78
        for system in spaceobj.systems.all:
            system = spaceobj.systems.get(system)
            if system.destroyed():
                string = "|x{}: |RDESTROYED\n".format(system.name)
            else:
                string = "{}{}:|n {} / {}\n".format('|w' if system.online() else '|R', system.name, system.current_power, system.max_power)
            if system._data['type'] == 'producer':
                producers += string
            elif system._data['type'] == 'router':
                routers += string
            elif system._data['type'] == 'consumer':
                consumers += string
        #for system in systems:
            #string += "{}: {} / {} ({})".format(system.name, system.actual, system.max, system.percent)
        self.caller.msg(header + "\n|[B|w[|yPower Production|w]|n\n{}|[B|w[|yRouting|w]|n\n{}{}\n|[B|w[|ySystems|w]|n\n{}".format(producers, routers, '|G-' * 78, consumers) + footer)
class CmdFuelstat(Command):
    key = 'fuelstat'
    locks = 'cmd:is_operator()'
    def func(self):
        spaceobj = self.obj.db.spaceobj
        matter = spaceobj.systems.matter_storage
        antimatter = spaceobj.systems.antimatter_storage
        return self.caller.msg("{}: {} / {}: {}".format(matter.name, matter.fuel, antimatter.name, antimatter.fuel))

class CmdEngset(Command):
    key = 'engset'
    locks = 'cmd:is_operator()'
    def parse(self):
        if 'power' in self.args:
            self.mode = 'power'
            self.system = None
            system = find_system(self.obj.db.spaceobj, self.args.lstrip('power ').rstrip('0123456789').strip())
            try:
                self.setting = int(filter(str.isdigit, str(self.args)))
            except:
                self.setting = None
            if system == -1:
                return self.caller.msg("Ambiguous match. Please be more specific.")
            elif not system:
                return self.caller.msg("Unknown system, please try again.")
            else:
                self.system = system
        else:
            self.mode = None

    def func(self):
        console = self.obj
        if self.mode == 'power':
            if not self.system:
                return
            if not self.setting == None:
                if self.system.destroyed():
                    return console.notify("Unable to comply. |R{}: Destroyed|n".format(self.system.name))
                if self.setting > 100:
                    return console.notify("You cannot exceed 100% of max power.")
                if self.system.set_power == self.setting:
                    return console.notify("{} already set to {}%".format(self.system.name, self.setting))
                self.system.set_power = self.system.max_power * self.setting / 100
                console.notify("{} set to {}%".format(self.system.name, self.setting))
                UpdatePower(console.db.spaceobj)
            else:
                console.notify("{}: {}/{}".format(self.system.name, self.system.current_power, self.system.max_power))
        else:
            return self.caller.msg("Try 'help engset'.")

def find_system(spaceobj, target_system):
    systems = []
    for system in spaceobj.systems.all:
        if target_system in spaceobj.systems.get(system).name.lower():
            systems.append(str(system))
    if systems:
        system = spaceobj.systems.get(systems[0])
        return system
    else:
        return 0
