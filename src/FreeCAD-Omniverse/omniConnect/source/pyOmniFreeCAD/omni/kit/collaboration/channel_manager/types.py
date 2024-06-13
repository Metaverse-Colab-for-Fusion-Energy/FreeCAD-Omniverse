# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
class PeerUser:
    """Information of peer user that's joined to the same channel."""

    def __init__(self, user_id: str, user_name: str, from_app: str) -> None:
        """
        Constructor. Internal only.

        Args:
            user_id (str): Unique user id.
            user_name (str): Readable user name.
        """

        self._user_id = user_id
        self._user_name = user_name
        self._from_app = from_app

    @property
    def user_id(self):
        """Property. Unique user id."""

        return self._user_id

    @property
    def user_name(self):
        """Property. Readable user name."""

        return self._user_name

    @property
    def from_app(self):
        """Property. Readable app name, like 'Kit', 'Maya', etc."""

        return self._from_app

class MessageType:
    JOIN = "JOIN"           # User is joined. Client should respond HELLO if it receives JOIN from new user.
    HELLO = "HELLO"         # Someone said hello to me. Normally, client sends HELLO when it receives 
    GET_USERS = "GET_USERS" # User does not join this channel, but wants to find who are inside this channel.
                            # Clients receive this message should respond with HELLO to broadcast its existence.
                            # Clients implement this command does not need to send JOIN firstly, and no LEFT sent
                            # also before quitting channel.
    LEFT = "LEFT"           # User left this channel.
    MESSAGE = "MESSAGE"     # Normal message after JOIN.


class Message:
    def __init__(self, from_user: PeerUser, message_type: MessageType, content: dict) -> None:
        """
        Constructor. Internal only.

        Args:
            from_user (PeerUser): User that message sent from.
            message_type (MessageType): Message type.
            content (dict): Message content in dict. 
        """

        self._from_user = from_user
        self._message_type = message_type
        self._content = content

    @property
    def from_user(self) -> PeerUser:
        """Property. User that message sent from."""

        return self._from_user

    @property
    def message_type(self) -> MessageType:
        """Property. Message type."""

        return self._message_type

    @property
    def content(self) -> dict:
        """Property. Message content in dictionary."""

        return self._content
    
    def __str__(self) -> str:
        return f"from: {self.from_user.user_name}, message_type: {self.message_type}, content: {self.content}"
