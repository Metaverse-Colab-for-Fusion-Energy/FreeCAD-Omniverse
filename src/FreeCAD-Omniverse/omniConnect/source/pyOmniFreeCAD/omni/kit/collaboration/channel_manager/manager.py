# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import asyncio
import concurrent.futures
import weakref
import json
import logging
import omni.client

from functools import partial
from typing import Callable, Dict, List
from .types import Message, MessageType, PeerUser
import log, tick_update
LOGGER = log.get_logger("PyChannelManager", level=logging.INFO)


KIT_OMNIVERSE_CHANNEL_MESSAGE_HEADER = b'__OVUM__'
KIT_CHANNEL_MESSAGE_VERSION = "3.0"
OMNIVERSE_CHANNEL_URL_SUFFIX = ".__omni_channel__"
OMNIVERSE_CHANNEL_NEW_URL_SUFFIX = ".channel"
MESSAGE_VERSION_KEY = "version"
MESSAGE_FROM_USER_NAME_KEY = "from_user_name"
MESSAGE_CONTENT_KEY = "content"
MESSAGE_TYPE_KEY = "message_type"
MESSAGE_APP_KEY = "app"

def _build_message_in_bytes(from_user, message_type, content, app_name):
    content = {
        MESSAGE_VERSION_KEY: KIT_CHANNEL_MESSAGE_VERSION,
        MESSAGE_TYPE_KEY: message_type,
        MESSAGE_FROM_USER_NAME_KEY: from_user,
        MESSAGE_CONTENT_KEY: content,
        MESSAGE_APP_KEY: app_name,
    }

    content_bytes = json.dumps(content).encode()
    return KIT_OMNIVERSE_CHANNEL_MESSAGE_HEADER + content_bytes


class ChannelSubscriber:
    """Handler of subscription to a channel."""

    def __init__(self, message_handler: Callable[[Message], None], channel: weakref) -> None:
        """
        Constructor. Internal only.
        
        Args:
            message_handler (Callable[[Message], None]): Message handler to handle message.
            channel (weakref): Weak holder of channel.
        """

        self._channel = channel
        self._message_handler = message_handler

    def __del__(self):
        self.unsubscribe()

    def unsubscribe(self):
        """Stop subscribe."""

        self._message_handler = None
        if self._channel and self._channel():
            self._channel()._remove_subscriber(self)

    def _on_message(self, message: Message):
        if self._message_handler:
            self._message_handler(message)


