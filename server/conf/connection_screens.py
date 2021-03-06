# -*- coding: utf-8 -*-
"""
Connection screen

Texts in this module will be shown to the user at login-time.

Evennia will look at global string variables (variables defined
at the "outermost" scope of this module and use it as the
connection screen. If there are more than one, Evennia will
randomize which one it displays.

The commands available to the user when the connection screen is shown
are defined in commands.default_cmdsets. UnloggedinCmdSet and the
screen is read and displayed by the unlogged-in "look" command.

"""

from django.conf import settings
from evennia import utils

CONNECTION_SCREEN = """
|Y==============================================================|n
|G                              _
  /\  /\_   _ _ __   _____  _(_) __ _
 / /_/ / | | | '_ \ / _ \ \/ / ||/ _` |
/ __  /| ||_| | ||_) | (_) >  <| | (_| |
\/ /_/  \__, | .__/ \___/_/\_\_|\__,_|
        ||___/||_|
        
 |nWelcome to |G{}|n
 Running Evennia, version {}

 If you have an existing account, connect to it by typing:
      |wconnect <username> <password>|n
 If you need to create an account, type (without the <>'s):
      |wcreate <username> <password>|n

 If you have spaces in your username, enclose it in quotes.
 Enter |whelp|n for more info. |wlook|n will re-show this screen.
|Y==============================================================|n""" \
    .format(settings.SERVERNAME, utils.get_evennia_version())
