from channels.generic.websocket import AsyncWebsocketConsumer
from redis.asyncio import Redis
from rt_geo.models import VehicleLocation
import json

VEHICLE_CONSUMER_GROUP = "vehicles_rt"


class VehicleConsumer(AsyncWebsocketConsumer):
    rt_db = Redis()  # remember to add host=redis when running in container

    async def connect(self):
        self.vehicle_id = self.scope["url_route"]["kwargs"]["vehicle_id"]
        self.vehicle_group_name = f"vehicle_{self.vehicle_id}"

        await self.channel_layer.group_add(VEHICLE_CONSUMER_GROUP, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code: int):
        await self.channel_layer.group_discard(
            VEHICLE_CONSUMER_GROUP, self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        vehicle_location = VehicleLocation(**text_data_json)

        await self.rt_db.geoadd(
            "vehicles",
            values=[
                vehicle_location.location.longitude,
                vehicle_location.location.latitude,
                vehicle_location.vehicle_id,
            ],
        )
