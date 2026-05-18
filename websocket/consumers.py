import json

from channels.generic.websocket import AsyncWebsocketConsumer


class PrintConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        sale = text_data_json['sale']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'sale': sale
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        sale = event['sale']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'sale': sale
        }))


class RealtimeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        self.table = self.scope["url_route"]["kwargs"]["table"]
        self.group_name = f"realtime_{self.table}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        self.table = self.scope["url_route"]["kwargs"]["table"]

        self.group_name = f"realtime_{self.table}"
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def db_event(self, event):
        payload = event["payload"]

        await self.send(text_data=json.dumps({
            "eventType": payload["action"],
            "pk": (payload.get("old_record", {}) or payload.get("record", {})).get("id", None),
            "new_record": payload["record"],
        }))
