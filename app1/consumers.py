import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.vehicle_id = self.scope['url_route']['kwargs']['vehicle_id']
        self.group_name = f'vehicle_{self.vehicle_id}'

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from driver
    async def receive(self, text_data):
        data = json.loads(text_data)
        lat = data['latitude']
        lon = data['longitude']

        # Send to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_location',
                'latitude': lat,
                'longitude': lon
            }
        )

    # Send location to all in group (parents)
    async def send_location(self, event):
        await self.send(text_data=json.dumps({
            'latitude': event['latitude'],
            'longitude': event['longitude']
        }))
