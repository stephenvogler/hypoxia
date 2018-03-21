"""
Evennia settings file.

The available options are found in the default settings file found
here:

/home/svogler/muddev/evennia/evennia/settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Hypoxia: Enter the Void"

# Server ports. If enabled and marked as "visible", the port
# should be visible to the outside world on a production server.
# Note that there are many more options available beyond these.

# Telnet ports. Visible.
TELNET_ENABLED = True
TELNET_PORTS = [4000]
# (proxy, internal). Only proxy should be visible.
WEBSERVER_ENABLED = True
WEBSERVER_PORTS = [(4001, 4002)]
# Telnet+SSL ports, for supporting clients. Visible.
SSL_ENABLED = False
SSL_PORTS = [4003]
# SSH client ports. Requires crypto lib. Visible.
SSH_ENABLED = False
SSH_PORTS = [4004]
# Websocket-client port. Visible.
WEBSOCKET_CLIENT_ENABLED = True
WEBSOCKET_CLIENT_PORT = 4005
# Internal Server-Portal port. Not visible.
AMP_PORT = 4006

DEFAULT_CHANNELS = [
    # public channel
    {"key": "Public",
     "aliases": ('pub'),
     "desc": "Public discussion",
     "locks": "control:perm(Admin);listen:all();send:all()"},
    # connection/mud info
    {"key": "Login",
     "aliases": "",
     "desc": "Connection log",
     "locks": "control:perm(Developer);listen:all();send:false()"},
    # newbie channel
    {"key": "Newbie",
     "aliases": "new",
     "desc": "Help for newbies",
     "locks": "control:perm(Admin);listen:all();send:all()"},
    # space system
    {"key": "Space",
     "aliases": "",
     "desc": "Space system messages",
     "locks": "control:perm(Admin);listen:perm(Admin);send:all()"},
    # combat system
    {"key": "Combat",
     "aliases": "",
     "desc": "Combat system messages",
     "locks": "control:perm(Immortals);listen:perm(Admin);send:all()"},
    {"key": "RPS",
     "aliases": "",
     "desc": "Role Play system messages",
     "locks": "control:perm(Immortals);listen:perm(Admin);send:all()"},
    # economy system
    {"key": "Econ",
     "aliases": "",
     "desc": "Economy system messages",
     "locks": "control:perm(Immortals);listen:perm(Admin);send:all()"}
]
TYPECLASS_PATHS = ["typeclasses", "evennia", "evennia.contrib", "evennia.contrib.tutorial_examples", "world.space"]
GAME_INDEX_LISTING = {
    'game_status': 'pre-alpha',
    # Optional, comment out or remove if N/A
    #'game_website': 'http://my-game.com',
    'short_description': 'A gritty sci-fi game set in a less-than-utopian world.',
    # Optional but highly recommended. Markdown is supported.
    'long_description': (
        "Hypoxia: Enter the Void\n\n"
        "Hypoxia is an RP encouraged MUD/MUSH set in the distant future. "
        "Man has reached the stars, but brought corruption with him.\n\n"
        "Custome space engine, full-featured economy system, and more to come."
    ),
    'listing_contact': 'stephen.vogler@gmail.com',
    # At minimum, specify this or the web_client_url options. Both is fine, too.
    'telnet_hostname': 'hypoxia.ddns.net',
    'telnet_port': 4000,
    # At minimum, specify this or the telnet_* options. Both is fine, too.
    'web_client_url': 'http://hypoxia.ddns.net:4001/webclient/',
}
######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print "secret_settings.py file not found or failed to import."
