import asyncio
import logging
import omni.kit.collaboration.channel_manager as cm

#from .prompt import PromptButtonInfo, PromptManager
import log
LOGGER = log.get_logger("PyLiveSessionChannelManager", level=logging.INFO)

MESSAGE_GROUP_KEY = "__SESSION_MANAGEMENT__"
MESSAGE_KEY = "message"
MESSAGE_MERGE_STARTED = "MERGE_STARTED"
MESSAGE_MERGE_FINISHED = "MERGE_FINISHED"


class LiveSessionChannelManager:
    def __init__(self, channel_url: str, model):
        self._channel: cm.Channel = None
        self._channel_subscriber: cm.ChannelSubscriber = None
        self._join_channel_future = None
        self._channel_url = channel_url
        self._layer_model = model
        
        # Live session channel message callbacks
        self._join_callback = None
        self._hello_callback = None
        self._left_callback = None
        self._merge_start_callback = None
        self._merge_finished_callback = None
    
        # Session users
        self._peer_users: set(cm.types.PeerUser) = set()
    
    def destroy(self):
        self._stop_channel()
        self._layer_model = None

    def start(self):
        self._join_channel(self._channel_url)

    # This was added because the the ensure_future(join_stage_async(...)) wasn't ever executing
    async def start_async(self, channel_manager):
        LOGGER.info(f"Awaiting a join channel: {self._channel_url}")
        self._channel = await channel_manager.join_channel_async(self._channel_url, False)        
        self._channel_subscriber = self._channel.add_subscriber(self._on_channel_message)

    def stop(self):
        self._stop_channel()
    
    async def broadcast_merge_started_message_async(self):
        message = {MESSAGE_GROUP_KEY: {MESSAGE_KEY: MESSAGE_MERGE_STARTED}}
        await self._channel.send_message_async(message)

    async def broadcast_merge_done_message_async(self):
        message = {MESSAGE_GROUP_KEY: {MESSAGE_KEY: MESSAGE_MERGE_FINISHED}}
        await self._channel.send_message_async(message)

    async def broadcast_get_users_message_async(self):
        await self._channel.send_get_users_message_async()

    def register_join_callback(self, callback):
        self._join_callback = callback

    def register_hello_callback(self, callback):
        self._hello_callback = callback

    def register_left_callback(self, callback):
        self._left_callback = callback

    def register_merge_start_callback(self, callback):
        self._merge_start_callback = callback

    def register_merge_finished_callback(self, callback):
        self._merge_finished_callback = callback

    def get_users(self) -> cm.PeerUser:
        return self._peer_users

    def _join_channel(self, url):
        async def join_stage_async(url):
            LOGGER.info(f"Awaiting a join channel: {url}")
            self._channel = await cm.join_channel_async(url)
            if not self._channel:
                return

            self._channel_subscriber = self._channel.add_subscriber(self._on_channel_message)
        
        LOGGER.info(f"Joining channel: {url}")
        self._join_channel_future = asyncio.ensure_future(join_stage_async(url))
    
    def _on_channel_message(self, message: cm.Message):
        if message.message_type == cm.MessageType.JOIN:
            str = f"User {message.from_user.user_name} joined."
            #nm.post_notification(str)
            LOGGER.info(str)
            self._peer_users.add(message.from_user)
            if self._join_callback:
                self._join_callback(message.from_user.user_name, message.from_user.from_app)
        elif message.message_type == cm.MessageType.LEFT:
            str = f"User {message.from_user.user_name} left."
            #nm.post_notification(str)
            LOGGER.info(str)
            self._peer_users.remove(message.from_user)
            if self._left_callback:
                self._left_callback(message.from_user.user_name, message.from_user.from_app)
        elif message.message_type == cm.MessageType.HELLO:
            str = f"User {message.from_user.user_name} joined."
            #nm.post_notification(str)
            LOGGER.info(str)
            self._peer_users.add(message.from_user)
            if self._hello_callback:
                self._hello_callback(message.from_user.user_name, message.from_user.from_app)
        elif message.message_type == cm.MessageType.MESSAGE:
            content = message.content.get(MESSAGE_GROUP_KEY, None)
            if not content or not isinstance(content, dict):
                return

            message_type = content.get(MESSAGE_KEY, None)
            if not message_type:
                return
            
            if message_type == MESSAGE_MERGE_STARTED:
                LOGGER.info(f"User {message.from_user.user_name} starts to merge live layers.")
                if self._merge_start_callback:
                    self._merge_start_callback(message.from_user.user_name, message.from_user.from_app)
                #nm.post_notification(
                #    f"Stage owner `{self._layer_model.session_owner}' is merging live changes into base layers."
                #    " Please make sure no edits util merge is done, or you can quit this live session.",
                #)
            elif message_type == MESSAGE_MERGE_FINISHED:
                LOGGER.info(f"User {message.from_user.user_name} finished to merge live layers.")
                if self._merge_finished_callback:
                    self._merge_finished_callback(message.from_user.user_name, message.from_user.from_app)

                def reload_and_quit():
                    pass
                    #self._layer_model.reload_all_outdated_layers()
                    #self._layer_model.stop_live_session()

                #PromptManager.post_simple_prompt(
                #    "Live Session End",
                #    f"Stage owner `{self._layer_model.session_owner}' finished to merge live layers and stopped the session."
                #    " Do you want to reload the stage to get latest changes or simply quit this live session?",
                #    PromptButtonInfo("Quit and Reload", reload_and_quit),
                #    PromptButtonInfo("QUIT", lambda: self._layer_model.stop_live_session()),
                #    shortcut_keys=False
                #)
            else:
                return
    
    def _stop_channel(self):
        if self._channel_subscriber:
            self._channel_subscriber.unsubscribe()
            self._channel_subscriber = None
        if self._channel:
            self._channel.stop()
        self._channel = None
        try:
            if self._join_channel_future and not self._join_channel_future.done():
                self._join_channel_future.cancel()
        except Exception:
            pass
