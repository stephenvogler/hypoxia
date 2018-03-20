"""
Channel

The channel class represents the out-of-character chat-room usable by
Accounts in-game. It is mostly overloaded to change its appearance, but
channels can be used to implement many different forms of message
distribution systems.

Note that sending data to channels are handled via the CMD_CHANNEL
syscommand (see evennia.syscmds). The sending should normally not need
to be modified.

"""

from evennia import DefaultChannel


class Channel(DefaultChannel):
    """
    Working methods:
        at_channel_creation() - called once, when the channel is created
        has_connection(account) - check if the given account listens to this channel
        connect(account) - connect account to this channel
        disconnect(account) - disconnect account from channel
        access(access_obj, access_type='listen', default=False) - check the
                    access on this channel (default access_type is listen)
        delete() - delete this channel
        message_transform(msg, emit=False, prefix=True,
                          sender_strings=None, external=False) - called by
                          the comm system and triggers the hooks below
        msg(msgobj, header=None, senders=None, sender_strings=None,
            persistent=None, online=False, emit=False, external=False) - main
                send method, builds and sends a new message to channel.
        tempmsg(msg, header=None, senders=None) - wrapper for sending non-persistent
                messages.
        distribute_message(msg, online=False) - send a message to all
                connected accounts on channel, optionally sending only
                to accounts that are currently online (optimized for very large sends)

    Useful hooks:
        channel_prefix(msg, emit=False) - how the channel should be
                  prefixed when returning to user. Returns a string
        format_senders(senders) - should return how to display multiple
                senders to a channel
        pose_transform(msg, sender_string) - should detect if the
                sender is posing, and if so, modify the string
        format_external(msg, senders, emit=False) - format messages sent
                from outside the game, like from IRC
        format_message(msg, emit=False) - format the message body before
                displaying it to the user. 'emit' generally means that the
                message should not be displayed with the sender's name.

        pre_join_channel(joiner) - if returning False, abort join
        post_join_channel(joiner) - called right after successful join
        pre_leave_channel(leaver) - if returning False, abort leave
        post_leave_channel(leaver) - called right after successful leave
        pre_send_message(msg) - runs just before a message is sent to channel
        post_send_message(msg) - called just after message was sent to channel

    """
    def channel_prefix(self, msg=None, emit=False):

        """
        Hook method. How the channel should prefix itself for users.

        Args:
            msg (str, optional): Prefix text
            emit (bool, optional): Switches to emit mode, which usually
                means to not prefix the channel's info.

        Returns:
            prefix (str): The created channel prefix.

        """
        if self.key == 'IRC':
            return '' if emit else '|Y[|nIRC|Y]|n '
        elif self.key == 'Staff':
            return '' if emit else '|M[|nStaff|M|n '
        elif self.key == 'Newbie':
            return '' if emit else '|y[|nNewbie|y]|n '
        return '' if emit else '|B[|w%s|B]|n ' % self.key
    def pre_join_channel(self, joiner):
        """
        Hook method. Runs right before a channel is joined. If this
        returns a false value, channel joining is aborted.

        Args:
            joiner (object): The joining object.

        Returns:
            should_join (bool): If `False`, channel joining is aborted.

        """
        self.msg("%s has joined this channel." % joiner.name)
        return True
    def mute(self, subscriber):
        """
        Adds an entity to the list of muted subscribers.
        A muted subscriber will no longer see channel messages,
        but may use channel commands.
        """
        mutelist = self.mutelist
        if subscriber not in mutelist:
            mutelist.append(subscriber)
            self.db.mute_list = mutelist
            self.msg("|R<Mute>|n %s has stopped listening to this channel." % subscriber.name)
            return True
        return False

    def unmute(self, subscriber):
        """
        Removes an entity to the list of muted subscribers.
        A muted subscriber will no longer see channel messages,
        but may use channel commands.
        """
        mutelist = self.mutelist
        if subscriber in mutelist:
            self.msg("|G<Unmute>|n %s has resumed listening to this channel." % subscriber.name)
            mutelist.remove(subscriber)
            self.db.mute_list = mutelist
            return True
        return False

    def post_leave_channel(self, leaver):
        """
        Hook method. Runs right after an object or player leaves a channel.

        Args:
            joiner (object): The joining object.

        """
        self.msg("%s has left this channel." % leaver.name)
        pass
    pass
