
import json, pdb, asyncio

from . import constants
from .thread_pool import ThreadPool
from .game import Game, PaddleController, BallController
from .game import MatchManager, Match
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer

# Game sockets (with threads)

class GameConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.ball_controller = BallController()
        self.thread = None

        super().__init__(*args, **kwargs)

    def connect(self):
        # self.game = self.scope["url_route"]["kwargs"]["room_name"]
        self.game = self.scope["url_route"]["kwargs"]["room_name"]

        if self.game not in ThreadPool.threads:
            ThreadPool.add_game(self.game, self)
        self.thread = ThreadPool.threads[self.game]

        async_to_sync(self.channel_layer.group_add)(self.game, self.channel_name)
        if not self.thread["player_one"]:
            self.paddle_controller = PaddleController("player_one")
            self.thread["player_one"] = True

        elif not self.thread["player_two"]:
            self.paddle_controller = PaddleController("player_two")
            self.thread["player_two"] = True

        if self.thread["player_one"] and self.thread["player_two"]:
            self.thread["active"] = True

        (self.accept())

    def disconnect(self, close_code):
        self.thread[str(self.paddle_controller)] = False
        self.thread["active"] = False

        async_to_sync(self.channel_layer.group_discard)(self.game, self.channel_name)

    def receive(self, text_data):
        direction = json.loads(text_data).get("direction")
        self.paddle_controller.move(direction)
        # Deserialize the received message
        # game_data = json.loads(text_data)    
        # response_data = json.dumps(game_data)
        # await self.send(text_data=response_data)

    async def propagate_state(self):
        while True:
            if self.thread:
                if self.thread["active"]:
                    self.ball_controller.move()
                    async_to_sync(self.channel_layer.group_send)(
                        self.game,
                        {"type": "stream_state", "state": Game.state,},
                    )

    def stream_state(self, event):
        state = event["state"]

        self.send(text_data=json.dumps(state))

import uuid

match_manager = MatchManager()

class AsyncGameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']
        self.username = 'Anonymous'
        self.update_lock = asyncio.Lock()
        self.match = None

        if self.user is not None and self.user.is_authenticated:
            self.username = self.user.username

        # Game logic

        self.player_id = str(uuid.uuid4())

        async with self.update_lock:
            if not self.room_name in match_manager.get_matches():
                match_manager.get_matches()[self.room_name] = Match(self.room_name)
            self.match = match_manager.get_matches()[self.room_name]
            if not self.match.get_full():
                self.match.add_player(self.player_id)
            
        # Django channels logic

        await self.channel_layer.group_add(
            self.room_name, self.channel_name
        )

        await self.accept()

        async with self.update_lock:
            if self.match.get_full():
                await self.channel_layer.group_send(
                    self.room_name, {"type" : "game_start", "message": ""}
                )
                self.match.task = asyncio.create_task(self.game_loop())

    async def disconnect(self, close_code):

        # Game logic

        async with self.update_lock:
            if not self.match.task is None:
                self.match.task.cancel()
                self.match.task = None

        # Django channels logic

        await self.channel_layer.group_send(
            self.room_name, {"type": "game_end"}
        )

        await self.channel_layer.group_discard(
            self.room_name, self.channel_name
        )

        print(asyncio.all_tasks())

    async def receive(self, text_data):
        print(self.player_id)
        print(text_data)

        direction = json.loads(text_data).get("direction")
        async with self.update_lock:
            self.match.move(self.player_id, direction)

    async def game_loop(self):
        while True:
            
            # Logica gioco
            ...

            await self.channel_layer.group_send(
                self.room_name, {"type": "game.message", "message": self.match.get_state()}
            )
            await asyncio.sleep(constants.REFRESH_RATE)

    async def prova_message(self, event):
        #JSON.stringify({ 'direction': 'down' }
        print(event)

    async def game_start(self, event):

        await self.send(text_data=json.dumps({"type": "game_start"}))

    async def game_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({"type": "game_message", "message": message}))

    async def game_end(self, event):
        
        await self.send(text_data=json.dumps({"type": "game_end"}))

# Chat sockets

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user = self.scope["user"]
        username = "Anonymous"
        if user.is_authenticated:
            username = user.username
        message = username + ": " + text_data_json["message"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))