class NativeChannelWrapper:
    """
    Channel is the manager that manages message receive and distribution to MessageSubscriber. It works
    in subscribe/publish pattern.
    """

    def __init__(self, url: str, get_users_only: bool, app_name: str):
        """
        Constructor. Internal only.
        """

        self._url = url
        self._logged_user_name = ""
        self._peer_users: Dict[str, PeerUser] = {}
        self._channel_handler = None
        self._subscribers = []
        self._message_queue = []
        self._stopped = False
        self._get_users_only = get_users_only
        self._stopping = False
        self._app_name = app_name

    @property
    def url(self) -> str:
        """Property. The channel url in Omniverse."""

        return self._url

    @property
    def stopped(self) -> bool:
        """Property. If this channel is stopped already."""

        return self._stopped or not self._channel_handler or self._channel_handler.is_finished()
    
    @property
    def stopping(self) -> bool:
        return self._stopping

    @property
    def logged_user_name(self) -> str:
        """Property. The logged user name for this channel."""

        return self._logged_user_name

    @property
    def peer_users(self) -> Dict[str, PeerUser]:
        """Property. All the peer clients that joined to this channel."""

        return self._peer_users

    async def join_channel_async(self):
        """
        Async function. Join Omniverse Channel.

        Args:
            url: The url to create/join a channel.
            get_users_only: Johns channel as a monitor only or not.
        """
        
        LOGGER.info(f"Starting to join channel: {self.url}")

        if self._channel_handler:
            self._channel_handler.stop()
            self._channel_handler = None

        # Gets the logged user information.
        try:
            result, server_info = await omni.client.get_server_info_async(self.url)
            if result != omni.client.Result.OK:
                return False

            self._logged_user_name = server_info.username
        except Exception as e:
            LOGGER.error(f"Failed to join channel {self.url} since user token cannot be got: {str(e)}.")
            return False

        channel_connect_future = concurrent.futures.Future()
        
        # TODO: Should this function be guarded with mutex?
        # since it's called in another native thread.
        def on_channel_message(
            channel, result: omni.client.Result, event_type: omni.client.ChannelEvent, from_user: str, content
        ):
            if not channel_connect_future.done():
                LOGGER.info(f"Join channel {self.url} successfully.")
                channel_connect_future.set_result(result == omni.client.Result.OK)
                
            if result != omni.client.Result.OK:
                LOGGER.warn(f"Stop channel since it has errors: {result}.")
                channel._stopped = True
                return

            #LOGGER.warn(f"Channel Message Receieved: {event_type}: {content}")
            channel._on_message(event_type, from_user, content)

        self._channel_handler = omni.client.join_channel_with_callback(self.url, partial(on_channel_message, self))
        result = channel_connect_future.result()
        if result:
            if self._get_users_only:
                await self._send_message_internal_async(MessageType.GET_USERS, {})
            else:
                await self._send_message_internal_async(MessageType.JOIN, {})

        return result

    def stop(self):
        """Stop this channel."""
        if self._stopping or self.stopped:
            return

        self._stopping = True
        return asyncio.ensure_future(self._stop_async())

    async def _stop_async(self):
        LOGGER.info(f"Stopping channel {self.url}.")
        if self._channel_handler and not self._channel_handler.is_finished():
            await self._send_message_internal_async(MessageType.LEFT, {})
            self._channel_handler.stop()
        self._channel_handler = None
        self._stopped = True
        self._stopping = False

    def add_subscriber(self, on_message: Callable[[Message], None]) -> ChannelSubscriber:
        subscriber = ChannelSubscriber(on_message, weakref.ref(self))
        self._subscribers.append(weakref.ref(subscriber))

        return subscriber

    def _remove_subscriber(self, subscriber: ChannelSubscriber):
        to_be_removed = []
        for item in self._subscribers:
            if not item() or item() == subscriber:
                to_be_removed.append(item)
        
        for item in to_be_removed:
            self._subscribers.remove(item)

    async def send_message_async(self, content: dict) -> omni.client.Request:
        if self.stopped or self.stopping:
            return

        return await self._send_message_internal_async(MessageType.MESSAGE, content)

    async def send_get_users_message_async(self) -> omni.client.Request:
        if self.stopped or self.stopping:
            return

        return await self._send_message_internal_async(MessageType.GET_USERS, {})

    async def _send_message_internal_async(self, message_type: MessageType, content: dict):
        LOGGER.info(f"Send {message_type} message to channel {self.url}, content: {content}")
        message = _build_message_in_bytes(self._logged_user_name, message_type, content, self._app_name)
        return await omni.client.send_message_async(self._channel_handler.id, message)

    def _update(self):
        if self.stopped or self._stopping:
            return

        for message in self._message_queue:
            self._handle_message(message[0], message[1], message[2])
        self._message_queue.clear()

    def _on_message(self, event_type: omni.client.ChannelEvent, from_user: str, content):
        # Queue message handling to main looper.
        self._message_queue.append((event_type, from_user, content))

    def _handle_message(self, event_type: omni.client.ChannelEvent, from_user: str, content):
        # Sent from me, skip them
        if not from_user:
            return

        peer_user = None
        payload = {}
        message_type = None
        if event_type == omni.client.ChannelEvent.JOIN:
            # We don't use JOIN from server
            pass
        elif event_type == omni.client.ChannelEvent.LEFT:
            peer_user = self._peer_users.pop(from_user, None)
            if peer_user:
                message_type = MessageType.LEFT
        elif event_type == omni.client.ChannelEvent.DELETED:
            self._channel_handler.stop()
            self._channel_handler = None
        elif event_type == omni.client.ChannelEvent.MESSAGE:
            LOGGER.info(f"Message received from user with id {from_user}.")
            try:
                header_len = len(KIT_OMNIVERSE_CHANNEL_MESSAGE_HEADER)
                bytes = memoryview(content).tobytes()
                if len(bytes) < header_len:
                    LOGGER.error(f"Unsupported message received from user {from_user}.")
                else:
                    bytes = bytes[header_len:]
                message = json.loads(bytes)
            except json.decoder.JSONDecodeError as e:
                LOGGER.error(f"Failed to decode message sent from user {from_user}: error - {e}")
                return

            version = message.get(MESSAGE_VERSION_KEY, None)
            if not version or version != KIT_CHANNEL_MESSAGE_VERSION:
                LOGGER.warn(f"Message version sent from user {from_user} does not match expected one: {message}.")
                return

            from_user_name = message.get(MESSAGE_FROM_USER_NAME_KEY, None)
            if not from_user_name:
                LOGGER.warn(f"Message sent from unknown user: {message}")
                return

            message_type = message.get(MESSAGE_TYPE_KEY, None)
            if not message_type:
                LOGGER.warn(f"Message sent from user {from_user} does not include message type.")
                return
            
            if message_type == MessageType.GET_USERS:
                LOGGER.info(f"Fetch message from user with id {from_user}, name {from_user_name}.")
                if not self._get_users_only:
                    asyncio.ensure_future(self._send_message_internal_async(MessageType.HELLO, {}))
                
                return
                
            peer_user = self._peer_users.get(from_user, None)
            if not peer_user:
                # Don't handle non-recorded user's left.
                if message_type == MessageType.LEFT:
                    LOGGER.info(f"User {from_user}, name {from_user_name} left channel.")
                    return
                else:
                    from_app = message.get(MESSAGE_APP_KEY, "Unknown")
                    peer_user = PeerUser(from_user, from_user_name, from_app)
                    self._peer_users[from_user] = peer_user

            if message_type == MessageType.HELLO:
                LOGGER.info(f"Hello message from user with id {from_user}, name {from_user_name}.")
            elif message_type == MessageType.JOIN:
                LOGGER.info(f"Join message from user with id {from_user}, name {from_user_name}.")
                if not self._get_users_only:
                    asyncio.ensure_future(self._send_message_internal_async(MessageType.HELLO, {}))
            elif message_type == MessageType.LEFT:
                LOGGER.info(f"Left message from user with id {from_user}, name {from_user_name}.")
                self._peer_users.pop(from_user, None)
            else:
                message_content = message.get(MESSAGE_CONTENT_KEY, None)
                if not message_content or not isinstance(message_content, dict):
                    LOGGER.warn(f"Message content sent from user {from_user} is empty or invalid format: {message}.")
                    return

                LOGGER.info(f"Message received from user with id {from_user}: {message}.")
                payload = message_content
                message_type = MessageType.MESSAGE

        if message_type and peer_user:
            message = Message(peer_user, message_type, payload)
            for subscriber in self._subscribers:
                if subscriber():
                    subscriber()._on_message(message)
                

class Channel:
    def __init__(self, handler: weakref, channel_manager: weakref) -> None:
        self._handler = handler
        self._channel_manager = channel_manager
        if self._handler and self._handler():
            self._url = self._handler().url
        else:
            self._url = ""
    
    def __del__(self):
        self.stop()
    
    @property
    def stopped(self):
        return not self._handler or not self._handler() or self._handler().stopped
    
    @property
    def url(self):
        return self._url

    def stop(self):
        if not self.stopped and self._channel_manager and self._channel_manager():
            self._channel_manager()._stop_channel(self._handler())
    
    def add_subscriber(self, on_message: Callable[[Message], None]) -> ChannelSubscriber:
        """
        Add subscriber.

        Args:
            on_message (Callable[[Message], None]): The message handler.
        
        Returns:
            Instance of ChannelSubscriber. The channel will be stopped if instance is release.
            So it needs to hold the instance before it's stopped. You can manually call `stop`
            to stop this channel, or set the returned instance to None.
        """
        if not self.stopped:
            return self._handler().add_subscriber(on_message)
        
        return None
    
    async def send_message_async(self, content: dict) -> omni.client.Request:
        """
        Async function. Send message to all peer clients.

        Args:
            content (dict): The message composed in dictionary.
        
        Return:
            omni.client.Request.
        """
        if not self.stopped:
            return await self._handler().send_message_async(content)

    async def send_get_users_message_async(self) -> omni.client.Request:
        """
        Async function. Send get_users message to all peer clients.

        Return:
            omni.client.Request.
        """
        if not self.stopped:
            return await self._handler().send_get_users_message_async()

        return None


class ChannelManager:
    def __init__(self, app_name = "") -> None:
        self._all_channels: List[NativeChannelWrapper] = []
        self._update_subscription = None
        self._stop_tasks = []
        self._app_name = app_name

    def on_startup(self):
        LOGGER.info("Starting Omniverse Channel Manager...")
        self._all_channels.clear()
        #app = omni.kit.app.get_app()
        #self._update_subscription = app.get_update_event_stream().create_subscription_to_pop(
        #    self._on_update, name="omni.kit.collaboration.channel_manager update"
        #)
        tick_update_instance = tick_update.get_instance()
        if tick_update_instance:
            tick_update_instance.register_update_callback(self._on_update)
        else:
            LOGGER.error("There's no tick_update instance, cannot process channel messages")

    def on_shutdown(self):
        LOGGER.info("Shutting down Omniverse Channel Manager...")
        self._update_subscription = None
        tick_update_instance = tick_update.get_instance()
        if tick_update_instance:
            tick_update_instance.unregister_update_callback(self._on_update)

        for channel in self._all_channels:
            self._stop_channel(channel)
        self._all_channels.clear()

        for task in self._stop_tasks:
            try:
                if not task.done():
                    task.cancel()
            except Exception:
                pass
        self._stop_tasks = []
    
    def _stop_channel(self, channel: NativeChannelWrapper):
        if channel and not channel.stopping:
            self._stop_tasks.append(channel.stop())

    def _on_update(self, dt):
        #LOGGER.info("update")
        to_be_removed = []
        for channel in self._all_channels:
            if channel.stopped:
                to_be_removed.append(channel)
            else:
                channel._update()

        for channel in to_be_removed:
            self._all_channels.remove(channel)
        
        to_be_removed = []
        for task in self._stop_tasks:
            if task.done():
                to_be_removed.append(task)
        
        for task in to_be_removed:
            self._stop_tasks.remove(task)

    def has_channel(self, url: str):
        for channel in self._all_channels:
            if url == channel:
                return True
        
        return False

    async def join_channel_async(self, url: str, get_users_only: bool):
        """
        Async function. Join Omniverse Channel.

        Args:
            url: The url to create/join a channel.
            get_users_only: Johns channel as a monitor only or not.
        """
        channel_wrapper = NativeChannelWrapper(url, get_users_only, self._app_name)

        success = await channel_wrapper.join_channel_async()
        if success:
            self._all_channels.append(channel_wrapper)
            channel = Channel(weakref.ref(channel_wrapper), weakref.ref(self))
        else:
            channel = None
        
        return channel

